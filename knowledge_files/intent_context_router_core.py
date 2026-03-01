"""Deterministic intent router and context pack builder."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Sequence, Tuple, Union

try:
    from context_atoms_core import (
        DEFAULT_MAX_ATOMS,
        DEFAULT_MAX_RENDERED_CHARS,
        AtomSpec,
        get_all_atoms,
        get_atom_indexes,
    )
except ImportError:
    from knowledge_files.context_atoms_core import (  # type: ignore
        DEFAULT_MAX_ATOMS,
        DEFAULT_MAX_RENDERED_CHARS,
        AtomSpec,
        get_all_atoms,
        get_atom_indexes,
    )


def gpt_core(obj: Any) -> Any:
    """Mark symbols as core-layer internals for tooling and audits."""
    obj.__gpt_layer__ = "core"
    obj.__gpt_core__ = True
    return obj


@gpt_core
class Intent(str, Enum):
    """Enum of supported runtime intents for atom context assembly."""
    CONVERSATION_ONLY = "INTENT_CONVERSATION_ONLY"
    FAILURE_RECOVERY = "INTENT_FAILURE_RECOVERY"
    PDF_EXPORT = "INTENT_PDF_EXPORT"
    MEMORY_PERSIST_UPDATE = "INTENT_MEMORY_PERSIST_UPDATE"
    LOAD_CORPUS = "INTENT_LOAD_CORPUS"
    ONBOARDING_IMPORT_REPAIR = "INTENT_ONBOARDING_IMPORT_REPAIR"
    RESUME_DRAFTING = "INTENT_RESUME_DRAFTING"
    JD_ANALYSIS = "INTENT_JD_ANALYSIS"
    MEMORY_STATUS = "INTENT_MEMORY_STATUS"
    INITIALIZATION_OR_SETUP = "INTENT_INITIALIZATION_OR_SETUP"


@gpt_core
@dataclass(frozen=True)
class RuntimeState:
    """
    Immutable per-turn runtime snapshot used by atom predicates.

    Semantics:
    - corpus_exists=True: canonical corpus exists in the GitHub repo.
    - corpus_loaded=True: corpus has been pulled and loaded into local runtime state.
    """
    repo_exists: bool = False
    runtime_initialized: bool = False
    corpus_exists: bool = False
    corpus_loaded: bool = False
    corpus_valid: bool = False
    onboarding_complete: bool = False
    approved_markdown_ready: bool = False
    last_jd_analysis_present: bool = False
    last_operation_failed: bool = False
    status_changed_since_last_emit: bool = False
    user_requested_memory_status: bool = False
    technical_detail_requested: bool = False
    repo_create_attempted_this_turn: bool = False

    @classmethod
    def from_sources(
        cls,
        status: Optional[Dict[str, Any]] = None,
        turn_state: Optional[Dict[str, Any]] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> "RuntimeState":
        """Build runtime booleans from status/turn-state payloads with explicit False defaults."""
        status = status or {}
        turn_state = turn_state or {}
        overrides = overrides or {}

        def _bool(name: str, *sources: Dict[str, Any]) -> bool:
            """Read a boolean field from overrides, turn_state, then status."""
            for source in sources:
                if name in source:
                    return bool(source.get(name))
            return False

        return cls(
            repo_exists=_bool("repo_exists", overrides, turn_state, status),
            runtime_initialized=_bool("runtime_initialized", overrides, turn_state, status),
            corpus_exists=_bool("corpus_exists", overrides, turn_state, status),
            corpus_loaded=_bool("corpus_loaded", overrides, turn_state, status),
            corpus_valid=_bool("corpus_valid", overrides, turn_state, status),
            onboarding_complete=_bool("onboarding_complete", overrides, turn_state, status),
            approved_markdown_ready=_bool("approved_markdown_ready", overrides, turn_state, status),
            last_jd_analysis_present=_bool("last_jd_analysis_present", overrides, turn_state, status),
            last_operation_failed=_bool("last_operation_failed", overrides, turn_state, status),
            status_changed_since_last_emit=_bool(
                "status_changed_since_last_emit", overrides, turn_state, status
            ),
            user_requested_memory_status=_bool(
                "user_requested_memory_status", overrides, turn_state, status
            ),
            technical_detail_requested=_bool(
                "technical_detail_requested", overrides, turn_state, status
            ),
            repo_create_attempted_this_turn=_bool(
                "repo_create_attempted_this_turn", overrides, turn_state, status
            ),
        )


@gpt_core
@dataclass(frozen=True)
class ContextAtom:
    """Router-ready atom representation derived from AtomSpec."""
    id: str
    title: str
    content: str
    intents: FrozenSet[Intent]
    priority: int
    predicate: Callable[[RuntimeState], bool]
    restrictive: bool
    tags: FrozenSet[str]
    source_ref: str


@gpt_core
@dataclass(frozen=True)
class ContextPack:
    """Deterministic output payload returned by build_context()."""
    intent: Intent
    atoms: List[ContextAtom]
    rendered_context: str
    rerouted_to: List[Intent]
    required_routes: List[Intent]
    block_current_intent: bool
    block_reason: Optional[str]
    next_step_hint: Optional[str]
    diagnostics: Dict[str, Any] = field(default_factory=dict)


_ALL_INTENT_VALUES = {intent.value: intent for intent in Intent}


def _convert_atom(spec: AtomSpec) -> ContextAtom:
    """Convert an AtomSpec registry entry into a ContextAtom."""
    intents: List[Intent] = []
    for intent_id in spec.intents:
        intent = _ALL_INTENT_VALUES.get(intent_id)
        if intent is None:
            raise ValueError(f"Unknown intent id in atom registry: {intent_id}")
        intents.append(intent)

    def _predicate(state: RuntimeState, fn: Callable[[Any], bool] = spec.predicate) -> bool:
        """Wrap spec predicates to always return strict bool values."""
        return bool(fn(state))

    return ContextAtom(
        id=spec.id,
        title=spec.title,
        content=spec.content,
        intents=frozenset(intents),
        priority=spec.priority,
        predicate=_predicate,
        restrictive=spec.restrictive,
        tags=frozenset(spec.tags),
        source_ref=spec.source_ref,
    )


_ATOM_REGISTRY: Tuple[ContextAtom, ...] = tuple(_convert_atom(spec) for spec in get_all_atoms())
_ATOM_BY_ID: Dict[str, ContextAtom] = {atom.id: atom for atom in _ATOM_REGISTRY}
_ATOM_INDEXES = get_atom_indexes()
_ATOM_ORDER: Dict[str, int] = {atom.id: idx for idx, atom in enumerate(_ATOM_REGISTRY)}


def _priority_level(priority: int) -> int:
    """Normalize atom priority to configured 1..10 level buckets."""
    return max(1, min(10, int(priority)))


def _atom_sort_key(atom: ContextAtom) -> Tuple[int, int, int, str]:
    """Sort restrictive atoms first, then priority level, then registry order."""
    return (
        0 if atom.restrictive else 1,
        _priority_level(atom.priority),
        _ATOM_ORDER.get(atom.id, 10**9),
        atom.id,
    )


def _extract_conflict_keys(atom: ContextAtom) -> List[str]:
    """Extract conflict groups from tags formatted as conflict:<key>."""
    keys: List[str] = []
    for tag in atom.tags:
        if tag.startswith("conflict:"):
            keys.append(tag.split(":", 1)[1])
    return keys


def _resolve_conflicts(atoms: Sequence[ContextAtom]) -> Tuple[List[ContextAtom], List[str]]:
    """Keep one winner per conflict group and record dropped atom ids."""
    grouped: Dict[str, List[ContextAtom]] = {}
    for atom in atoms:
        for key in _extract_conflict_keys(atom):
            grouped.setdefault(key, []).append(atom)

    drop_ids: List[str] = []
    keep_ids = {atom.id for atom in atoms}
    for key, group in grouped.items():
        if len(group) < 2:
            continue
        winner = sorted(group, key=_atom_sort_key)[0]
        for atom in group:
            if atom.id == winner.id:
                continue
            if atom.id in keep_ids:
                keep_ids.remove(atom.id)
                drop_ids.append(atom.id)

    filtered = [atom for atom in atoms if atom.id in keep_ids]
    return filtered, sorted(set(drop_ids))


def _render_atom(atom: ContextAtom) -> str:
    """Render one atom into the model-facing title + content block."""
    return f"{atom.title}\n{atom.content}"


def _estimate_tokens(text: str) -> int:
    """Cheap character-based token estimate for diagnostics only."""
    return max(1, len(text) // 4) if text else 0


def _dedupe_intents(route_chain: Iterable[Intent], current_intent: Intent) -> List[Intent]:
    """Remove duplicate/recursive routes while preserving route order."""
    deduped: List[Intent] = []
    seen = set()
    for route in route_chain:
        if route == current_intent:
            continue
        if route in seen:
            continue
        seen.add(route)
        deduped.append(route)
    return deduped


def _memory_preflight_routes(state: RuntimeState) -> List[Intent]:
    """Build required memory preflight route chain from runtime state."""
    routes: List[Intent] = []
    if not state.runtime_initialized or not state.repo_exists:
        routes.append(Intent.INITIALIZATION_OR_SETUP)
    if not state.corpus_loaded:
        if state.corpus_exists:
            routes.append(Intent.LOAD_CORPUS)
        else:
            routes.append(Intent.ONBOARDING_IMPORT_REPAIR)
        return routes
    if (not state.corpus_exists) or (not state.corpus_valid):
        routes.append(Intent.ONBOARDING_IMPORT_REPAIR)
    return routes


def _derive_required_routes(intent: Intent, state: RuntimeState) -> Tuple[List[Intent], Optional[str], Optional[str]]:
    """Compute intent preconditions, block reason, and next-step hint."""
    required: List[Intent] = []
    reason: Optional[str] = None

    if intent == Intent.JD_ANALYSIS:
        if not (state.corpus_loaded and state.corpus_exists and state.corpus_valid):
            required.extend(_memory_preflight_routes(state))
            reason = "JD analysis requires loaded, valid corpus evidence."

    elif intent == Intent.RESUME_DRAFTING:
        if not (state.corpus_loaded and state.corpus_exists and state.corpus_valid):
            required.extend(_memory_preflight_routes(state))
            reason = "Resume drafting requires loaded, valid corpus evidence."
        if not state.last_jd_analysis_present:
            required.append(Intent.JD_ANALYSIS)
            if reason is None:
                reason = "Resume drafting requires JD analysis output first."

    elif intent == Intent.PDF_EXPORT:
        if not state.approved_markdown_ready:
            required.append(Intent.RESUME_DRAFTING)
            reason = "PDF export requires user-approved frozen markdown."

    elif intent == Intent.LOAD_CORPUS:
        if (not state.runtime_initialized) or (not state.repo_exists):
            required.append(Intent.INITIALIZATION_OR_SETUP)
            reason = "Corpus load requires initialization/bootstrap first."
        elif not state.corpus_exists:
            required.append(Intent.ONBOARDING_IMPORT_REPAIR)
            reason = "Corpus load requires an existing corpus in GitHub."

    elif intent == Intent.MEMORY_PERSIST_UPDATE:
        if (not state.runtime_initialized) or (not state.repo_exists):
            required.append(Intent.INITIALIZATION_OR_SETUP)
            reason = "Memory persistence requires initialization/bootstrap first."
        if not state.corpus_loaded:
            required.append(Intent.LOAD_CORPUS)
            reason = reason or "Memory persistence requires corpus preflight/pull."
        if state.corpus_loaded and ((not state.corpus_exists) or (not state.corpus_valid)):
            required.append(Intent.ONBOARDING_IMPORT_REPAIR)
            reason = reason or "Memory persistence requires a valid corpus."

    elif intent == Intent.MEMORY_STATUS:
        if (not state.runtime_initialized) or (not state.repo_exists):
            required.append(Intent.INITIALIZATION_OR_SETUP)
            reason = "Memory status requires initialized runtime and repo bootstrap."

    required = _dedupe_intents(required, intent)
    if not required:
        return [], None, None

    if len(required) > 6:
        required = required[:6]

    next_step = (
        f"Route to `{required[0].value}` first, then continue with `{intent.value}`."
        if required
        else None
    )
    return required, reason, next_step


def _render_blocked_context(
    intent: Intent,
    required_routes: Sequence[Intent],
    block_reason: Optional[str],
) -> str:
    """Render precondition-only guidance when the requested intent is blocked."""
    lines = [f"INTENT BLOCKED: {intent.value}"]
    if block_reason:
        lines.append(f"Reason: {block_reason}")
    lines.append(f"Before running `{intent.value}`, execute required routes in order:")
    for idx, route in enumerate(required_routes, start=1):
        lines.append(f"{idx}. {route.value}")
    lines.append(f"After completing routes, rerun `build_context({intent.value}, state)`.")
    return "\n".join(lines)


@gpt_core
def _build_context_pack(intent: Intent, state: RuntimeState) -> ContextPack:
    """Build one ContextPack without applying automatic reroute recursion."""
    if not isinstance(intent, Intent):
        raise TypeError("intent must be an Intent enum value")
    if not isinstance(state, RuntimeState):
        raise TypeError("state must be a RuntimeState instance")

    required_routes, block_reason, next_step_hint = _derive_required_routes(intent, state)
    if required_routes:
        rendered_context = _render_blocked_context(intent, required_routes, block_reason)
        diagnostics: Dict[str, Any] = {
            "selected_atom_ids": [],
            "filtered_ids": {"conflict": [], "budget": []},
            "required_routes": [route.value for route in required_routes],
            "token_estimate": _estimate_tokens(rendered_context),
            "max_atoms": DEFAULT_MAX_ATOMS,
            "max_rendered_chars": DEFAULT_MAX_RENDERED_CHARS,
            "source_model": "atoms_only",
            "registry_size": len(_ATOM_REGISTRY),
            "selected_source_refs": [],
            "blocked_mode": True,
        }
        return ContextPack(
            intent=intent,
            atoms=[],
            rendered_context=rendered_context,
            rerouted_to=[],
            required_routes=required_routes,
            block_current_intent=True,
            block_reason=block_reason,
            next_step_hint=next_step_hint,
            diagnostics=diagnostics,
        )

    intent_ids = list(_ATOM_INDEXES.get("by_intent", {}).get(intent.value, []))
    selected_atoms = []
    for atom_id in intent_ids:
        atom = _ATOM_BY_ID.get(atom_id)
        if atom is None:
            continue
        if atom.predicate(state):
            selected_atoms.append(atom)

    selected_atoms, dropped_conflicts = _resolve_conflicts(selected_atoms)

    selected_atoms = sorted(selected_atoms, key=_atom_sort_key)

    kept_atoms: List[ContextAtom] = []
    dropped_budget: List[str] = []
    rendered_parts: List[str] = []
    rendered_chars = 0

    for atom in selected_atoms:
        part = _render_atom(atom)
        if atom.restrictive:
            kept_atoms.append(atom)
            rendered_parts.append(part)
            rendered_chars += len(part)
            continue

        if len(kept_atoms) >= DEFAULT_MAX_ATOMS:
            dropped_budget.append(atom.id)
            continue

        projected_chars = rendered_chars + len(part)
        if projected_chars > DEFAULT_MAX_RENDERED_CHARS:
            dropped_budget.append(atom.id)
            continue

        kept_atoms.append(atom)
        rendered_parts.append(part)
        rendered_chars = projected_chars

    rendered_context = "\n\n".join(rendered_parts)
    selected_sources = sorted({atom.source_ref for atom in kept_atoms})

    diagnostics: Dict[str, Any] = {
        "selected_atom_ids": [atom.id for atom in kept_atoms],
        "filtered_ids": {
            "conflict": dropped_conflicts,
            "budget": dropped_budget,
        },
        "required_routes": [route.value for route in required_routes],
        "token_estimate": _estimate_tokens(rendered_context),
        "max_atoms": DEFAULT_MAX_ATOMS,
        "max_rendered_chars": DEFAULT_MAX_RENDERED_CHARS,
        "source_model": "atoms_only",
        "registry_size": len(_ATOM_REGISTRY),
        "selected_source_refs": selected_sources,
        "blocked_mode": False,
    }

    return ContextPack(
        intent=intent,
        atoms=kept_atoms,
        rendered_context=rendered_context,
        rerouted_to=[],
        required_routes=required_routes,
        block_current_intent=bool(required_routes),
        block_reason=block_reason,
        next_step_hint=next_step_hint,
        diagnostics=diagnostics,
    )


def _compact_context_output(pack: ContextPack) -> str:
    """Return compact model-facing output for non-verbose mode."""
    lines: List[str] = []
    if pack.block_current_intent:
        lines.append("BLOCKED: true")
        if pack.block_reason:
            lines.append(f"BLOCK REASON: {pack.block_reason}")
    if pack.rerouted_to:
        rerouted = ", ".join(intent.value for intent in pack.rerouted_to)
        lines.append(f"REROUTED TO: {rerouted}")
    lines.append("RENDERED CONTEXT:")
    lines.append(pack.rendered_context)
    return "\n".join(lines)


@gpt_core
def build_context(
    intent: Intent,
    state: RuntimeState,
    verbose: bool = False,
    max_reroutes: int = 6,
) -> Union[ContextPack, str]:
    """Build context and auto-reroute to the next actionable intent when blocked."""
    if not isinstance(intent, Intent):
        raise TypeError("intent must be an Intent enum value")
    if not isinstance(state, RuntimeState):
        raise TypeError("state must be a RuntimeState instance")
    if not isinstance(max_reroutes, int) or max_reroutes < 0:
        raise ValueError("max_reroutes must be an integer >= 0")

    current_intent = intent
    reroute_chain: List[Intent] = []
    visited: set[Intent] = set()
    final_pack: Optional[ContextPack] = None

    for _ in range(max_reroutes + 1):
        pack = _build_context_pack(current_intent, state)
        if not pack.block_current_intent or not pack.required_routes:
            final_pack = pack
            break

        next_intent = pack.required_routes[0]
        if next_intent in visited or next_intent == current_intent:
            final_pack = pack
            break

        visited.add(current_intent)
        reroute_chain.append(next_intent)
        current_intent = next_intent

    if final_pack is None:
        final_pack = _build_context_pack(current_intent, state)

    final_pack = ContextPack(
        intent=final_pack.intent,
        atoms=final_pack.atoms,
        rendered_context=final_pack.rendered_context,
        rerouted_to=reroute_chain,
        required_routes=final_pack.required_routes,
        block_current_intent=final_pack.block_current_intent,
        block_reason=final_pack.block_reason,
        next_step_hint=final_pack.next_step_hint,
        diagnostics=final_pack.diagnostics,
    )

    if verbose:
        return final_pack
    return _compact_context_output(final_pack)
