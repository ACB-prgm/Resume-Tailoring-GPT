"""GPT-facing surface for career corpus storage operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

try:
    from career_corpus_store_core import CareerCorpusStore as _CareerCorpusStoreCore
    from career_corpus_store_core import PathPart
except ImportError:
    from knowledge_files.career_corpus_store_core import CareerCorpusStore as _CareerCorpusStoreCore  # type: ignore
    from knowledge_files.career_corpus_store_core import PathPart  # type: ignore


__all__ = ["CareerCorpusStore"]


def gpt_surface(obj: Any) -> Any:
    """When to use: mark a callable as GPT-facing surface API."""
    obj.__gpt_layer__ = "surface"
    obj.__gpt_surface__ = True
    return obj


def gpt_core(obj: Any) -> Any:
    """When to use: mark a callable as internal core API."""
    obj.__gpt_layer__ = "core"
    obj.__gpt_core__ = True
    return obj


@gpt_surface
class CareerCorpusStore:
    """Thin GPT-facing wrapper around corpus store core behavior."""

    REMOTE_DIR = _CareerCorpusStoreCore.REMOTE_DIR
    INDEX_FILE = _CareerCorpusStoreCore.INDEX_FILE
    PROFILE_FILE = _CareerCorpusStoreCore.PROFILE_FILE
    CERTIFICATIONS_FILE = _CareerCorpusStoreCore.CERTIFICATIONS_FILE
    EDUCATION_FILE = _CareerCorpusStoreCore.EDUCATION_FILE
    METADATA_FILE = _CareerCorpusStoreCore.METADATA_FILE
    EXPERIENCE_FILE_PREFIX = _CareerCorpusStoreCore.EXPERIENCE_FILE_PREFIX
    PROJECT_FILE_PREFIX = _CareerCorpusStoreCore.PROJECT_FILE_PREFIX
    SPLIT_FORMAT_VERSION = _CareerCorpusStoreCore.SPLIT_FORMAT_VERSION

    @gpt_surface
    def __init__(
        self,
        path: Union[str, Path] = "/mnt/data/career_corpus.json",
        meta_path: Union[str, Path] = "/mnt/data/career_corpus.meta.json",
        schema_path: Optional[Union[str, Path]] = None,
        validate_on_load: bool = True,
        validate_on_save: bool = True,
    ) -> None:
        """When to use: create the local-first memory store. Inputs: file paths + validation flags. Outputs: initialized store handle."""
        self._core = _CareerCorpusStoreCore(
            path=path,
            meta_path=meta_path,
            schema_path=schema_path,
            validate_on_load=validate_on_load,
            validate_on_save=validate_on_save,
        )

    @property
    def _core_store(self) -> _CareerCorpusStoreCore:
        """Internal helper to core store."""
        return self._core

    @property
    def dirty(self) -> bool:
        """Dirty."""
        return self._core.dirty

    @property
    def is_loaded(self) -> bool:
        """Is loaded."""
        return self._core.is_loaded

    @gpt_surface
    def load(self) -> Dict[str, Any]:
        """When to use: hydrate local corpus from disk. Inputs: none. Outputs: deep-copied corpus object."""
        return self._core.load()

    @gpt_surface
    def save(self) -> None:
        """When to use: atomically persist local edits. Inputs: none. Outputs: none."""
        self._core.save()

    @gpt_surface
    def status(self) -> Dict[str, Any]:
        """When to use: inspect local/remote sync metadata. Inputs: none. Outputs: status dictionary."""
        return self._core.status()

    @gpt_surface
    def snapshot(self) -> Dict[str, Any]:
        """When to use: read an immutable view of current corpus. Inputs: none. Outputs: deep-copied corpus object."""
        return self._core.snapshot()

    @gpt_surface
    def get(self, path: List[PathPart]) -> Any:
        """When to use: read a nested value from corpus. Inputs: list path. Outputs: deep-copied value."""
        return self._core.get(path)

    @gpt_surface
    def set(self, path: List[PathPart], value: Any) -> None:
        """When to use: assign one nested value. Inputs: list path + value. Outputs: none."""
        self._core.set(path, value)

    @gpt_surface
    def update(self, mutator_fn: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]) -> None:
        """When to use: apply batch in-memory mutations. Inputs: mutator callable. Outputs: none."""
        self._core.update(mutator_fn)

    @gpt_surface
    def replace_corpus(
        self,
        corpus: Dict[str, Any],
        remote_file_sha: Optional[str] = None,
        remote_branch: Optional[str] = None,
        remote_file_hashes: Optional[Dict[str, str]] = None,
        validate: bool = True,
    ) -> None:
        """When to use: replace local corpus from trusted assembled docs. Inputs: corpus + optional remote metadata. Outputs: none."""
        self._core.replace_corpus(
            corpus=corpus,
            remote_file_sha=remote_file_sha,
            remote_branch=remote_branch,
            remote_file_hashes=remote_file_hashes,
            validate=validate,
        )

    @gpt_surface
    def build_split_documents(self) -> Dict[str, Dict[str, Any]]:
        """When to use: materialize split corpus docs for Git Data writes. Inputs: none. Outputs: path->document map."""
        return self._core.build_split_documents()

    @gpt_surface
    def index_referenced_paths(self, index_doc: Dict[str, Any]) -> List[str]:
        """When to use: resolve split file list from corpus manifest. Inputs: index doc. Outputs: ordered file path list."""
        return self._core.index_referenced_paths(index_doc)

    @gpt_surface
    def assemble_from_split_documents(
        self,
        index_doc: Dict[str, Any],
        documents_by_path: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """When to use: assemble one corpus from split docs. Inputs: index doc + path->doc map. Outputs: corpus object."""
        return self._core.assemble_from_split_documents(index_doc, documents_by_path)

    @gpt_surface
    def list_experiences(self) -> List[Dict[str, Any]]:
        """When to use: list normalized experience entries. Inputs: none. Outputs: list of experience objects."""
        return self._core.list_experiences()

    @gpt_surface
    def upsert_experience(
        self,
        obj: Dict[str, Any],
        match: Optional[Union[Dict[str, Any], Callable[[Dict[str, Any]], bool]]] = None,
    ) -> str:
        """When to use: insert or update one experience record. Inputs: experience object + optional matcher. Outputs: stable experience id."""
        return self._core.upsert_experience(obj=obj, match=match)
