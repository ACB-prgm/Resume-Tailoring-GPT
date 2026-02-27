"""
Explicit GitHub sync adapter for local-first career corpus storage.

This layer intentionally separates fast local editing from remote persistence.
Only `pull()` and `push()` should cross the tool boundary.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional

from career_corpus_store import CareerCorpusStore

try:
    from memory_validation import (
        assert_validated_before_write,
        build_upsert_payload,
        decode_base64_utf8,
        verify_base64_roundtrip,
    )
except ImportError:
    from knowledge_files.memory_validation import (  # type: ignore
        assert_validated_before_write,
        build_upsert_payload,
        decode_base64_utf8,
        verify_base64_roundtrip,
    )


ReadRemoteFn = Callable[[], Dict[str, Any]]
UpsertRemoteFn = Callable[[Dict[str, Any]], Dict[str, Any]]


class CareerCorpusSync:
    """
    Sync local corpus state with GitHub via injected tool-call adapters.

    Adapter contracts:
    - `read_remote()` returns a dict with GitHub-like contents response fields.
    - `upsert_remote(payload)` accepts {message, content, sha?} and returns a
      dict with at least the resulting file sha, either at top-level `sha` or
      nested under `content.sha`.
    """

    def __init__(
        self,
        store: CareerCorpusStore,
        read_remote: ReadRemoteFn,
        upsert_remote: UpsertRemoteFn,
    ) -> None:
        self.store = store
        self._read_remote = read_remote
        self._upsert_remote = upsert_remote

    def pull(self, force: bool = False) -> Dict[str, Any]:
        """
        Pull remote corpus to local cache.

        No-op when remote SHA matches local meta SHA unless `force=True`.
        """
        response = self._read_remote()
        normalized = self._normalize_read_response(response)

        if not normalized["exists"]:
            return {
                "ok": True,
                "changed": False,
                "reason": "remote_missing",
            }

        status = self.store.status()
        remote_sha = normalized["sha"]
        if (
            not force
            and remote_sha
            and status.get("remote_sha")
            and remote_sha == status["remote_sha"]
        ):
            return {
                "ok": True,
                "changed": False,
                "reason": "sha_unchanged",
                "remote_sha": remote_sha,
            }

        decoded_text = decode_base64_utf8(normalized["content_b64"])
        document = json.loads(decoded_text)
        if not isinstance(document, dict):
            raise ValueError("Remote career_corpus.json is not a JSON object.")

        self.store.replace_corpus(document, remote_sha=remote_sha)
        return {
            "ok": True,
            "changed": True,
            "remote_sha": remote_sha,
            "dirty": self.store.status()["dirty"],
        }

    def push(self, message: str = "Update career_corpus") -> Dict[str, Any]:
        """
        Push local corpus to GitHub only when local state is dirty.
        """
        if not self.store.is_loaded:
            self.store.load()
        if not self.store.dirty:
            return {
                "ok": True,
                "pushed": False,
                "reason": "not_dirty",
                "remote_sha": self.store.status().get("remote_sha"),
            }

        validated = False
        self.store.validate()
        validated = True
        assert_validated_before_write(validated, "career_corpus push")

        # Persist local state first so edits are never stranded only in memory.
        self.store.save()

        snapshot = self.store.snapshot()
        ok, error = verify_base64_roundtrip(snapshot)
        if not ok:
            raise ValueError(f"Base64 preflight failed: {error}")

        status = self.store.status()
        payload = build_upsert_payload(
            message=message,
            json_obj=snapshot,
            sha=status.get("remote_sha"),
        )
        response = self._upsert_remote(payload)
        new_sha = self._extract_sha_from_upsert_response(response)
        if not new_sha:
            raise ValueError("Upsert response missing resulting file sha.")

        self.store.mark_push_success(new_sha)
        return {
            "ok": True,
            "pushed": True,
            "remote_sha": new_sha,
        }

    @staticmethod
    def _normalize_read_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize several possible adapter response shapes into:
        {exists: bool, sha: Optional[str], content_b64: Optional[str]}
        """
        if response is None:
            return {"exists": False, "sha": None, "content_b64": None}

        status_code = response.get("status_code")
        if status_code == 404 or response.get("exists") is False:
            return {"exists": False, "sha": None, "content_b64": None}

        message = str(response.get("message", "")).lower()
        if "not found" in message and "content" not in response:
            return {"exists": False, "sha": None, "content_b64": None}

        if "content_b64" in response:
            return {
                "exists": True,
                "sha": response.get("sha"),
                "content_b64": str(response["content_b64"]).strip(),
            }

        # GitHub contents API shape.
        if isinstance(response.get("content"), str):
            return {
                "exists": True,
                "sha": response.get("sha"),
                "content_b64": response["content"].strip(),
            }

        # Some wrappers may nest response under `content`.
        nested = response.get("content")
        if isinstance(nested, dict) and isinstance(nested.get("content"), str):
            return {
                "exists": True,
                "sha": nested.get("sha") or response.get("sha"),
                "content_b64": nested["content"].strip(),
            }

        raise ValueError("Unsupported read response shape for career corpus pull.")

    @staticmethod
    def _extract_sha_from_upsert_response(response: Dict[str, Any]) -> Optional[str]:
        if not isinstance(response, dict):
            return None
        if isinstance(response.get("sha"), str):
            return response["sha"]
        content = response.get("content")
        if isinstance(content, dict) and isinstance(content.get("sha"), str):
            return content["sha"]
        return None
