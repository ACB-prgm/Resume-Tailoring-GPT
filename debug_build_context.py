#!/usr/bin/env python3
"""Simple local debugger for build_context().

Edit the variables below, then run:
  venv/bin/python debug_build_context.py
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from knowledge_files.intent_context_router_surface import Intent, RuntimeState, build_context


# ---------------------------------------------------------------------------
# Edit these values only.
# ---------------------------------------------------------------------------
INTENT = Intent.JD_ANALYSIS

STATE_OVERRIDES = {
    # Example overrides:
    "repo_exists": True,
    "runtime_initialized": True,
    "corpus_loaded": True,
    "corpus_exists": True,
    "corpus_valid": True,
}

# Return full verbose ContextPack when True; compact model-facing output when False.
VERBOSE = False

# Include intent/runtime_state input block before the function output.
INCLUDE_INPUT = False
# ---------------------------------------------------------------------------


def _jsonable(value: Any) -> Any:
    """Convert router values to JSON-serializable shapes."""
    if isinstance(value, Intent):
        return value.value
    if callable(value):
        return getattr(value, "__name__", type(value).__name__)
    if isinstance(value, set):
        return sorted(_jsonable(v) for v in value)
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def _pack_to_dict(pack: Any) -> dict[str, Any]:
    """Return the full build_context output as a JSON-friendly dict."""
    atoms = []
    for atom in pack.atoms:
        atoms.append(
            {
                "id": atom.id,
                "title": atom.title,
                "content": atom.content,
                "intents": [intent.value for intent in atom.intents],
                "priority": atom.priority,
                "restrictive": atom.restrictive,
                "tags": sorted(atom.tags),
                "source_ref": atom.source_ref,
                "predicate": getattr(atom.predicate, "__name__", str(atom.predicate)),
            }
        )

    return {
        "intent": pack.intent.value,
        "atoms": atoms,
        "rendered_context": pack.rendered_context,
        "rerouted_to": [route.value for route in pack.rerouted_to],
        "required_routes": [route.value for route in pack.required_routes],
        "block_current_intent": pack.block_current_intent,
        "block_reason": pack.block_reason,
        "next_step_hint": pack.next_step_hint,
        "diagnostics": _jsonable(pack.diagnostics),
    }


def main() -> None:
    """Run the script entrypoint."""
    default_state = asdict(RuntimeState())
    state_data = {**default_state, **STATE_OVERRIDES}
    state = RuntimeState(**state_data)
    result = build_context(INTENT, state, verbose=VERBOSE)
    if VERBOSE:
        output: dict[str, Any] = {"context_pack": _pack_to_dict(result)}
    else:
        compact_text = str(result)
        output = {
            "context": compact_text.splitlines(),
        }
    if INCLUDE_INPUT:
        output["input"] = {
            "intent": INTENT.value,
            "runtime_state": state_data,
        }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
