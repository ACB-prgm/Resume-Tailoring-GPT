"""
Explicit GitHub sync adapter for local-first career corpus storage.

Writes use Git Data UTF-8 flow:
blob -> tree -> commit -> ref update
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set

try:
    from career_corpus_store_core import CareerCorpusStore
except ImportError:
    from knowledge_files.career_corpus_store_core import CareerCorpusStore  # type: ignore

try:
    from memory_validation_core import (
        assert_notes_content_only,
        assert_persist_claim_allowed,
        assert_sections_explicitly_approved,
        assert_validation_claim_allowed,
        canonical_json_sha256,
        canonical_json_text,
        diagnose_payload_integrity,
    )
except ImportError:
    from knowledge_files.memory_validation_core import (  # type: ignore
        assert_notes_content_only,
        assert_persist_claim_allowed,
        assert_sections_explicitly_approved,
        assert_validation_claim_allowed,
        canonical_json_sha256,
        canonical_json_text,
        diagnose_payload_integrity,
    )


GetMemoryRepoFn = Callable[[], Dict[str, Any]]
GetBranchRefFn = Callable[[str], Dict[str, Any]]
GetGitCommitFn = Callable[[str], Dict[str, Any]]
GetGitTreeFn = Callable[[str, bool], Dict[str, Any]]
GetGitBlobFn = Callable[[str], Dict[str, Any]]
CreateGitBlobFn = Callable[[Dict[str, Any]], Dict[str, Any]]
CreateGitTreeFn = Callable[[Dict[str, Any]], Dict[str, Any]]
CreateGitCommitFn = Callable[[Dict[str, Any]], Dict[str, Any]]
UpdateBranchRefFn = Callable[[str, Dict[str, Any]], Dict[str, Any]]
CreateMemoryRepoFn = Callable[[Dict[str, Any]], Dict[str, Any]]


def gpt_core(obj: Any) -> Any:
    obj.__gpt_layer__ = "core"
    obj.__gpt_core__ = True
    return obj


@dataclass
class PushAttemptResult:
    ok: bool
    error_code: Optional[str] = None
    reason: Optional[str] = None
    retryable: bool = False
    remote_blob_shas: Optional[Dict[str, str]] = None
    remote_commit_sha: Optional[str] = None
    remote_branch: Optional[str] = None
    new_tree_sha: Optional[str] = None


@gpt_core
class CareerCorpusSync:
    """Sync local corpus state with GitHub via injected tool-call adapters."""

    METHOD = "git_blob_utf8_split"
    REQUIRED_ONBOARDING_SECTIONS = {
        "profile",
        "experience",
        "projects",
        "skills",
        "certifications",
        "education",
        "metadata",
    }

    def __init__(
        self,
        store: CareerCorpusStore,
        get_memory_repo: Optional[GetMemoryRepoFn] = None,
        get_branch_ref: Optional[GetBranchRefFn] = None,
        get_git_commit: Optional[GetGitCommitFn] = None,
        get_git_tree: Optional[GetGitTreeFn] = None,
        get_git_blob: Optional[GetGitBlobFn] = None,
        create_git_blob: Optional[CreateGitBlobFn] = None,
        create_git_tree: Optional[CreateGitTreeFn] = None,
        create_git_commit: Optional[CreateGitCommitFn] = None,
        update_branch_ref: Optional[UpdateBranchRefFn] = None,
        max_retries: int = 1,
    ) -> None:
        self.store = store
        self._get_memory_repo = get_memory_repo
        self._get_branch_ref = get_branch_ref
        self._get_git_commit = get_git_commit
        self._get_git_tree = get_git_tree
        self._get_git_blob = get_git_blob
        self._create_git_blob = create_git_blob
        self._create_git_tree = create_git_tree
        self._create_git_commit = create_git_commit
        self._update_branch_ref = update_branch_ref
        self._max_retries = max_retries

    def pull(self, force: bool = False) -> Dict[str, Any]:
        missing = self._missing_pull_adapters()
        if missing:
            return {
                "ok": False,
                "changed": False,
                "reason": f"missing_pull_adapters:{','.join(missing)}",
                "error_code": "api_unknown",
            }
        return self._pull_split(force=force)

    def pull_if_stale_before_write(self, force: bool = False) -> Dict[str, Any]:
        """
        Skip pre-write pull when local cache is already hydrated and tracked.

        This avoids redundant blob reads immediately before push in the common
        section-update flow.
        """
        if force:
            return self.pull(force=True)
        status = self.store.status()
        if self.store.is_loaded and status.get("remote_file_sha"):
            return {"ok": True, "changed": False, "reason": "skipped_prewrite_pull_local_fresh"}
        return self.pull(force=False)

    def persist_memory_changes(self, message: str = "Update career corpus memory") -> Dict[str, Any]:
        return self.push(message=message)

    @staticmethod
    def bootstrap_memory_repo(
        get_memory_repo: GetMemoryRepoFn,
        create_memory_repo: CreateMemoryRepoFn,
        turn_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Deterministic repo bootstrap: get -> (optional create) -> confirm get.

        Enforces max one create attempt per turn via `turn_state`.
        """
        first = get_memory_repo()
        first_status = CareerCorpusSync._status_code(first)
        if first_status != 404:
            return {
                "ok": True,
                "repo_exists": True,
                "created": False,
                "sequence": ["get"],
                "repo_create_attempted_this_turn": bool(
                    turn_state and turn_state.get("repo_create_attempted_this_turn")
                ),
            }

        if turn_state is not None and turn_state.get("repo_create_attempted_this_turn"):
            raise RuntimeError("createMemoryRepo already attempted this turn.")
        if turn_state is not None:
            turn_state["repo_create_attempted_this_turn"] = True

        create_payload = {
            "name": "career-corpus-memory",
            "private": True,
            "auto_init": True,
        }
        create_response = create_memory_repo(create_payload)
        create_status = CareerCorpusSync._status_code(create_response)
        if create_status and create_status >= 400:
            return {
                "ok": False,
                "repo_exists": False,
                "created": False,
                "sequence": ["get", "create"],
                "error_code": f"api_{create_status}",
                "reason": "create_failed",
                "repo_create_attempted_this_turn": True,
            }

        confirmed = get_memory_repo()
        confirmed_status = CareerCorpusSync._status_code(confirmed)
        repo_exists = confirmed_status != 404
        return {
            "ok": repo_exists,
            "repo_exists": repo_exists,
            "created": True,
            "sequence": ["get", "create", "get_confirm"],
            "error_code": None if repo_exists else "api_404",
            "reason": "confirmed" if repo_exists else "confirm_failed",
            "repo_create_attempted_this_turn": True,
        }

    def push(
        self,
        message: str = "Update career corpus memory",
        target_sections: Optional[List[str]] = None,
        approved_sections: Optional[Dict[str, Any]] = None,
        user_git_fluency: str = "non_technical",
        technical_details_requested: bool = False,
    ) -> Dict[str, Any]:
        result = self._base_result()
        before_snapshot = self._status_snapshot(self.store.status())
        if not self.store.is_loaded:
            self.store.load()

        if target_sections:
            try:
                assert_sections_explicitly_approved(approved_sections or {}, target_sections)
            except Exception as exc:
                result.update(
                    {
                        "ok": False,
                        "reason": str(exc),
                        "error_code": "approval_missing",
                    }
                )
                return self._finalize_push_result(
                    result, before_snapshot, user_git_fluency, technical_details_requested
                )

        if not self.store.dirty:
            result.update(
                {
                    "ok": True,
                    "pushed": False,
                    "persisted": True,
                    "reason": "not_dirty",
                }
            )
            result["verify_ok"] = True
            return self._finalize_push_result(
                result, before_snapshot, user_git_fluency, technical_details_requested
            )

        missing = self._missing_push_adapters()
        if missing:
            result.update(
                {
                    "ok": False,
                    "reason": f"missing_adapters:{','.join(missing)}",
                    "error_code": "api_unknown",
                }
            )
            return self._finalize_push_result(
                result, before_snapshot, user_git_fluency, technical_details_requested
            )

        try:
            self.store.validate()
            assert_notes_content_only(self.store.snapshot())
            result["validated"] = True
            result["validation_ran"] = True
            assert_validation_claim_allowed(validated_ran=True, validation_ok=True)
        except RuntimeError as exc:
            result.update(
                {
                    "ok": False,
                    "reason": str(exc),
                    "error_code": "notes_policy_violation",
                }
            )
            result["validation_ran"] = True
            return self._finalize_push_result(
                result, before_snapshot, user_git_fluency, technical_details_requested
            )
        except Exception as exc:
            result.update(
                {
                    "ok": False,
                    "reason": str(exc),
                    "error_code": "validation_failed",
                }
            )
            result["validation_ran"] = True
            return self._finalize_push_result(
                result, before_snapshot, user_git_fluency, technical_details_requested
            )

        # Local-first invariant.
        self.store.save()
        result["local_saved"] = True

        docs = self.store.build_split_documents()
        docs_text = {path: canonical_json_text(doc) for path, doc in docs.items()}
        local_hashes = {path: canonical_json_sha256(doc) for path, doc in docs.items()}
        result["payload_integrity"] = {
            path: diagnose_payload_integrity(text)
            for path, text in docs_text.items()
            if path in (CareerCorpusStore.INDEX_FILE,)
        }

        status = self.store.status()
        previous_hashes = status.get("remote_file_hashes") or {}
        changed_paths = sorted(
            [path for path, file_hash in local_hashes.items() if previous_hashes.get(path) != file_hash]
        )
        deleted_paths = sorted(
            [path for path in previous_hashes.keys() if path not in local_hashes]
        )

        if not changed_paths and not deleted_paths:
            result.update(
                {
                    "ok": True,
                    "pushed": False,
                    "persisted": True,
                    "reason": "hashes_unchanged",
                }
            )
            result["verify_ok"] = True
            return self._finalize_push_result(
                result, before_snapshot, user_git_fluency, technical_details_requested
            )

        if target_sections:
            disallowed = self._disallowed_changed_paths(changed_paths, deleted_paths, set(target_sections))
            if disallowed:
                result.update(
                    {
                        "ok": False,
                        "pushed": False,
                        "persisted": False,
                        "reason": f"disallowed_changed_paths:{','.join(sorted(disallowed))}",
                        "error_code": "unapproved_section_changes",
                    }
                )
                return self._finalize_push_result(
                    result, before_snapshot, user_git_fluency, technical_details_requested
                )

        attempt = 0
        attempt_result: Optional[PushAttemptResult] = None
        while attempt <= self._max_retries:
            attempt_result = self._attempt_git_push(
                message=message,
                docs_text=docs_text,
                changed_paths=changed_paths,
                deleted_paths=deleted_paths,
            )
            result["retry_count"] = attempt
            if attempt_result.ok:
                break
            if not attempt_result.retryable:
                break
            attempt += 1

        if attempt_result is None or not attempt_result.ok:
            result.update(
                {
                    "ok": False,
                    "pushed": False,
                    "persisted": False,
                    "reason": attempt_result.reason if attempt_result else "push_attempt_missing",
                    "error_code": attempt_result.error_code if attempt_result else "api_unknown",
                }
            )
            return self._finalize_push_result(
                result, before_snapshot, user_git_fluency, technical_details_requested
            )

        result["remote_written"] = True
        result["remote_blob_sha"] = attempt_result.remote_blob_shas.get(CareerCorpusStore.INDEX_FILE)
        result["remote_commit_sha"] = attempt_result.remote_commit_sha
        result["remote_branch"] = attempt_result.remote_branch

        verification = self._verify_push_result(
            commit_sha=attempt_result.remote_commit_sha,
            expected_blob_shas=attempt_result.remote_blob_shas or {},
            changed_paths=changed_paths,
            deleted_paths=deleted_paths,
        )
        result["verification"] = verification
        result["verify_ok"] = bool(verification.get("ok"))
        if not verification["ok"]:
            result.update(
                {
                    "ok": False,
                    "pushed": True,
                    "persisted": False,
                    "reason": verification["error"],
                    "error_code": "transport_corruption",
                }
            )
            return self._finalize_push_result(
                result, before_snapshot, user_git_fluency, technical_details_requested
            )

        try:
            assert_persist_claim_allowed(push_ok=True, verify_ok=True)
        except Exception as exc:
            result.update(
                {
                    "ok": False,
                    "pushed": True,
                    "persisted": False,
                    "reason": str(exc),
                    "error_code": "persist_claim_invalid",
                }
            )
            return self._finalize_push_result(
                result, before_snapshot, user_git_fluency, technical_details_requested
            )

        self.store.mark_push_success(
            remote_file_sha=verification.get("remote_index_sha"),
            remote_blob_sha=attempt_result.remote_blob_shas.get(CareerCorpusStore.INDEX_FILE),
            remote_commit_sha=attempt_result.remote_commit_sha,
            remote_branch=attempt_result.remote_branch,
            remote_file_hashes=local_hashes,
            method=self.METHOD,
            verified=True,
        )
        result.update(
            {
                "ok": True,
                "pushed": True,
                "persisted": True,
                "reason": "push_verified",
                "error_code": None,
            }
        )
        return self._finalize_push_result(
            result, before_snapshot, user_git_fluency, technical_details_requested
        )

    def _pull_split(self, force: bool = False) -> Dict[str, Any]:
        repo_response = self._get_memory_repo()
        if self._status_code(repo_response) == 404:
            return {"ok": False, "changed": False, "reason": "memory_repo_not_found", "error_code": "api_404"}
        branch = repo_response.get("default_branch")
        if not isinstance(branch, str) or not branch:
            return {"ok": False, "changed": False, "reason": "default_branch_missing", "error_code": "api_unknown"}

        ref_response = self._get_branch_ref(branch)
        if self._status_code(ref_response) == 404:
            return {"ok": False, "changed": False, "reason": "branch_ref_not_found", "error_code": "api_404"}
        commit_sha = self._extract_nested(ref_response, ("object", "sha"))
        if not commit_sha:
            return {"ok": False, "changed": False, "reason": "parent_commit_sha_missing", "error_code": "api_unknown"}

        commit_response = self._get_git_commit(commit_sha)
        if self._status_code(commit_response) == 404:
            return {"ok": False, "changed": False, "reason": "parent_commit_not_found", "error_code": "api_404"}
        tree_sha = self._extract_nested(commit_response, ("tree", "sha"))
        if not tree_sha:
            return {"ok": False, "changed": False, "reason": "base_tree_sha_missing", "error_code": "api_unknown"}

        tree_response = self._get_git_tree(tree_sha, True)
        path_to_blob = self._tree_path_to_blob_sha(tree_response)
        index_sha = path_to_blob.get(CareerCorpusStore.INDEX_FILE)
        if not index_sha:
            return {"ok": True, "changed": False, "reason": "remote_missing", "error_code": "api_404"}

        status = self.store.status()
        if not force and status.get("remote_file_sha") == index_sha:
            return {"ok": True, "changed": False, "reason": "sha_unchanged", "remote_file_sha": index_sha}

        index_doc = self._read_blob_json(index_sha)
        referenced_paths = CareerCorpusStore.index_referenced_paths(index_doc)
        split_docs: Dict[str, Dict[str, Any]] = {}
        for path in referenced_paths:
            blob_sha = path_to_blob.get(path)
            if not blob_sha:
                return {
                    "ok": False,
                    "changed": False,
                    "reason": f"split_file_missing:{path}",
                    "error_code": "transport_corruption",
                }
            split_docs[path] = self._read_blob_json(blob_sha)

        corpus = CareerCorpusStore.assemble_from_split_documents(index_doc, split_docs)
        file_hashes = index_doc.get("file_hashes")
        remote_hashes = file_hashes if isinstance(file_hashes, dict) else {}
        self.store.replace_corpus(
            corpus,
            remote_file_sha=index_sha,
            remote_branch=branch,
            remote_file_hashes=remote_hashes,
            validate=False,
        )
        return {
            "ok": True,
            "changed": True,
            "reason": "pulled",
            "remote_file_sha": index_sha,
            "dirty": self.store.status()["dirty"],
        }

    def _attempt_git_push(
        self,
        message: str,
        docs_text: Dict[str, str],
        changed_paths: List[str],
        deleted_paths: List[str],
    ) -> PushAttemptResult:
        repo_response = self._get_memory_repo()
        if self._status_code(repo_response) == 404:
            return PushAttemptResult(ok=False, error_code="api_404", reason="memory_repo_not_found")
        branch = repo_response.get("default_branch")
        if not isinstance(branch, str) or not branch:
            return PushAttemptResult(ok=False, error_code="api_unknown", reason="default_branch_missing")

        ref_response = self._get_branch_ref(branch)
        status = self._status_code(ref_response)
        if status == 409:
            return PushAttemptResult(ok=False, error_code="ref_conflict", reason="branch_ref_conflict", retryable=True)
        if status == 404:
            return PushAttemptResult(ok=False, error_code="api_404", reason="branch_ref_not_found")
        parent_commit_sha = self._extract_nested(ref_response, ("object", "sha"))
        if not parent_commit_sha:
            return PushAttemptResult(ok=False, error_code="api_unknown", reason="parent_commit_sha_missing")

        commit_response = self._get_git_commit(parent_commit_sha)
        if self._status_code(commit_response) == 404:
            return PushAttemptResult(ok=False, error_code="api_404", reason="parent_commit_not_found")
        base_tree_sha = self._extract_nested(commit_response, ("tree", "sha"))
        if not base_tree_sha:
            return PushAttemptResult(ok=False, error_code="api_unknown", reason="base_tree_sha_missing")

        blob_shas: Dict[str, str] = {}
        for path in changed_paths:
            blob_response = self._create_git_blob({"content": docs_text[path], "encoding": "utf-8"})
            status = self._status_code(blob_response)
            if status == 422:
                return PushAttemptResult(ok=False, error_code="api_422", reason=f"blob_rejected:{path}", retryable=True)
            blob_sha = blob_response.get("sha")
            if not isinstance(blob_sha, str) or not blob_sha:
                return PushAttemptResult(ok=False, error_code="api_unknown", reason=f"blob_sha_missing:{path}")
            blob_shas[path] = blob_sha

        tree_entries: List[Dict[str, Any]] = []
        for path in changed_paths:
            tree_entries.append(
                {
                    "path": path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_shas[path],
                }
            )
        for path in deleted_paths:
            tree_entries.append(
                {
                    "path": path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": None,
                }
            )

        tree_response = self._create_git_tree({"base_tree": base_tree_sha, "tree": tree_entries})
        status = self._status_code(tree_response)
        if status == 422:
            return PushAttemptResult(ok=False, error_code="api_422", reason="tree_rejected", retryable=True)
        new_tree_sha = tree_response.get("sha")
        if not isinstance(new_tree_sha, str) or not new_tree_sha:
            return PushAttemptResult(ok=False, error_code="api_unknown", reason="new_tree_sha_missing")

        commit_create_response = self._create_git_commit(
            {
                "message": message,
                "tree": new_tree_sha,
                "parents": [parent_commit_sha],
            }
        )
        status = self._status_code(commit_create_response)
        if status == 422:
            return PushAttemptResult(ok=False, error_code="api_422", reason="commit_rejected", retryable=True)
        new_commit_sha = commit_create_response.get("sha")
        if not isinstance(new_commit_sha, str) or not new_commit_sha:
            return PushAttemptResult(ok=False, error_code="api_unknown", reason="new_commit_sha_missing")

        ref_update_response = self._update_branch_ref(branch, {"sha": new_commit_sha, "force": False})
        status = self._status_code(ref_update_response)
        if status == 409:
            return PushAttemptResult(ok=False, error_code="ref_conflict", reason="ref_update_conflict", retryable=True)
        if status == 422:
            return PushAttemptResult(ok=False, error_code="api_422", reason="ref_update_rejected", retryable=True)
        if status == 404:
            return PushAttemptResult(ok=False, error_code="api_404", reason="ref_update_not_found")

        return PushAttemptResult(
            ok=True,
            remote_blob_shas=blob_shas,
            remote_commit_sha=new_commit_sha,
            remote_branch=branch,
            new_tree_sha=new_tree_sha,
        )

    def _verify_push_result(
        self,
        commit_sha: str,
        expected_blob_shas: Dict[str, str],
        changed_paths: List[str],
        deleted_paths: List[str],
    ) -> Dict[str, Any]:
        commit_response = self._get_git_commit(commit_sha)
        tree_sha = self._extract_nested(commit_response, ("tree", "sha"))
        if not tree_sha:
            return {"ok": False, "error": "verification_tree_missing", "remote_index_sha": None}
        tree_response = self._get_git_tree(tree_sha, True)
        path_to_blob = self._tree_path_to_blob_sha(tree_response)

        for path in deleted_paths:
            if path in path_to_blob:
                return {"ok": False, "error": f"deleted_path_still_present:{path}", "remote_index_sha": None}

        for path in changed_paths:
            blob_sha = path_to_blob.get(path)
            if not blob_sha:
                return {"ok": False, "error": f"changed_path_missing:{path}", "remote_index_sha": None}
            expected = expected_blob_shas.get(path)
            if not expected:
                return {"ok": False, "error": f"expected_blob_sha_missing:{path}", "remote_index_sha": None}
            if blob_sha != expected:
                return {
                    "ok": False,
                    "error": f"blob_sha_mismatch:{path}:expected={expected}:actual={blob_sha}",
                    "remote_index_sha": None,
                }

        return {
            "ok": True,
            "error": None,
            "remote_index_sha": path_to_blob.get(CareerCorpusStore.INDEX_FILE),
        }

    def _read_blob_json(self, blob_sha: str) -> Dict[str, Any]:
        blob_response = self._get_git_blob(blob_sha)
        status = self._status_code(blob_response)
        if status == 404:
            raise ValueError(f"Blob not found: {blob_sha}")

        # Raw media type for JSON files may already be parsed to an object by tool wrappers.
        if isinstance(blob_response, dict):
            has_blob_wrapper = "content" in blob_response or "encoding" in blob_response
            if not has_blob_wrapper and "status_code" not in blob_response:
                return blob_response

        text = self._blob_response_to_text(blob_response)
        obj = json.loads(text)
        if not isinstance(obj, dict):
            raise ValueError("Expected blob JSON object.")
        return obj

    def _read_blob_text(self, blob_sha: str) -> str:
        blob_response = self._get_git_blob(blob_sha)
        status = self._status_code(blob_response)
        if status == 404:
            raise ValueError(f"Blob not found: {blob_sha}")
        return self._blob_response_to_text(blob_response)

    @staticmethod
    def _blob_response_to_text(blob_response: Any) -> str:
        if isinstance(blob_response, str):
            return blob_response
        if isinstance(blob_response, (bytes, bytearray)):
            return bytes(blob_response).decode("utf-8")
        if not isinstance(blob_response, dict):
            raise ValueError(f"Unsupported blob response type: {type(blob_response).__name__}")

        content = blob_response.get("content")
        encoding = blob_response.get("encoding")
        if isinstance(content, str):
            if encoding == "utf-8":
                return content
            if encoding == "base64" or not encoding:
                # GitHub blob content may include line breaks.
                compact = "".join(content.split())
                raw = base64.b64decode(compact.encode("ascii"))
                return raw.decode("utf-8")

        # Raw JSON blob parsed as object by wrapper.
        if "status_code" not in blob_response:
            return json.dumps(blob_response, ensure_ascii=False)

        raise ValueError("Blob response missing content.")

    @staticmethod
    def _tree_path_to_blob_sha(tree_response: Dict[str, Any]) -> Dict[str, str]:
        entries = tree_response.get("tree")
        if not isinstance(entries, list):
            raise ValueError("Tree response missing 'tree' list.")
        mapping: Dict[str, str] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "blob":
                continue
            path = entry.get("path")
            sha = entry.get("sha")
            if isinstance(path, str) and isinstance(sha, str):
                mapping[path] = sha
        return mapping

    def _missing_push_adapters(self) -> List[str]:
        missing = []
        if self._get_memory_repo is None:
            missing.append("get_memory_repo")
        if self._get_branch_ref is None:
            missing.append("get_branch_ref")
        if self._get_git_commit is None:
            missing.append("get_git_commit")
        if self._get_git_tree is None:
            missing.append("get_git_tree")
        if self._get_git_blob is None:
            missing.append("get_git_blob")
        if self._create_git_blob is None:
            missing.append("create_git_blob")
        if self._create_git_tree is None:
            missing.append("create_git_tree")
        if self._create_git_commit is None:
            missing.append("create_git_commit")
        if self._update_branch_ref is None:
            missing.append("update_branch_ref")
        return missing

    def _missing_pull_adapters(self) -> List[str]:
        missing = []
        if self._get_memory_repo is None:
            missing.append("get_memory_repo")
        if self._get_branch_ref is None:
            missing.append("get_branch_ref")
        if self._get_git_commit is None:
            missing.append("get_git_commit")
        if self._get_git_tree is None:
            missing.append("get_git_tree")
        if self._get_git_blob is None:
            missing.append("get_git_blob")
        return missing

    @staticmethod
    def _status_code(response: Any) -> Optional[int]:
        if not isinstance(response, dict):
            return None
        status = response.get("status_code")
        return status if isinstance(status, int) else None

    @staticmethod
    def _extract_nested(response: Dict[str, Any], path: tuple[str, ...]) -> Optional[str]:
        node: Any = response
        for key in path:
            if not isinstance(node, dict):
                return None
            node = node.get(key)
        return node if isinstance(node, str) and node else None

    def _base_result(self) -> Dict[str, Any]:
        return {
            "ok": False,
            "pushed": False,
            "persisted": False,
            "retry_count": 0,
            "method": self.METHOD,
            "remote_blob_sha": None,
            "remote_commit_sha": None,
            "remote_file_sha": None,
            "remote_branch": None,
            "verification": {"ok": False, "error": "not_run"},
            "reason": None,
            "error_code": None,
            "validated": False,
            "validation_ran": False,
            "local_saved": False,
            "remote_written": False,
            "verify_ok": False,
            "status_changed": False,
            "user_message": None,
        }

    @staticmethod
    def _status_snapshot(status: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "dirty": status.get("dirty"),
            "local_hash": status.get("local_hash"),
            "remote_file_sha": status.get("remote_file_sha"),
            "remote_blob_sha": status.get("remote_blob_sha"),
            "remote_commit_sha": status.get("remote_commit_sha"),
            "remote_branch": status.get("remote_branch"),
            "last_push_utc": status.get("last_push_utc"),
            "last_verified_utc": status.get("last_verified_utc"),
            "last_push_method": status.get("last_push_method"),
        }

    def _finalize_push_result(
        self,
        result: Dict[str, Any],
        before_snapshot: Dict[str, Any],
        user_git_fluency: str,
        technical_details_requested: bool,
    ) -> Dict[str, Any]:
        after_snapshot = self._status_snapshot(self.store.status())
        result["status_changed"] = before_snapshot != after_snapshot
        result["user_message"] = self._build_user_message(
            result,
            user_git_fluency=user_git_fluency,
            technical_details_requested=technical_details_requested,
        )
        return result

    @staticmethod
    def _build_user_message(
        result: Dict[str, Any],
        user_git_fluency: str = "non_technical",
        technical_details_requested: bool = False,
    ) -> str:
        persisted = bool(result.get("persisted"))
        reason = result.get("reason")
        error_code = result.get("error_code")
        technical = technical_details_requested or user_git_fluency == "technical"

        if persisted:
            if reason in {"not_dirty", "hashes_unchanged"}:
                message = "No memory changes to save."
            else:
                message = "Saved to memory/corpus."
        else:
            message = "Couldn't save to memory."

        if technical:
            details: List[str] = []
            if isinstance(reason, str) and reason:
                details.append(f"reason={reason}")
            if isinstance(error_code, str) and error_code:
                details.append(f"error_code={error_code}")
            branch = result.get("remote_branch")
            commit_sha = result.get("remote_commit_sha")
            if isinstance(branch, str) and branch:
                details.append(f"branch={branch}")
            if isinstance(commit_sha, str) and commit_sha:
                details.append(f"commit={commit_sha}")
            if details:
                message = f"{message} ({', '.join(details)})"
        return message

    @classmethod
    def _disallowed_changed_paths(
        cls,
        changed_paths: List[str],
        deleted_paths: List[str],
        target_sections: Set[str],
    ) -> Set[str]:
        allowed = cls._allowed_paths_for_sections(target_sections)
        disallowed: Set[str] = set()
        for path in changed_paths + deleted_paths:
            if path not in allowed and not cls._path_prefix_allowed(path, target_sections):
                disallowed.add(path)
        return disallowed

    @classmethod
    def _allowed_paths_for_sections(cls, target_sections: Set[str]) -> Set[str]:
        mapping = {
            "profile": "corpus_profile.json",
            "skills": "corpus_skills.json",
            "certifications": "corpus_certifications.json",
            "education": "corpus_education.json",
            "metadata": "corpus_metadata.json",
        }
        allowed = {CareerCorpusStore.INDEX_FILE}
        for section, path in mapping.items():
            if section in target_sections:
                allowed.add(path)
        return allowed

    @staticmethod
    def _path_prefix_allowed(path: str, target_sections: Set[str]) -> bool:
        if "experience" in target_sections and path.startswith("corpus_experience_"):
            return True
        if "projects" in target_sections and path.startswith("corpus_project_"):
            return True
        return False
