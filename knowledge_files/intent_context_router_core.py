"""Deterministic intent router and context pack builder."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Sequence, Tuple

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
    obj.__gpt_layer__ = "core"
    obj.__gpt_core__ = True
    return obj


@gpt_core
class Intent(str, Enum):
    CONVERSATION_ONLY = "INTENT_CONVERSATION_ONLY"
    FAILURE_RECOVERY = "INTENT_FAILURE_RECOVERY"
    PDF_EXPORT = "INTENT_PDF_EXPORT"
    MEMORY_PERSIST_UPDATE = "INTENT_MEMORY_PERSIST_UPDATE"
    ONBOARDING_IMPORT_REPAIR = "INTENT_ONBOARDING_IMPORT_REPAIR"
    RESUME_DRAFTING = "INTENT_RESUME_DRAFTING"
    JD_ANALYSIS = "INTENT_JD_ANALYSIS"
    MEMORY_STATUS = "INTENT_MEMORY_STATUS"
    INITIALIZATION_OR_SETUP = "INTENT_INITIALIZATION_OR_SETUP"

_LEGACY_REFERENCE_PACKS: Dict[Intent, Tuple[str, ...]] = {
    Intent.CONVERSATION_ONLY: ("UATGuardrails.md",),
    Intent.FAILURE_RECOVERY: (
        "UATGuardrails.md",
        "MemoryPersistenceGuidelines.md",
        "MemoryStateModel.md",
    ),
    Intent.PDF_EXPORT: (
        "PDFExportGuidelines.md",
        "resume_renderer.py",
        "resume_theme.py",
    ),
    Intent.MEMORY_PERSIST_UPDATE: (
        "MemoryPersistenceGuidelines.md",
        "memory_validation_surface.py",
        "career_corpus_store_surface.py",
        "career_corpus_sync_surface.py",
        "career_corpus.schema.json",
        "github_action_schema.json",
    ),
    Intent.ONBOARDING_IMPORT_REPAIR: (
        "OnboardingGuidelines.md",
        "UATGuardrails.md",
        "MemoryPersistenceGuidelines.md",
    ),
    Intent.RESUME_DRAFTING: (
        "ResumeBuildingGuidelines.md",
        "ResumeTemplate.md",
        "MemoryPersistenceGuidelines.md",
    ),
    Intent.JD_ANALYSIS: ("JDAnalysisGuidelines.md", "UATGuardrails.md"),
    Intent.MEMORY_STATUS: ("MemoryStateModel.md", "MemoryPersistenceGuidelines.md"),
    Intent.INITIALIZATION_OR_SETUP: (
        "InitializationGuidelines.md",
        "MemoryPersistenceGuidelines.md",
    ),
}


@gpt_core
@dataclass(frozen=True)
class RuntimeState:
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
    intent: Intent
    atoms: List[ContextAtom]
    rendered_context: str
    required_routes: List[Intent]
    block_current_intent: bool
    block_reason: Optional[str]
    next_step_hint: Optional[str]
    diagnostics: Dict[str, Any] = field(default_factory=dict)


_ALL_INTENT_VALUES = {intent.value: intent for intent in Intent}


def _convert_atom(spec: AtomSpec) -> ContextAtom:
    intents: List[Intent] = []
    for intent_id in spec.intents:
        intent = _ALL_INTENT_VALUES.get(intent_id)
        if intent is None:
            raise ValueError(f"Unknown intent id in atom registry: {intent_id}")
        intents.append(intent)

    def _predicate(state: RuntimeState, fn: Callable[[Any], bool] = spec.predicate) -> bool:
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


def _extract_conflict_keys(atom: ContextAtom) -> List[str]:
    keys: List[str] = []
    for tag in atom.tags:
        if tag.startswith("conflict:"):
            keys.append(tag.split(":", 1)[1])
    return keys


def _resolve_conflicts(atoms: Sequence[ContextAtom]) -> Tuple[List[ContextAtom], List[str]]:
    grouped: Dict[str, List[ContextAtom]] = {}
    for atom in atoms:
        for key in _extract_conflict_keys(atom):
            grouped.setdefault(key, []).append(atom)

    drop_ids: List[str] = []
    keep_ids = {atom.id for atom in atoms}
    for key, group in grouped.items():
        if len(group) < 2:
            continue
        winner = sorted(group, key=lambda atom: (0 if atom.restrictive else 1, atom.priority, atom.id))[0]
        for atom in group:
            if atom.id == winner.id:
                continue
            if atom.id in keep_ids:
                keep_ids.remove(atom.id)
                drop_ids.append(atom.id)

    filtered = [atom for atom in atoms if atom.id in keep_ids]
    return filtered, sorted(set(drop_ids))


def _ordered_unique(atom_ids: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for atom_id in atom_ids:
        if atom_id in seen:
            continue
        seen.add(atom_id)
        ordered.append(atom_id)
    return ordered


def _render_atom(atom: ContextAtom) -> str:
    return f"[{atom.id}] {atom.title}\n{atom.content}"


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4) if text else 0


def _dedupe_intents(route_chain: Iterable[Intent], current_intent: Intent) -> List[Intent]:
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
    routes: List[Intent] = []
    if not state.runtime_initialized or not state.repo_exists:
        routes.append(Intent.INITIALIZATION_OR_SETUP)
    if not state.corpus_loaded:
        routes.append(Intent.MEMORY_STATUS)
    if (not state.corpus_exists) or (not state.corpus_valid):
        routes.append(Intent.ONBOARDING_IMPORT_REPAIR)
    return routes


def _derive_required_routes(intent: Intent, state: RuntimeState) -> Tuple[List[Intent], Optional[str], Optional[str]]:
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

    elif intent == Intent.MEMORY_PERSIST_UPDATE:
        if (not state.runtime_initialized) or (not state.repo_exists):
            required.append(Intent.INITIALIZATION_OR_SETUP)
            reason = "Memory persistence requires initialization/bootstrap first."
        if not state.corpus_loaded:
            required.append(Intent.MEMORY_STATUS)
            reason = reason or "Memory persistence requires corpus preflight/pull."
        if (not state.corpus_exists) or (not state.corpus_valid):
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


@gpt_core
def build_context(intent: Intent, state: RuntimeState) -> ContextPack:
    """Build deterministic context snippets and precondition routes for one intent."""
    if not isinstance(intent, Intent):
        raise TypeError("intent must be an Intent enum value")
    if not isinstance(state, RuntimeState):
        raise TypeError("state must be a RuntimeState instance")

    global_ids = list(_ATOM_INDEXES.get("by_tag", {}).get("global", ()))
    intent_ids = list(_ATOM_INDEXES.get("by_intent", {}).get(intent.value, ()))
    state_ids = [atom.id for atom in _ATOM_REGISTRY if atom.predicate(state)]

    ordered_ids = _ordered_unique([*global_ids, *intent_ids, *state_ids])
    selected_atoms = [_ATOM_BY_ID[atom_id] for atom_id in ordered_ids if atom_id in _ATOM_BY_ID]

    selected_atoms, dropped_conflicts = _resolve_conflicts(selected_atoms)

    selected_atoms = sorted(
        selected_atoms,
        key=lambda atom: (0 if atom.restrictive else 1, atom.priority, atom.id),
    )

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
    required_routes, block_reason, next_step_hint = _derive_required_routes(intent, state)
    legacy_pack = _LEGACY_REFERENCE_PACKS.get(intent, ())
    selected_sources = sorted({atom.source_ref for atom in kept_atoms})
    legacy_overlap = sorted(source for source in selected_sources if source in set(legacy_pack))
    legacy_only = sorted(source for source in legacy_pack if source not in set(selected_sources))
    atom_only_sources = sorted(source for source in selected_sources if source not in set(legacy_pack))

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
        "shadow": {
            "legacy_reference_pack": list(legacy_pack),
            "selected_source_refs": selected_sources,
            "overlap": legacy_overlap,
            "legacy_only": legacy_only,
            "atom_only_sources": atom_only_sources,
        },
    }

    return ContextPack(
        intent=intent,
        atoms=kept_atoms,
        rendered_context=rendered_context,
        required_routes=required_routes,
        block_current_intent=bool(required_routes),
        block_reason=block_reason,
        next_step_hint=next_step_hint,
        diagnostics=diagnostics,
    )
