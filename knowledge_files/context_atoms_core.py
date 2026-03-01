"""Atom registry and indexes for intent context routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, FrozenSet, List


INTENT_CONVERSATION_ONLY = "INTENT_CONVERSATION_ONLY"
INTENT_FAILURE_RECOVERY = "INTENT_FAILURE_RECOVERY"
INTENT_PDF_EXPORT = "INTENT_PDF_EXPORT"
INTENT_MEMORY_PERSIST_UPDATE = "INTENT_MEMORY_PERSIST_UPDATE"
INTENT_ONBOARDING_IMPORT_REPAIR = "INTENT_ONBOARDING_IMPORT_REPAIR"
INTENT_RESUME_DRAFTING = "INTENT_RESUME_DRAFTING"
INTENT_JD_ANALYSIS = "INTENT_JD_ANALYSIS"
INTENT_MEMORY_STATUS = "INTENT_MEMORY_STATUS"
INTENT_INITIALIZATION_OR_SETUP = "INTENT_INITIALIZATION_OR_SETUP"

ALL_INTENT_IDS: FrozenSet[str] = frozenset(
    {
        INTENT_CONVERSATION_ONLY,
        INTENT_FAILURE_RECOVERY,
        INTENT_PDF_EXPORT,
        INTENT_MEMORY_PERSIST_UPDATE,
        INTENT_ONBOARDING_IMPORT_REPAIR,
        INTENT_RESUME_DRAFTING,
        INTENT_JD_ANALYSIS,
        INTENT_MEMORY_STATUS,
        INTENT_INITIALIZATION_OR_SETUP,
    }
)

DEFAULT_MAX_ATOMS = 14
DEFAULT_MAX_RENDERED_CHARS = 12_000


StatePredicate = Callable[[Any], bool]


@dataclass(frozen=True)
class AtomSpec:
    """Atom Spec."""
    id: str
    title: str
    content: str
    intents: FrozenSet[str]
    priority: int  # 1..10 level bucket (lower = earlier)
    predicate: StatePredicate
    restrictive: bool
    tags: FrozenSet[str]
    source_ref: str


def _flag(state: Any, field_name: str) -> bool:
    """Internal helper to flag."""
    return bool(getattr(state, field_name, False))


def _always(_: Any) -> bool:
    """Internal helper to always."""
    return True


def _needs_initialization(state: Any) -> bool:
    """Internal helper to needs initialization."""
    return (not _flag(state, "runtime_initialized")) or (not _flag(state, "repo_exists"))


def _needs_corpus_loaded(state: Any) -> bool:
    """Internal helper to needs corpus loaded."""
    return not _flag(state, "corpus_loaded")


def _needs_corpus_repair(state: Any) -> bool:
    """Internal helper to needs corpus repair."""
    return (not _flag(state, "corpus_exists")) or (not _flag(state, "corpus_valid"))


def _needs_jd_first(state: Any) -> bool:
    """Internal helper to needs jd first."""
    return not _flag(state, "last_jd_analysis_present")


def _needs_approved_markdown(state: Any) -> bool:
    """Internal helper to needs approved markdown."""
    return not _flag(state, "approved_markdown_ready")


def _memory_status_requested(state: Any) -> bool:
    """Internal helper to memory status requested."""
    return (
        _flag(state, "user_requested_memory_status")
        or _flag(state, "status_changed_since_last_emit")
        or _flag(state, "last_operation_failed")
    )


def _technical_detail_requested(state: Any) -> bool:
    """Internal helper to technical detail requested."""
    return _flag(state, "technical_detail_requested")


ATOM_REGISTRY: List[AtomSpec] = [
    AtomSpec(
        id="conversation.stop_after_reply",
        title="Conversation-Only Behavior",
        content="""\
