"""GPT-facing surface for intent resolution and atom-based context routing."""

from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from intent_context_router_core import (
        ContextAtom,
        ContextPack,
        Intent,
        RuntimeState,
        build_context as _build_context,
        resolve_intent as _resolve_intent,
    )
except ImportError:
    from knowledge_files.intent_context_router_core import (  # type: ignore
        ContextAtom,
        ContextPack,
        Intent,
        RuntimeState,
        build_context as _build_context,
        resolve_intent as _resolve_intent,
    )


__all__ = [
    "Intent",
    "RuntimeState",
    "ContextAtom",
    "ContextPack",
    "resolve_intent",
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
def resolve_intent(user_text: str, hints: Optional[Dict[str, Any]] = None) -> Intent:
    """When to use: map user text to one deterministic primary intent. Inputs: user text + optional hints. Outputs: Intent enum."""
    return _resolve_intent(user_text, hints)


@gpt_surface
def build_context(intent: Intent, state: RuntimeState) -> ContextPack:
    """When to use: build ordered atom context and precondition routes for one intent. Inputs: intent + runtime state. Outputs: ContextPack."""
    return _build_context(intent, state)
