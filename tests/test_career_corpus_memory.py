from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

from knowledge_files.career_corpus_store import CareerCorpusStore
from knowledge_files.career_corpus_sync import CareerCorpusSync

try:
    from memory_validation import canonical_json_text, encode_base64_utf8
except ImportError:
    from knowledge_files.memory_validation import canonical_json_text, encode_base64_utf8  # type: ignore


def make_corpus(with_ids: bool = True) -> Dict[str, Any]:
    exp = {
        "employer": "Acme Corp",
        "title": "Systems Analyst",
        "start_date": "2020-01",
        "end_date": None,
        "location": "Remote",
        "bullets": ["Built integrations."],
        "tools": ["Python"],
        "outcomes": ["Reduced cycle time."],
        "domain_tags": ["integration"],
    }
    proj = {
        "name": "ERP Rollout",
        "role": "Lead Analyst",
        "stack": ["SQL", "Power BI"],
        "outcomes": ["Improved reporting accuracy."],
    }
    cert = {
        "name": "Cert A",
        "issuer": "Issuer A",
        "status": "active",
    }
    edu = {
        "degree": "BS",
        "institution": "State U",
        "graduation_year": 2015,
    }
    if with_ids:
        exp["id"] = "exp_existing"
        proj["id"] = "proj_existing"
        cert["id"] = "cert_existing"
        edu["id"] = "edu_existing"

    return {
        "schema_version": "1.0.0",
        "profile": {"full_name": "Test User"},
        "summary_facts": ["Fact 1"],
        "experience": [exp],
        "projects": [proj],
        "skills": {
            "technical": ["Python"],
            "platforms": ["Azure"],
            "methods": ["Agile"],
            "domains": ["Enterprise IT"],
        },
        "certifications": [cert],
        "education": [edu],
        "metadata": {
            "last_updated_utc": "2026-01-01T00:00:00Z",
            "source": "manual_import",
        },
    }