For greeting/thanks/chitchat with no actionable task: respond briefly and stop workflow
execution.
""",
        intents=frozenset({INTENT_CONVERSATION_ONLY}),
        priority=1,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"conversation"}),
        source_ref="UATGuardrails.md",
    ),
    AtomSpec(
        id="failure.retry_once_then_manual",
        title="Deterministic Failure Recovery",
        content="""\
Use one deterministic retry for retryable memory/API failures after correcting preflight
conditions. If retry fails, stop and return explicit manual recovery steps in the same turn.
""",
        intents=frozenset({INTENT_FAILURE_RECOVERY}),
        priority=2,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"failure", "guardrail"}),
        source_ref="UATGuardrails.md",
    ),
    AtomSpec(
        id="failure.technical_detail_toggle",
        title="Failure Detail Level",
        content="""\
Default failure wording should be non-technical. Include branch/commit/hash diagnostics
only when technical detail is explicitly requested.
""",
        intents=frozenset({INTENT_FAILURE_RECOVERY}),
        priority=2,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"failure"}),
        source_ref="MemoryPersistenceGuidelines.md",
    ),
    AtomSpec(
        id="pdf.export_preconditions",
        title="PDF Export Preconditions",
        content="""\
Export only from user-approved frozen markdown. Never rewrite resume content during
export. If markdown is not approved, block export and route back to drafting/review.
""",
        intents=frozenset({INTENT_PDF_EXPORT}),
        priority=3,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"pdf", "guardrail"}),
        source_ref="PDFExportGuidelines.md",
    ),
    AtomSpec(
        id="pdf.pipeline",
        title="PDF Renderer Pipeline",
        content="""\
Use ResumeRenderer and ResumeTheme for export. Enforce page limits before render.
Default max pages is 1; allow 2 only when explicitly approved for senior scope.
""",
        intents=frozenset({INTENT_PDF_EXPORT}),
        priority=3,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"pdf"}),
        source_ref="PDFExportGuidelines.md",
    ),
    AtomSpec(
        id="persist.validate_then_push_then_verify",
        title="Persistence Execution Contract",
        content="""\
Persistence order is fixed: validate -> push -> verify. Writes must be section-approved
when scoped updates are requested. Only report success after verification passes.
""",
        intents=frozenset({INTENT_MEMORY_PERSIST_UPDATE}),
        priority=4,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"memory", "persist"}),
        source_ref="MemoryPersistenceGuidelines.md",
    ),
    AtomSpec(
        id="persist.onboarding_single_final_push",
        title="Onboarding Single Final Push",
        content="""\
During onboarding, stage section approvals first and execute one final push after the
full required approval set is collected. Do not push section-by-section.
""",
        intents=frozenset({INTENT_MEMORY_PERSIST_UPDATE, INTENT_ONBOARDING_IMPORT_REPAIR}),
        priority=4,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"memory", "persist", "onboarding"}),
        source_ref="OnboardingGuidelines.md",
    ),
    AtomSpec(
        id="persist.status_visibility",
        title="Memory Status Visibility",
        content="""\
Show MEMORY STATUS only on explicit request, state change, or failure.
Required status plain text block
MEMORY STATUS
- repo_exists: <true|false>
- corpus_exists: <true|false>
- onboarding_complete: <true|false>
- last_written: <friendly timestamp | Never>

Optional status fields (show only when relevant)
validated: include when a validation gate ran in this flow.
persisted: include when a write attempt occurred this flow.
fallback_used: include only when fallback path was used.
method: include for persistence/status-debug contexts.
retry_count: include when retries were attempted.
verification: include when verification ran or failed.
""",
        intents=frozenset({INTENT_MEMORY_PERSIST_UPDATE, INTENT_MEMORY_STATUS, INTENT_FAILURE_RECOVERY}),
        priority=4,
        predicate=_memory_status_requested,
        restrictive=False,
        tags=frozenset({"memory_status", "memory", "conflict:status_output"}),
        source_ref="MemoryStateModel.md",
    ),
    AtomSpec(
        id="onboarding.phase_order",
        title="Onboarding Phase Order",
        content="""\
