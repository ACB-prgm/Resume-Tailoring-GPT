"""GPT-facing surface for GitHub memory synchronization."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

try:
    from career_corpus_store_core import CareerCorpusStore as _CareerCorpusStoreCore
    from career_corpus_sync_core import CareerCorpusSync as _CareerCorpusSyncCore
except ImportError:
    from knowledge_files.career_corpus_store_core import CareerCorpusStore as _CareerCorpusStoreCore  # type: ignore
    from knowledge_files.career_corpus_sync_core import CareerCorpusSync as _CareerCorpusSyncCore  # type: ignore


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


__all__ = ["CareerCorpusSync"]


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
class CareerCorpusSync:
    """Thin GPT-facing wrapper around sync core behavior."""

    @gpt_surface
    def __init__(
        self,
        store: Any,
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
        """When to use: create the sync orchestrator. Inputs: store + GitHub adapter callables. Outputs: initialized sync handle."""
        core_store = getattr(store, "_core_store", store)
        if not isinstance(core_store, _CareerCorpusStoreCore):
            raise TypeError("store must be CareerCorpusStore surface/core instance")

        self._core = _CareerCorpusSyncCore(
            store=core_store,
            get_memory_repo=get_memory_repo,
            get_branch_ref=get_branch_ref,
            get_git_commit=get_git_commit,
            get_git_tree=get_git_tree,
            get_git_blob=get_git_blob,
            create_git_blob=create_git_blob,
            create_git_tree=create_git_tree,
            create_git_commit=create_git_commit,
            update_branch_ref=update_branch_ref,
            max_retries=max_retries,
        )

    @staticmethod
    @gpt_surface
    def bootstrap_memory_repo(
        get_memory_repo: GetMemoryRepoFn,
        create_memory_repo: CreateMemoryRepoFn,
        turn_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """When to use: deterministically ensure fixed memory repo exists. Inputs: get/create repo callables + optional turn state. Outputs: bootstrap result object."""
        return _CareerCorpusSyncCore.bootstrap_memory_repo(get_memory_repo, create_memory_repo, turn_state)

    @gpt_surface
    def pull(self, force: bool = False) -> Dict[str, Any]:
        """When to use: refresh local cache from remote split docs. Inputs: optional force flag. Outputs: pull result object."""
        return self._core.pull(force=force)

    @gpt_surface
    def pull_if_stale_before_write(self, force: bool = False) -> Dict[str, Any]:
        """When to use: avoid redundant pull before push when local state is fresh. Inputs: optional force flag. Outputs: pull decision/result object."""
        return self._core.pull_if_stale_before_write(force=force)

    @gpt_surface
    def push(
        self,
        message: str = "Update career corpus memory",
        target_sections: Optional[List[str]] = None,
        approved_sections: Optional[Dict[str, Any]] = None,
        user_git_fluency: str = "non_technical",
        technical_details_requested: bool = False,
    ) -> Dict[str, Any]:
        """When to use: persist approved local changes to GitHub. Inputs: commit message + optional section approval scope. Outputs: push status object."""
        return self._core.push(
            message=message,
            target_sections=target_sections,
            approved_sections=approved_sections,
            user_git_fluency=user_git_fluency,
            technical_details_requested=technical_details_requested,
        )

    @gpt_surface
    def persist_memory_changes(self, message: str = "Update career corpus memory") -> Dict[str, Any]:
        """When to use: convenience alias for push in memory workflows. Inputs: commit message. Outputs: push status object."""
        return self._core.persist_memory_changes(message=message)
