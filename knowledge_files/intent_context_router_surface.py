"""GPT-facing surface for intent resolution and atom-based context routing."""

from __future__ import annotations

from typing import Any, Union

try:
    from intent_context_router_core import (
        ContextAtom,
        ContextPack,
        Intent,
        RuntimeState,
        build_context as _build_context,
    )
except ImportError:
    from knowledge_files.intent_context_router_core import (  # type: ignore
        ContextAtom,
        ContextPack,
        Intent,
        RuntimeState,
        build_context as _build_context,
    )


__all__ = [
    "Intent",
    "RuntimeState",
    "ContextAtom",
    "ContextPack",
    "build_context",
]


# RuntimeState field contract (GPT-facing)
# Use these definitions when constructing RuntimeState for build_context(...).
#
# repo_exists: memory repository exists in user's GitHub.
# runtime_initialized: runtime bootstrap/auth completed for this session.
# corpus_exists: canonical corpus files exist in GitHub repo.
# corpus_loaded: corpus has been pulled from GitHub and loaded locally.
# corpus_valid: locally loaded corpus passed validation.
# onboarding_complete: corpus metadata indicates onboarding is complete.
# approved_markdown_ready: resume markdown is finalized and approved for export.
# last_jd_analysis_present: a JD analysis result exists for current drafting flow.
# last_operation_failed: most recent memory/runtime operation failed.
# status_changed_since_last_emit: memory status changed since last status emission.
# user_requested_memory_status: user explicitly asked for memory status this turn.
# technical_detail_requested: user requested technical/debug-level response detail.
# repo_create_attempted_this_turn: createMemoryRepo was already attempted this turn.


def gpt_surface(obj: Any) -> Any:
    """When to use: mark a symbol as GPT-facing surface API."""
    obj.__gpt_layer__ = "surface"
    obj.__gpt_surface__ = True
    return obj


def gpt_core(obj: Any) -> Any:
    """When to use: mark a symbol as internal core API."""
    obj.__gpt_layer__ = "core"
    obj.__gpt_core__ = True
    return obj


gpt_surface(Intent)
gpt_surface(RuntimeState)
gpt_surface(ContextAtom)
gpt_surface(ContextPack)


@gpt_surface
def build_context(
    intent: Intent,
    state: RuntimeState,
    verbose: bool = False,
    max_reroutes: int = 6,
) -> Union[ContextPack, str]:
    """When to use: build routed context for one intent. Inputs: intent + runtime state. Outputs: compact string (default) or ContextPack (verbose)."""
    return _build_context(intent, state, verbose=verbose, max_reroutes=max_reroutes)
