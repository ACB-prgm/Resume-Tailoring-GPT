"""GPT-facing surface for intent resolution and atom-based context routing."""

from __future__ import annotations

from typing import Any

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
def build_context(intent: Intent, state: RuntimeState) -> ContextPack:
    """When to use: build ordered atom context and precondition routes for one intent. Inputs: intent + runtime state. Outputs: ContextPack."""
    return _build_context(intent, state)
