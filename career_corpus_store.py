"""
Local-first career corpus store.

This module keeps a local authoritative cache of `career_corpus.json` and a
small sync metadata file. It is optimized for fast in-session edits by loading
once, editing in memory, and writing atomically only when changed.
"""

from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import uuid4

from jsonschema import Draft202012Validator


PathPart = Union[str, int]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _default_schema_path() -> Path:
    candidates = [
        Path("/mnt/data/career_corpus.schema.json"),
        Path(__file__).resolve().parent / "career_corpus.schema.json",
        Path(__file__).resolve().parent / "knowledge_files" / "career_corpus.schema.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("/mnt/data/career_corpus.schema.json")


class CareerCorpusStore:
    """In-memory editor + atomic persistence for `career_corpus.json`."""

    ID_PREFIXES = {
        "experience": "exp",
        "projects": "proj",
        "certifications": "cert",
        "education": "edu",
    }

    def __init__(
        self,
        path: Union[str, Path] = "/mnt/data/career_corpus.json",
        meta_path: Union[str, Path] = "/mnt/data/career_corpus.meta.json",
        schema_path: Optional[Union[str, Path]] = None,
        validate_on_load: bool = True,
        validate_on_save: bool = True,
    ) -> None:
        self.path = Path(path)
        self.meta_path = Path(meta_path)
        self.schema_path = Path(schema_path) if schema_path else _default_schema_path()
        self.validate_on_load = validate_on_load
        self.validate_on_save = validate_on_save

        self._corpus: Optional[Dict[str, Any]] = None
        self.dirty = False
        self._local_hash: Optional[str] = None
        self._meta = self._read_meta()

    def load(self) -> Dict[str, Any]:
        """Load corpus JSON from disk into memory once per session."""
        if not self.path.exists():
            raise FileNotFoundError(f"Corpus file not found: {self.path}")

        data = self._read_json_object(self.path)
        self._corpus = data
        ids_added = self._ensure_ids_for_known_lists()

        if self.validate_on_load:
            self.validate()

        self._local_hash = self._compute_hash(self._corpus)
        self._meta["local_hash"] = self._local_hash
        self.dirty = ids_added
        self._write_meta()
        return deepcopy(self._corpus)

    def save(self) -> None:
        """Persist corpus to disk atomically only when dirty."""
        self._ensure_loaded()
        if not self.dirty:
            return

        if self.validate_on_save:
            self.validate()

        self._atomic_write_json(self.path, self._corpus)
        self._local_hash = self._compute_hash(self._corpus)
        self._meta["local_hash"] = self._local_hash
        self.dirty = False
        self._write_meta()

    def status(self) -> Dict[str, Any]:
        return {
            "dirty": self.dirty,
            "local_hash": self._local_hash,
            "remote_sha": self._meta.get("remote_sha"),
            "last_pull_utc": self._meta.get("last_pull_utc"),
            "last_push_utc": self._meta.get("last_push_utc"),
        }

    @property
    def is_loaded(self) -> bool:
        return self._corpus is not None

    def validate(self) -> None:
        """Validate current in-memory corpus against the configured schema."""
        self._ensure_loaded()

        try:
            # Preferred path when deployed with memory_validation.py in /mnt/data.
            from memory_validation import validate_career_corpus  # type: ignore
        except ImportError:
            try:
                # Local-repo fallback where validators live in knowledge_files/.
                from knowledge_files.memory_validation import validate_career_corpus  # type: ignore
            except ImportError:
                validate_career_corpus = None  # type: ignore

        if validate_career_corpus:
            valid, errors = validate_career_corpus(self._corpus)
        else:
            schema = self._read_json_object(self.schema_path)
            validator = Draft202012Validator(schema)
            raw_errors = list(validator.iter_errors(self._corpus))
            errors = [f"{'.'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in raw_errors]
            valid = not raw_errors

        if not valid:
            raise ValueError("Career corpus schema validation failed: " + "; ".join(errors))

    def snapshot(self) -> Dict[str, Any]:
        self._ensure_loaded()
        return deepcopy(self._corpus)

    def list_experiences(self) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        experiences = self._corpus.get("experience", [])
        if not isinstance(experiences, list):
            raise TypeError("Expected 'experience' to be a list.")
        return deepcopy(experiences)

    def get_experience(self, key: Union[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        self._ensure_loaded()
        idx = self._find_experience_index(key)
        if idx is None:
            return None
        return deepcopy(self._corpus["experience"][idx])

    def append_experience(self, obj: Dict[str, Any]) -> str:
        self._ensure_loaded()
        if not isinstance(obj, dict):
            raise TypeError("Experience payload must be an object.")
        experiences = self._corpus.setdefault("experience", [])
        if not isinstance(experiences, list):
            raise TypeError("Expected 'experience' to be a list.")
        item = deepcopy(obj)
        item_id = self._ensure_item_id(item, "experience")
        experiences.append(item)
        self._mark_dirty()
        return item_id

    def upsert_experience(
        self,
        obj: Dict[str, Any],
        match: Optional[Union[Dict[str, Any], Callable[[Dict[str, Any]], bool]]] = None,
    ) -> str:
        self._ensure_loaded()
        if not isinstance(obj, dict):
            raise TypeError("Experience payload must be an object.")

        item = deepcopy(obj)
        experiences = self._corpus.setdefault("experience", [])
        if not isinstance(experiences, list):
            raise TypeError("Expected 'experience' to be a list.")

        idx: Optional[int] = None
        item_id = item.get("id")
        if isinstance(item_id, str) and item_id:
            idx = self._find_experience_index(item_id)

        if idx is None and match is not None:
            idx = self._find_by_match(experiences, match)

        if idx is None:
            fallback = {k: item.get(k) for k in ("employer", "title", "start_date")}
            if all(v is not None for v in fallback.values()):
                idx = self._find_by_match(experiences, fallback)

        if idx is None:
            item_id = self._ensure_item_id(item, "experience")
            experiences.append(item)
            self._mark_dirty()
            return item_id

        existing = deepcopy(experiences[idx])
        if "id" not in item or not item["id"]:
            item["id"] = existing.get("id") or self._ensure_item_id(existing, "experience")
        merged = {**existing, **item}
        experiences[idx] = merged
        self._mark_dirty()
        return str(merged["id"])

    def delete_experience(self, key: Union[str, Dict[str, Any]]) -> bool:
        self._ensure_loaded()
        idx = self._find_experience_index(key)
        if idx is None:
            return False
        del self._corpus["experience"][idx]
        self._mark_dirty()
        return True

    def get(self, path: List[PathPart]) -> Any:
        """Read any nested value by path, for example ['profile', 'full_name']."""
        self._ensure_loaded()
        node: Any = self._corpus
        for part in path:
            node = node[part]
        return deepcopy(node)

    def set(self, path: List[PathPart], value: Any) -> None:
        """Set any nested value by path, for example ['profile', 'full_name']."""
        self._ensure_loaded()
        if not path:
            raise ValueError("Path cannot be empty.")
        parent, last = self._resolve_parent(path)
        parent[last] = value
        self._mark_dirty()

    def update(self, mutator_fn: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]) -> None:
        """
        Apply an in-memory mutator function.

        If the mutator returns a dict, that replaces the current corpus object.
        """
        self._ensure_loaded()
        before = self._compute_hash(self._corpus)
        replacement = mutator_fn(self._corpus)
        if replacement is not None:
            if not isinstance(replacement, dict):
                raise TypeError("Mutator return value must be a dict or None.")
            self._corpus = replacement
        self._ensure_ids_for_known_lists()
        after = self._compute_hash(self._corpus)
        if after != before:
            self._mark_dirty()

    def replace_corpus(self, corpus: Dict[str, Any], remote_sha: Optional[str] = None) -> None:
        """
        Replace in-memory corpus with a full document (used by sync pull).

        The document is validated and written atomically to local disk.
        """
        if not isinstance(corpus, dict):
            raise TypeError("Corpus document must be an object.")
        self._corpus = deepcopy(corpus)
        ids_added = self._ensure_ids_for_known_lists()
        self.validate()
        self._atomic_write_json(self.path, self._corpus)
        self._local_hash = self._compute_hash(self._corpus)
        self._meta["local_hash"] = self._local_hash
        if remote_sha is not None:
            self._meta["remote_sha"] = remote_sha
        self._meta["last_pull_utc"] = _utc_now()
        self.dirty = ids_added
        self._write_meta()

    def mark_push_success(self, remote_sha: str) -> None:
        self._meta["remote_sha"] = remote_sha
        self._meta["last_push_utc"] = _utc_now()
        self._write_meta()

    def _ensure_loaded(self) -> None:
        if self._corpus is None:
            self.load()

    def _mark_dirty(self) -> None:
        self.dirty = True
        self._local_hash = self._compute_hash(self._corpus)
        self._meta["local_hash"] = self._local_hash

    def _find_experience_index(self, key: Union[str, Dict[str, Any]]) -> Optional[int]:
        experiences = self._corpus.get("experience", [])
        if not isinstance(experiences, list):
            raise TypeError("Expected 'experience' to be a list.")
        return self._find_by_match(experiences, key)

    @staticmethod
    def _find_by_match(
        items: List[Dict[str, Any]],
        matcher: Union[str, Dict[str, Any], Callable[[Dict[str, Any]], bool]],
    ) -> Optional[int]:
        if callable(matcher):
            for idx, item in enumerate(items):
                if matcher(item):
                    return idx
            return None

        if isinstance(matcher, str):
            for idx, item in enumerate(items):
                if item.get("id") == matcher:
                    return idx
            return None

        if isinstance(matcher, dict):
            for idx, item in enumerate(items):
                if all(item.get(k) == v for k, v in matcher.items()):
                    return idx
            return None

        raise TypeError("Matcher must be str, dict, or callable.")

    def _ensure_ids_for_known_lists(self) -> bool:
        changed = False
        for section in ("experience", "projects", "certifications", "education"):
            records = self._corpus.get(section, [])
            if not isinstance(records, list):
                continue
            for record in records:
                if isinstance(record, dict):
                    before = record.get("id")
                    after = self._ensure_item_id(record, section)
                    changed = changed or before != after
        return changed

    def _ensure_item_id(self, item: Dict[str, Any], section: str) -> str:
        item_id = item.get("id")
        if isinstance(item_id, str) and item_id.strip():
            return item_id
        prefix = self.ID_PREFIXES.get(section, "item")
        generated = f"{prefix}_{uuid4().hex}"
        item["id"] = generated
        return generated

    @staticmethod
    def _compute_hash(document: Dict[str, Any]) -> str:
        canonical = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _resolve_parent(self, path: List[PathPart]) -> tuple[Any, PathPart]:
        node: Any = self._corpus
        for part in path[:-1]:
            node = node[part]
        return node, path[-1]

    def _read_meta(self) -> Dict[str, Any]:
        if not self.meta_path.exists():
            return {
                "remote_sha": None,
                "local_hash": None,
                "last_pull_utc": None,
                "last_push_utc": None,
            }
        data = self._read_json_object(self.meta_path)
        return {
            "remote_sha": data.get("remote_sha"),
            "local_hash": data.get("local_hash"),
            "last_pull_utc": data.get("last_pull_utc"),
            "last_push_utc": data.get("last_push_utc"),
        }

    def _write_meta(self) -> None:
        self._atomic_write_json(self.meta_path, self._meta)

    @staticmethod
    def _read_json_object(path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"Expected top-level JSON object in {path}")
        return data

    @staticmethod
    def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f".{path.name}.tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