class FakeGitRepo:
    def __init__(self, split_docs: Dict[str, Dict[str, Any]]) -> None:
        self.default_branch = "main"
        self.calls = {
            "get_memory_repo": 0,
            "get_branch_ref": 0,
            "get_git_commit": 0,
            "get_git_tree": 0,
            "get_git_blob": 0,
            "create_git_blob": 0,
            "create_git_tree": 0,
            "create_git_commit": 0,
            "update_branch_ref": 0,
        }
        self.ref_conflicts_remaining = 0
        self.corrupt_paths: set[str] = set()
        self.tamper_tree_paths: set[str] = set()
        self.raw_blob_mode: str = "base64"  # one of: base64, raw_text, raw_json_object

        self._blob_counter = 0
        self._tree_counter = 0
        self._commit_counter = 0
        self._blobs: Dict[str, str] = {}
        self._trees: Dict[str, Dict[str, str]] = {}
        self._commits: Dict[str, str] = {}
        self._head_commit: str = ""

        initial_path_map: Dict[str, str] = {}
        for path, doc in split_docs.items():
            sha = self._new_blob(canonical_json_text(doc))
            initial_path_map[path] = sha
        tree_sha = self._new_tree(initial_path_map)
        self._head_commit = self._new_commit(tree_sha)

    def head_path_map(self) -> Dict[str, str]:
        tree_sha = self._commits[self._head_commit]
        return deepcopy(self._trees[tree_sha])

    def get_memory_repo(self) -> Dict[str, Any]:
        self.calls["get_memory_repo"] += 1
        return {"default_branch": self.default_branch}

    def get_branch_ref(self, branch: str) -> Dict[str, Any]:
        self.calls["get_branch_ref"] += 1
        if branch != self.default_branch:
            return {"status_code": 404}
        return {"object": {"sha": self._head_commit}}

    def get_git_commit(self, commit_sha: str) -> Dict[str, Any]:
        self.calls["get_git_commit"] += 1
        tree_sha = self._commits.get(commit_sha)
        if not tree_sha:
            return {"status_code": 404}
        return {"tree": {"sha": tree_sha}}

    def get_git_tree(self, tree_sha: str, recursive: bool) -> Dict[str, Any]:
        self.calls["get_git_tree"] += 1
        path_map = self._trees.get(tree_sha)
        if path_map is None:
            return {"status_code": 404}
        entries = [{"path": p, "type": "blob", "sha": s} for p, s in sorted(path_map.items())]
        return {"sha": tree_sha, "tree": entries, "truncated": False, "recursive": recursive}

    def get_git_blob(self, blob_sha: str) -> Dict[str, Any]:
        self.calls["get_git_blob"] += 1
        text = self._blobs.get(blob_sha)
        if text is None:
            return {"status_code": 404}

        path = None
        for p, s in self.head_path_map().items():
            if s == blob_sha:
                path = p
                break

        if path in self.corrupt_paths:
            obj = json.loads(text)
            obj["_corrupt"] = True
            text = json.dumps(obj, ensure_ascii=False)

        if self.raw_blob_mode == "raw_text":
            return text  # type: ignore[return-value]
        if self.raw_blob_mode == "raw_json_object":
            return json.loads(text)  # type: ignore[return-value]

        return {
            "sha": blob_sha,
            "encoding": "base64",
            "content": encode_base64_utf8(text),
        }

    def create_git_blob(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls["create_git_blob"] += 1
        if payload.get("encoding") != "utf-8":
            return {"status_code": 422}
        content = payload.get("content")
        if not isinstance(content, str):
            return {"status_code": 422}
        sha = self._new_blob(content)
        return {"sha": sha}

    def create_git_tree(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls["create_git_tree"] += 1
        base_tree = payload.get("base_tree")
        tree_entries = payload.get("tree")
        if not isinstance(base_tree, str) or not isinstance(tree_entries, list):
            return {"status_code": 422}
        base_map = deepcopy(self._trees.get(base_tree, {}))
        for entry in tree_entries:
            path = entry.get("path")
            sha = entry.get("sha")
            if not isinstance(path, str):
                continue
            if sha is None:
                base_map.pop(path, None)
            elif isinstance(sha, str):
                if path in self.tamper_tree_paths:
                    # Simulate transport/tree corruption: tree references a different blob.
                    base_map[path] = self._new_blob('{"_tampered":true}')
                else:
                    base_map[path] = sha
            else:
                return {"status_code": 422}
        new_tree_sha = self._new_tree(base_map)
        return {"sha": new_tree_sha}

    def create_git_commit(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls["create_git_commit"] += 1
        tree_sha = payload.get("tree")
        if not isinstance(tree_sha, str) or tree_sha not in self._trees:
            return {"status_code": 422}
        new_commit_sha = self._new_commit(tree_sha)
        return {"sha": new_commit_sha}

    def update_branch_ref(self, branch: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls["update_branch_ref"] += 1
        if branch != self.default_branch:
            return {"status_code": 404}
        if self.ref_conflicts_remaining > 0:
            self.ref_conflicts_remaining -= 1
            return {"status_code": 409}
        commit_sha = payload.get("sha")
        if not isinstance(commit_sha, str) or commit_sha not in self._commits:
            return {"status_code": 422}
        self._head_commit = commit_sha
        return {"object": {"sha": commit_sha}}

    def _new_blob(self, content: str) -> str:
        self._blob_counter += 1
        sha = f"blob_{self._blob_counter}"
        self._blobs[sha] = content
        return sha

    def _new_tree(self, path_map: Dict[str, str]) -> str:
        self._tree_counter += 1
        sha = f"tree_{self._tree_counter}"
        self._trees[sha] = deepcopy(path_map)
        return sha

    def _new_commit(self, tree_sha: str) -> str:
        self._commit_counter += 1
        sha = f"commit_{self._commit_counter}"
        self._commits[sha] = tree_sha
        return sha


class CareerCorpusMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.corpus_path = root / "career_corpus.json"
        self.meta_path = root / "career_corpus.meta.json"
        self.schema_path = (
            Path(__file__).resolve().parents[1]
            / "knowledge_files"
            / "career_corpus.schema.json"
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_corpus(self, with_ids: bool = True) -> Dict[str, Any]:
        corpus = make_corpus(with_ids=with_ids)
        self.corpus_path.write_text(json.dumps(corpus), encoding="utf-8")
        return corpus

    def _store(self) -> CareerCorpusStore:
        return CareerCorpusStore(
            path=self.corpus_path,
            meta_path=self.meta_path,
            schema_path=self.schema_path,
            validate_on_load=True,
            validate_on_save=True,
        )

    def _sync_with_repo(self, store: CareerCorpusStore, repo: FakeGitRepo) -> CareerCorpusSync:
        return CareerCorpusSync(
            store=store,
            get_memory_repo=repo.get_memory_repo,
            get_branch_ref=repo.get_branch_ref,
            get_git_commit=repo.get_git_commit,
            get_git_tree=repo.get_git_tree,
            get_git_blob=repo.get_git_blob,
            create_git_blob=repo.create_git_blob,
            create_git_tree=repo.create_git_tree,
            create_git_commit=repo.create_git_commit,
            update_branch_ref=repo.update_branch_ref,
        )

    def test_load_save_atomicity(self) -> None:
        self._write_corpus(with_ids=True)
        store = self._store()
        store.load()
        store.set(["profile", "full_name"], "Updated User")
        self.assertTrue(store.dirty)
        store.save()
        self.assertFalse(store.dirty)
        reloaded = json.loads(self.corpus_path.read_text(encoding="utf-8"))
        self.assertEqual(reloaded["profile"]["full_name"], "Updated User")
        tmp_path = self.corpus_path.with_name(f".{self.corpus_path.name}.tmp")
        self.assertFalse(tmp_path.exists())

    def test_id_assignment_on_load(self) -> None:
        self._write_corpus(with_ids=False)
        store = self._store()
        loaded = store.load()
        self.assertTrue(store.dirty)
        self.assertIn("id", loaded["experience"][0])
        self.assertIn("id", loaded["projects"][0])
        self.assertIn("id", loaded["certifications"][0])
        self.assertIn("id", loaded["education"][0])

    def test_upsert_experience_semantics(self) -> None:
        self._write_corpus(with_ids=True)
        store = self._store()
        corpus = store.load()
        existing = corpus["experience"][0]

        updated = dict(existing)
        updated["outcomes"] = ["Updated outcome"]
        returned_id = store.upsert_experience(updated)
        self.assertEqual(returned_id, existing["id"])
        self.assertEqual(len(store.list_experiences()), 1)
        self.assertEqual(store.list_experiences()[0]["outcomes"], ["Updated outcome"])

        fallback_update = {
            "employer": existing["employer"],
            "title": existing["title"],
            "start_date": existing["start_date"],
            "end_date": existing["end_date"],
            "location": existing["location"],
            "bullets": ["Changed by fallback"],
            "tools": existing["tools"],
            "outcomes": existing["outcomes"],
            "domain_tags": existing["domain_tags"],
        }
        store.upsert_experience(fallback_update)
        self.assertEqual(len(store.list_experiences()), 1)
        self.assertEqual(store.list_experiences()[0]["bullets"], ["Changed by fallback"])

    def test_pull_noop_when_sha_unchanged(self) -> None:
        self._write_corpus(with_ids=True)
        store = self._store()
        store.load()
        split_docs = store.build_split_documents()
        repo = FakeGitRepo(split_docs)
        current_index_sha = repo.head_path_map()[CareerCorpusStore.INDEX_FILE]
        store.mark_push_success(remote_file_sha=current_index_sha, remote_file_hashes=split_docs[CareerCorpusStore.INDEX_FILE]["file_hashes"])

        sync = self._sync_with_repo(store, repo)
        result = sync.pull()
        self.assertTrue(result["ok"])
        self.assertFalse(result["changed"])
        self.assertEqual(result["reason"], "sha_unchanged")

    def test_push_blob_utf8_success_with_verification(self) -> None:
        self._write_corpus(with_ids=True)
        store = self._store()
        store.load()
        repo = FakeGitRepo(store.build_split_documents())

        store.set(["profile", "full_name"], "Dirty User")
        sync = self._sync_with_repo(store, repo)
        result = sync.push("Blob flow push")
        self.assertTrue(result["ok"])
        self.assertTrue(result["pushed"])
        self.assertTrue(result["persisted"])
        self.assertEqual(result["method"], "git_blob_utf8_split")
        self.assertTrue(result["verification"]["ok"])
        self.assertEqual(result["retry_count"], 0)
        self.assertGreater(repo.calls["create_git_blob"], 0)
        self.assertEqual(store.status()["remote_branch"], "main")

    def test_push_not_dirty_no_remote_calls(self) -> None:
        self._write_corpus(with_ids=True)
        store = self._store()
        store.load()
        repo = FakeGitRepo(store.build_split_documents())
        sync = self._sync_with_repo(store, repo)

        result = sync.push("No-op")
        self.assertTrue(result["ok"])
        self.assertFalse(result["pushed"])
        self.assertTrue(result["persisted"])
        self.assertEqual(repo.calls["get_memory_repo"], 0)
        self.assertEqual(repo.calls["create_git_blob"], 0)

    def test_push_ref_conflict_retries_once_then_succeeds(self) -> None:
        self._write_corpus(with_ids=True)
        store = self._store()
        store.load()
        repo = FakeGitRepo(store.build_split_documents())
        repo.ref_conflicts_remaining = 1
        store.set(["profile", "full_name"], "Dirty User")

        sync = self._sync_with_repo(store, repo)
        result = sync.push("Retry once")
        self.assertTrue(result["ok"])
        self.assertTrue(result["persisted"])
        self.assertEqual(result["retry_count"], 1)
        self.assertGreaterEqual(repo.calls["update_branch_ref"], 2)

    def test_push_ref_conflict_retries_once_then_fails_not_persisted(self) -> None:
        self._write_corpus(with_ids=True)
        store = self._store()
        store.load()
        repo = FakeGitRepo(store.build_split_documents())
        repo.ref_conflicts_remaining = 99
        store.set(["profile", "full_name"], "Dirty User")

        sync = self._sync_with_repo(store, repo)
        result = sync.push("Retry fail")
        self.assertFalse(result["ok"])
        self.assertFalse(result["persisted"])
        self.assertEqual(result["error_code"], "ref_conflict")
        self.assertEqual(result["retry_count"], 1)

    def test_push_hash_mismatch_marks_transport_corruption(self) -> None:
        self._write_corpus(with_ids=True)
        store = self._store()
        store.load()
        repo = FakeGitRepo(store.build_split_documents())
        store.set(["profile", "full_name"], "Dirty User")
        repo.tamper_tree_paths.add(CareerCorpusStore.INDEX_FILE)

        sync = self._sync_with_repo(store, repo)
        result = sync.push("Mismatch")
        self.assertFalse(result["ok"])
        self.assertTrue(result["pushed"])
        self.assertFalse(result["persisted"])
        self.assertEqual(result["error_code"], "transport_corruption")

    def test_meta_migration_old_remote_sha_fields_supported(self) -> None:
        self._write_corpus(with_ids=True)
        legacy_meta = {
            "remote_sha": "legacy_sha_only",
            "local_hash": "abc",
            "last_pull_utc": "2026-01-01T00:00:00Z",
            "last_push_utc": "2026-01-01T00:00:00Z",
        }
        self.meta_path.write_text(json.dumps(legacy_meta), encoding="utf-8")
        store = self._store()
        status = store.status()
        self.assertEqual(status["remote_file_sha"], "legacy_sha_only")
        self.assertEqual(status["remote_sha"], "legacy_sha_only")

    def test_pull_split_handles_raw_blob_text(self) -> None:
        self._write_corpus(with_ids=True)
        store = self._store()
        store.load()
        repo = FakeGitRepo(store.build_split_documents())
        repo.raw_blob_mode = "raw_text"

        sync = self._sync_with_repo(store, repo)
        result = sync.pull(force=True)
        self.assertTrue(result["ok"])
        self.assertTrue(result["changed"])

    def test_pull_split_handles_raw_blob_json_object(self) -> None:
        self._write_corpus(with_ids=True)
        store = self._store()
        store.load()
        repo = FakeGitRepo(store.build_split_documents())
        repo.raw_blob_mode = "raw_json_object"

        sync = self._sync_with_repo(store, repo)
        result = sync.pull(force=True)
        self.assertTrue(result["ok"])
        self.assertTrue(result["changed"])


if __name__ == "__main__":
    unittest.main()