Run onboarding in fixed order:
Phase A: onboarding introduction (once per session)
Phase B: GitHub account/authentication gate + memory repo bootstrap
Phase C: intake mode selection (LinkedIn PDF/CV upload OR manual setup)
Phase D: section-by-section confirmation gate (approval before staging)
Phase E: final validation + single push + onboarding completion metadata update
""",
        intents=frozenset({INTENT_ONBOARDING_IMPORT_REPAIR}),
        priority=5,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"onboarding"}),
        source_ref="OnboardingGuidelines.md",
    ),
    AtomSpec(
        id="onboarding.github_gate",
        title="Onboarding GitHub Hard Gate",
        content="""\
If user has no GitHub account/auth readiness, provide concise setup steps and pause
onboarding. Do not continue intake until account/auth is ready and memory repo bootstrap
succeeds.
""",
        intents=frozenset({INTENT_ONBOARDING_IMPORT_REPAIR}),
        priority=5,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"onboarding", "initialization"}),
        source_ref="OnboardingGuidelines.md",
    ),
    AtomSpec(
        id="onboarding.section_confirmation_gate",
        title="Section Confirmation Gate",
        content="""\
Preview one section at a time in readable markdown/text, collect explicit approval, and
stage only approved target sections. Keep unapproved sections out of push scope.
""",
        intents=frozenset({INTENT_ONBOARDING_IMPORT_REPAIR}),
        priority=5,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"onboarding", "memory"}),
        source_ref="OnboardingGuidelines.md",
    ),
    AtomSpec(
        id="resume.template_required",
        title="Resume Template Contract",
        content="""\
Build resume output against ResumeTemplate.md structure. Do not introduce unsupported
section structures unless user explicitly requests changes.
""",
        intents=frozenset({INTENT_RESUME_DRAFTING}),
        priority=6,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"resume"}),
        source_ref="ResumeBuildingGuidelines.md",
    ),
    AtomSpec(
        id="resume.evidence_and_no_fluff",
        title="Resume Evidence and No-Fluff Rule",
        content="""\
Every resume claim must be supported by corpus or current chat evidence. Do not add
fluff: if content does not make a case for a JD requirement, omit it.
""",
        intents=frozenset({INTENT_RESUME_DRAFTING}),
        priority=6,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"resume", "guardrail"}),
        source_ref="ResumeBuildingGuidelines.md",
    ),
    AtomSpec(
        id="resume.ats_alignment",
        title="Resume ATS Alignment",
        content="""\
Before finalizing draft, confirm Tier 1 requirement coverage in title line, summary,
core competencies, and first role bullets with linked evidence.
""",
        intents=frozenset({INTENT_RESUME_DRAFTING}),
        priority=6,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"resume"}),
        source_ref="ResumeBuildingGuidelines.md",
    ),
    AtomSpec(
        id="jd.preflight_required",
        title="JD Analysis Memory Preflight",
        content="""\
JD analysis requires corpus-backed evidence. If corpus is not loaded/valid, route
through memory preflight before requirement scoring or candidate alignment.
""",
        intents=frozenset({INTENT_JD_ANALYSIS}),
        priority=7,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"jd", "memory"}),
        source_ref="JDAnalysisGuidelines.md",
    ),
    AtomSpec(
        id="jd.markdown_output_contract",
        title="JD Markdown Output Contract",
        content="""\
Return JD analysis in markdown with binary gates (only those present in JD), Tier 1 and
Tier 2 keywords, core skill clusters, translation map, recruiter search simulation, and
concise candidate alignment.
""",
        intents=frozenset({INTENT_JD_ANALYSIS}),
        priority=7,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"jd"}),
        source_ref="JDAnalysisGuidelines.md",
    ),
    AtomSpec(
        id="jd.status_markers",
        title="JD Evidence Markers",
        content="""\
