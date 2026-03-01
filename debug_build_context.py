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
    # "repo_exists": True,
    # "runtime_initialized": True,
    # "corpus_loaded": True,
    # "corpus_exists": True,
    # "corpus_valid": True,
}

# Default output is exactly what the model sees: rendered_context only.
PRINT_RENDERED_CONTEXT_ONLY = True

# If False above, this controls whether atom content is shown in detailed output.
SHOW_ATOM_CONTENT = True
# ---------------------------------------------------------------------------


def _jsonable(value: Any) -> Any:
    """Internal helper to jsonable."""
    if isinstance(value, Intent):
        return value.value
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def main() -> None:
    """Run the script entrypoint."""
    default_state = asdict(RuntimeState())
    state_data = {**default_state, **STATE_OVERRIDES}
    state = RuntimeState(**state_data)
    pack = build_context(INTENT, state)

    if PRINT_RENDERED_CONTEXT_ONLY:
        print(pack.rendered_context)
        return

    print("=== INPUT ===")
    print(f"intent: {INTENT.value}")
    print("runtime_state:")
    for key in sorted(state_data.keys()):
        print(f"  {key}: {state_data[key]}")

    print("\n=== OUTPUT ===")
    print(f"block_current_intent: {pack.block_current_intent}")
    print(f"block_reason: {pack.block_reason or 'None'}")
    print(f"next_step_hint: {pack.next_step_hint or 'None'}")
    print("required_routes:")
    if pack.required_routes:
        for route in pack.required_routes:
            print(f"  - {route.value}")
    else:
        print("  - (none)")

    print("\natoms:")
    if not pack.atoms:
        print("  - (none)")
    else:
        for index, atom in enumerate(pack.atoms, start=1):
            print(f"  {index}. {atom.title}")
            print(f"     id={atom.id} priority={atom.priority} restrictive={atom.restrictive}")
            if SHOW_ATOM_CONTENT:
                print("     content:")
                for line in atom.content.splitlines():
                    print(f"       {line}")

    print("\nrendered_context:")
    print(pack.rendered_context or "(empty)")

    print("\ndiagnostics:")
    print(json.dumps(_jsonable(pack.diagnostics), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
