"""
Local-first career corpus store.

This module keeps an authoritative local `career_corpus.json`, supports
in-memory editing, and can materialize split JSON documents for remote storage.
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


def _canonical_json_text(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _canonical_json_sha256(obj: Dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json_text(obj).encode("utf-8")).hexdigest()


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

    INDEX_FILE = "corpus_index.json"
    PROFILE_FILE = "corpus_profile.json"
    SUMMARY_FILE = "corpus_summary_facts.json"
    SKILLS_FILE = "corpus_skills.json"
    CERTIFICATIONS_FILE = "corpus_certifications.json"
    EDUCATION_FILE = "corpus_education.json"
    METADATA_FILE = "corpus_metadata.json"
    SPLIT_FORMAT_VERSION = "1.0.0"

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
            "remote_sha": self._meta.get("remote_sha"),  # legacy compatibility
            "remote_file_sha": self._meta.get("remote_file_sha"),
            "remote_blob_sha": self._meta.get("remote_blob_sha"),
            "remote_commit_sha": self._meta.get("remote_commit_sha"),
            "remote_branch": self._meta.get("remote_branch"),
            "remote_file_hashes": self._meta.get("remote_file_hashes") or {},
            "last_pull_utc": self._meta.get("last_pull_utc"),
            "last_push_utc": self._meta.get("last_push_utc"),
            "last_verified_utc": self._meta.get("last_verified_utc"),
            "last_push_method": self._meta.get("last_push_method"),
        }

    @property
    def is_loaded(self) -> bool:
        return self._corpus is not None

    def validate(self) -> None:
        self._ensure_loaded()

        try:
            from memory_validation import validate_career_corpus  # type: ignore
        except ImportError:
            try:
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

    def build_split_documents(self) -> Dict[str, Dict[str, Any]]:
        """
        Materialize remote split documents.

        Experiences and projects are stored as one file per record.
        """
        self._ensure_loaded()
        corpus = self._corpus
        docs: Dict[str, Dict[str, Any]] = {}

        docs[self.PROFILE_FILE] = {"profile": deepcopy(corpus["profile"])}
        docs[self.SUMMARY_FILE] = {"summary_facts": deepcopy(corpus["summary_facts"])}
        docs[self.SKILLS_FILE] = {"skills": deepcopy(corpus["skills"])}
        docs[self.CERTIFICATIONS_FILE] = {"certifications": deepcopy(corpus["certifications"])}
        docs[self.EDUCATION_FILE] = {"education": deepcopy(corpus["education"])}
        docs[self.METADATA_FILE] = {"metadata": deepcopy(corpus["metadata"])}

        experience_files = []
        for exp in corpus.get("experience", []):
            exp_id = exp["id"]
            path = f"corpus_experience_{exp_id}.json"
            docs[path] = {"experience": deepcopy(exp)}
            experience_files.append({"id": exp_id, "path": path})

        project_files = []
        for proj in corpus.get("projects", []):
            proj_id = proj["id"]
            path = f"corpus_project_{proj_id}.json"
            docs[path] = {"project": deepcopy(proj)}
            project_files.append({"id": proj_id, "path": path})

        file_hashes = {
            path: _canonical_json_sha256(doc)
            for path, doc in docs.items()
        }
        index_doc = {
            "format_version": self.SPLIT_FORMAT_VERSION,
            "schema_version": corpus["schema_version"],
            "generated_at_utc": _utc_now(),
            "core_files": {
                "profile": self.PROFILE_FILE,
                "summary_facts": self.SUMMARY_FILE,
                "skills": self.SKILLS_FILE,
                "certifications": self.CERTIFICATIONS_FILE,
                "education": self.EDUCATION_FILE,
                "metadata": self.METADATA_FILE,
            },
            "experience_files": experience_files,
            "project_files": project_files,
            "file_hashes": file_hashes,
        }
        docs[self.INDEX_FILE] = index_doc
        return docs

    @classmethod
    def index_referenced_paths(cls, index_doc: Dict[str, Any]) -> List[str]:
        core_files = index_doc.get("core_files", {})
        paths: List[str] = []
        for key in ("profile", "summary_facts", "skills", "certifications", "education", "metadata"):
            path = core_files.get(key)
            if isinstance(path, str) and path:
                paths.append(path)
        for item in index_doc.get("experience_files", []):
            path = item.get("path")
            if isinstance(path, str) and path:
                paths.append(path)
        for item in index_doc.get("project_files", []):
            path = item.get("path")
            if isinstance(path, str) and path:
                paths.append(path)
        return paths

    @classmethod
    def assemble_from_split_documents(
        cls,
        index_doc: Dict[str, Any],
        documents_by_path: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        core_files = index_doc.get("core_files", {})

        def _require(path_key: str) -> Dict[str, Any]:
            path = core_files.get(path_key)
            if not isinstance(path, str) or path not in documents_by_path:
                raise ValueError(f"Missing required split file for '{path_key}'.")
            return documents_by_path[path]

        profile_doc = _require("profile")
        summary_doc = _require("summary_facts")
        skills_doc = _require("skills")
        certs_doc = _require("certifications")
        edu_doc = _require("education")
        metadata_doc = _require("metadata")

        experience = []
        for item in index_doc.get("experience_files", []):
            path = item.get("path")
            if not isinstance(path, str) or path not in documents_by_path:
                raise ValueError(f"Missing experience split file: {path}")
            exp_doc = documents_by_path[path]
            if "experience" not in exp_doc:
                raise ValueError(f"Invalid experience split file shape: {path}")
            experience.append(deepcopy(exp_doc["experience"]))

        projects = []
        for item in index_doc.get("project_files", []):
            path = item.get("path")
            if not isinstance(path, str) or path not in documents_by_path:
                raise ValueError(f"Missing project split file: {path}")
            proj_doc = documents_by_path[path]
            if "project" not in proj_doc:
                raise ValueError(f"Invalid project split file shape: {path}")
            projects.append(deepcopy(proj_doc["project"]))

        corpus = {
            "schema_version": index_doc.get("schema_version", "1.0.0"),
            "profile": deepcopy(profile_doc.get("profile", {})),
            "summary_facts": deepcopy(summary_doc.get("summary_facts", [])),
            "experience": experience,
            "projects": projects,
            "skills": deepcopy(skills_doc.get("skills", {})),
            "certifications": deepcopy(certs_doc.get("certifications", [])),
            "education": deepcopy(edu_doc.get("education", [])),
            "metadata": deepcopy(metadata_doc.get("metadata", {})),
        }
        return corpus

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
        self._ensure_loaded()
        node: Any = self._corpus
        for part in path:
            node = node[part]
        return deepcopy(node)

    def set(self, path: List[PathPart], value: Any) -> None:
        self._ensure_loaded()
        if not path:
            raise ValueError("Path cannot be empty.")
        parent, last = self._resolve_parent(path)
        parent[last] = value
        self._mark_dirty()

    def update(self, mutator_fn: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]) -> None:
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

    def replace_corpus(
        self,
        corpus: Dict[str, Any],
        remote_file_sha: Optional[str] = None,
        remote_branch: Optional[str] = None,
        remote_file_hashes: Optional[Dict[str, str]] = None,
    ) -> None:
        if not isinstance(corpus, dict):
            raise TypeError("Corpus document must be an object.")
        self._corpus = deepcopy(corpus)
        ids_added = self._ensure_ids_for_known_lists()
        self.validate()
        self._atomic_write_json(self.path, self._corpus)
        self._local_hash = self._compute_hash(self._corpus)
        self._meta["local_hash"] = self._local_hash
        if remote_file_sha is not None:
            self._meta["remote_file_sha"] = remote_file_sha
            self._meta["remote_sha"] = remote_file_sha
        if remote_branch is not None:
            self._meta["remote_branch"] = remote_branch
        if remote_file_hashes is not None:
            self._meta["remote_file_hashes"] = deepcopy(remote_file_hashes)
        self._meta["last_pull_utc"] = _utc_now()
        self.dirty = ids_added
        self._write_meta()

    def mark_push_success(
        self,
        remote_file_sha: Optional[str] = None,
        remote_blob_sha: Optional[str] = None,
        remote_commit_sha: Optional[str] = None,
        remote_branch: Optional[str] = None,
        remote_file_hashes: Optional[Dict[str, str]] = None,
        method: str = "git_blob_utf8",
        verified: bool = True,
    ) -> None:
        if remote_file_sha is not None:
            self._meta["remote_file_sha"] = remote_file_sha
            self._meta["remote_sha"] = remote_file_sha
        if remote_blob_sha is not None:
            self._meta["remote_blob_sha"] = remote_blob_sha
        if remote_commit_sha is not None:
            self._meta["remote_commit_sha"] = remote_commit_sha
        if remote_branch is not None:
            self._meta["remote_branch"] = remote_branch
        if remote_file_hashes is not None:
            self._meta["remote_file_hashes"] = deepcopy(remote_file_hashes)
        self._meta["last_push_utc"] = _utc_now()
        self._meta["last_push_method"] = method
        if verified:
            self._meta["last_verified_utc"] = _utc_now()
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
        canonical = _canonical_json_text(document)
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
                "remote_file_sha": None,
                "remote_blob_sha": None,
                "remote_commit_sha": None,
                "remote_branch": None,
                "remote_file_hashes": {},
                "last_verified_utc": None,
                "last_push_method": None,
                "local_hash": None,
                "last_pull_utc": None,
                "last_push_utc": None,
            }
        data = self._read_json_object(self.meta_path)
        legacy_remote_sha = data.get("remote_sha")
        remote_file_sha = data.get("remote_file_sha") or legacy_remote_sha
        hashes = data.get("remote_file_hashes")
        return {
            "remote_sha": legacy_remote_sha or remote_file_sha,
            "remote_file_sha": remote_file_sha,
            "remote_blob_sha": data.get("remote_blob_sha"),
            "remote_commit_sha": data.get("remote_commit_sha"),
            "remote_branch": data.get("remote_branch"),
            "remote_file_hashes": hashes if isinstance(hashes, dict) else {},
            "last_verified_utc": data.get("last_verified_utc"),
            "last_push_method": data.get("last_push_method"),
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