Use consistent status markers throughout JD analysis: green for solid evidence, yellow
for partial alignment, red for clear gaps. Omit binary gates not specified in the JD.
""",
        intents=frozenset({INTENT_JD_ANALYSIS}),
        priority=7,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"jd"}),
        source_ref="JDAnalysisGuidelines.md",
    ),
    AtomSpec(
        id="jd.resume_handoff_prompt",
        title="JD to Resume Handoff",
        content="""\
At the end of JD analysis, ask whether to draft a tailored resume now. If user says yes,
route to INTENT_RESUME_DRAFTING.
""",
        intents=frozenset({INTENT_JD_ANALYSIS}),
        priority=7,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"jd", "resume"}),
        source_ref="JDAnalysisGuidelines.md",
    ),
    AtomSpec(
        id="memory_status.state_block",
        title="Memory Status Block Format",
        content="""\
Use compact block exactly as baseline: MEMORY STATUS; - repo_exists; - corpus_exists; -
onboarding_complete; - last_written (friendly timestamp converted to local time or Never). Do not include
unrelated variables by default.
""",
        intents=frozenset({INTENT_MEMORY_STATUS}),
        priority=8,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"memory_status", "memory", "conflict:status_output"}),
        source_ref="MemoryStateModel.md",
    ),
    AtomSpec(
        id="memory_status.optional_fields",
        title="Memory Status Optional Fields",
        content="""\
Optional fields are conditional only: validated (validation ran), persisted (write
attempted), fallback_used (fallback path), method (debug contexts), retry_count (retries
occurred), verification (verification ran or failed).
""",
        intents=frozenset({INTENT_MEMORY_STATUS}),
        priority=8,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"memory_status"}),
        source_ref="MemoryStateModel.md",
    ),
    AtomSpec(
        id="init.deterministic_sequence",
        title="Initialization Deterministic Sequence",
        content="""\
Initialization sequence: add /mnt/data to sys.path -> resolve owner -> getMemoryRepo ->
optional createMemoryRepo (once per turn) -> confirm getMemoryRepo -> initialize
store/sync -> emit initialization status.
""",
        intents=frozenset({INTENT_INITIALIZATION_OR_SETUP}),
        priority=9,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"initialization"}),
        source_ref="InitializationGuidelines.md",
    ),
    AtomSpec(
        id="init.github_account_gate",
        title="Initialization GitHub Account Gate",
        content="""\
If GitHub account/auth is not ready, stop setup and provide concise account setup/auth
steps. Do not continue bootstrap or writes until readiness is confirmed.
""",
        intents=frozenset({INTENT_INITIALIZATION_OR_SETUP}),
        priority=9,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"initialization"}),
        source_ref="InitializationGuidelines.md",
    ),
    AtomSpec(
        id="state.require_initialization",
        title="State Gate: Initialization Required",
        content="""\
Runtime is not initialized or repo does not exist. Block current memory-dependent intent
and route to INTENT_INITIALIZATION_OR_SETUP first.
""",
        intents=frozenset(
            {
                INTENT_MEMORY_PERSIST_UPDATE,
                INTENT_MEMORY_STATUS,
                INTENT_JD_ANALYSIS,
                INTENT_RESUME_DRAFTING,
                INTENT_PDF_EXPORT,
            }
        ),
        priority=10,
        predicate=_needs_initialization,
        restrictive=True,
        tags=frozenset({"state", "precondition", "memory"}),
        source_ref="instructions.txt",
    ),
    AtomSpec(
        id="state.require_corpus_preflight",
        title="State Gate: Corpus Preflight Required",
        content="""\
Corpus is not loaded. Route to INTENT_MEMORY_STATUS to trigger pull/reassembly before
continuing this intent.
""",
        intents=frozenset({INTENT_JD_ANALYSIS, INTENT_RESUME_DRAFTING, INTENT_MEMORY_PERSIST_UPDATE}),
        priority=10,
        predicate=_needs_corpus_loaded,
        restrictive=True,
        tags=frozenset({"state", "precondition", "memory"}),
        source_ref="JDAnalysisGuidelines.md",
    ),
    AtomSpec(
        id="state.require_onboarding_repair",
        title="State Gate: Onboarding/Repair Required",
        content="""\
Corpus is missing or invalid after preflight. Route to INTENT_ONBOARDING_IMPORT_REPAIR
before proceeding.
""",
        intents=frozenset({INTENT_JD_ANALYSIS, INTENT_RESUME_DRAFTING, INTENT_MEMORY_PERSIST_UPDATE}),
        priority=10,
        predicate=_needs_corpus_repair,
        restrictive=True,
        tags=frozenset({"state", "precondition", "onboarding", "memory"}),
        source_ref="MemoryPersistenceGuidelines.md",
    ),
    AtomSpec(
        id="state.require_jd_before_resume",
        title="State Gate: JD Analysis Required",
        content="""\
Resume drafting requires completed JD analysis first. Route to INTENT_JD_ANALYSIS before
drafting.
""",
        intents=frozenset({INTENT_RESUME_DRAFTING}),
        priority=10,
        predicate=_needs_jd_first,
        restrictive=True,
        tags=frozenset({"state", "precondition", "resume", "jd"}),
        source_ref="instructions.txt",
    ),
    AtomSpec(
        id="state.require_approved_markdown",
        title="State Gate: Approved Markdown Required",
        content="""\
PDF export is blocked until approved_markdown_ready=true. Route to
INTENT_RESUME_DRAFTING review/finalization first.
""",
        intents=frozenset({INTENT_PDF_EXPORT}),
        priority=10,
        predicate=_needs_approved_markdown,
        restrictive=True,
        tags=frozenset({"state", "precondition", "pdf", "resume"}),
        source_ref="PDFExportGuidelines.md",
    ),
    AtomSpec(
        id="state.memory_status_only_when_relevant",
        title="State Rule: Status Emission Trigger",
        content="""\
Emit MEMORY STATUS only when requested, when status changed, or after a failed
operation. When emitted, keep the clean baseline block (repo_exists, corpus_exists,
onboarding_complete, last_written) and include optional fields only when flow-relevant.
""",
        intents=frozenset({INTENT_MEMORY_STATUS, INTENT_MEMORY_PERSIST_UPDATE, INTENT_FAILURE_RECOVERY}),
        priority=10,
        predicate=_memory_status_requested,
        restrictive=True,
        tags=frozenset({"state", "memory_status", "conflict:status_output"}),
        source_ref="MemoryStateModel.md",
    ),
    AtomSpec(
        id="state.technical_details",
        title="State Rule: Technical Detail Mode",
        content="""\
Technical detail requested. Include diagnostic fields and operation internals where
relevant.
""",
        intents=ALL_INTENT_IDS,
        priority=10,
        predicate=_technical_detail_requested,
        restrictive=False,
        tags=frozenset({"state", "detail_level"}),
        source_ref="instructions.txt",
    ),
]


def get_all_atoms() -> List[AtomSpec]:
    """Get all atoms."""
    return ATOM_REGISTRY


def get_atom_indexes() -> Dict[str, Dict[str, List[str]]]:
    """Get atom indexes."""
    by_intent: Dict[str, List[str]] = {intent_id: [] for intent_id in ALL_INTENT_IDS}
    by_tag: Dict[str, List[str]] = {}
    by_priority: Dict[str, List[str]] = {}

    ordered = sorted(ATOM_REGISTRY, key=lambda atom: (atom.priority, atom.id))
    for atom in ordered:
        for intent_id in atom.intents:
            by_intent.setdefault(intent_id, []).append(atom.id)
        for tag in atom.tags:
            by_tag.setdefault(tag, []).append(atom.id)
        by_priority.setdefault(str(atom.priority), []).append(atom.id)

    return {
        "by_intent": by_intent,
        "by_tag": by_tag,
        "by_priority": by_priority,
    }
