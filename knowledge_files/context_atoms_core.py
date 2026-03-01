"""Atom registry and indexes for intent context routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, FrozenSet, List


INTENT_CONVERSATION_ONLY = "INTENT_CONVERSATION_ONLY"
INTENT_FAILURE_RECOVERY = "INTENT_FAILURE_RECOVERY"
INTENT_PDF_EXPORT = "INTENT_PDF_EXPORT"
INTENT_MEMORY_PERSIST_UPDATE = "INTENT_MEMORY_PERSIST_UPDATE"
INTENT_LOAD_CORPUS = "INTENT_LOAD_CORPUS"
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
        INTENT_LOAD_CORPUS,
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
    # Only evaluate validity after a local load attempt; otherwise validity is unknown.
    if not _flag(state, "corpus_loaded"):
        return False
    return (not _flag(state, "corpus_exists")) or (not _flag(state, "corpus_valid"))


def _loaded_and_needs_corpus_repair(state: Any) -> bool:
    """Internal helper to loaded and needs corpus repair."""
    return _flag(state, "corpus_loaded") and _needs_corpus_repair(state)


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
        intents=frozenset({INTENT_CONVERSATION_ONLY}),
        priority=1,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"conversation"}),
        source_ref="UATGuardrails.md",
        title="Conversation-Only Behavior",
        content="""\
For greeting/thanks/chitchat with no actionable task: respond briefly and stop workflow
execution.
""",
    ),
    AtomSpec(
        id="failure.retry_once_then_manual",
        intents=frozenset({INTENT_FAILURE_RECOVERY}),
        priority=2,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"failure", "guardrail"}),
        source_ref="UATGuardrails.md",
        title="Deterministic Failure Recovery",
        content="""\
Use one deterministic retry for retryable memory/API failures after correcting preflight
conditions. If retry fails, stop and return explicit manual recovery steps in the same turn.
""",
    ),
    AtomSpec(
        id="failure.technical_detail_toggle",
        intents=frozenset({INTENT_FAILURE_RECOVERY}),
        priority=2,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"failure"}),
        source_ref="MemoryPersistenceGuidelines.md",
        title="Failure Detail Level",
        content="""\
Default failure wording should be non-technical. Include branch/commit/hash diagnostics
only when technical detail is explicitly requested.
""",
    ),
    AtomSpec(
        id="pdf.export_preconditions",
        intents=frozenset({INTENT_PDF_EXPORT}),
        priority=3,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"pdf", "guardrail"}),
        source_ref="PDFExportGuidelines.md",
        title="PDF Export Preconditions",
        content="""\
Export only from user-approved frozen markdown. Never rewrite resume content during
export. If markdown is not approved, block export and route back to drafting/review.
""",
    ),
    AtomSpec(
        id="pdf.pipeline",
        intents=frozenset({INTENT_PDF_EXPORT}),
        priority=3,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"pdf"}),
        source_ref="PDFExportGuidelines.md",
        title="PDF Renderer Pipeline",
        content="""\
Rules
- Markdown formatting should adhere to /mnt/data/ResumeTemplate.md.
- Use ResumeRenderer and ResumeTheme for export. 
- Enforce page limits before render.
    - Default max pages is 1; allow 2 only when explicitly approved for senior scope.
    - if the agreed upon markdown is > max pages:
        - Re-Route to INTENT_RESUME_DRAFTING and condense

Output requirements
- Format: A4 PDF.
- File naming scheme: <User Name> Resume - <TargetRole> - <CompanyIfKnown>.pdf
- Attach only the PDF artifact unless the users asks for the markdown.

```Python
from resume_renderer import ResumeRenderer
from resume_theme import ResumeTheme

theme = ResumeTheme()
renderer = ResumeRenderer(theme)
page_count = renderer.exceeds_one_page(markdown_text)

max_pages = 1
# Set max_pages = 2 only when senior scope is explicitly approved.

if page_count > max_pages:
    # Do not export yet; return to editing and shorten content.
    ...
else:
    renderer.render(markdown_text, output_path)
```
""",
    ),
    AtomSpec(
        id="persist.validate_then_push_then_verify",
        intents=frozenset({INTENT_MEMORY_PERSIST_UPDATE}),
        priority=4,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"memory", "persist"}),
        source_ref="MemoryPersistenceGuidelines.md",
        title="Persistence Execution Contract",
        content="""\
Persistence order is fixed: validate -> push -> verify. Writes must be section-approved
when scoped updates are requested. Only report success after verification passes.
""",
    ),
    AtomSpec(
        id="persist.onboarding_single_final_push",
        intents=frozenset({INTENT_MEMORY_PERSIST_UPDATE, INTENT_ONBOARDING_IMPORT_REPAIR}),
        priority=4,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"memory", "persist", "onboarding"}),
        source_ref="OnboardingGuidelines.md",
        title="Onboarding Single Final Push",
        content="""\
During onboarding, stage section approvals first and execute one final push after the
full required approval set is collected. Do not push section-by-section.
""",
    ),
    AtomSpec(
        id="persist.status_visibility",
        intents=frozenset({INTENT_MEMORY_PERSIST_UPDATE, INTENT_MEMORY_STATUS, INTENT_FAILURE_RECOVERY}),
        priority=4,
        predicate=_memory_status_requested,
        restrictive=False,
        tags=frozenset({"memory_status", "memory", "conflict:status_output"}),
        source_ref="MemoryStateModel.md",
        title="Memory Status Visibility",
        content="""\
Show MEMORY STATUS only on explicit request, state change, or failure.
""",
    ),
    AtomSpec(
        id="onboarding.phase_order",
        intents=frozenset({INTENT_ONBOARDING_IMPORT_REPAIR}),
        priority=5,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"onboarding"}),
        source_ref="OnboardingGuidelines.md",
        title="Onboarding Phase Order",
        content="""\
Run onboarding in fixed order:
Phase A: onboarding introduction (once per session)
Phase B: GitHub account/authentication gate + memory repo bootstrap
Phase C: intake mode selection (LinkedIn PDF/CV upload OR manual setup)
Phase D: section-by-section confirmation gate (approval before staging)
Phase E: final validation + single push + onboarding completion metadata update
""",
    ),
    AtomSpec(
        id="onboarding.github_gate",
        intents=frozenset({INTENT_ONBOARDING_IMPORT_REPAIR}),
        priority=5,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"onboarding", "initialization"}),
        source_ref="OnboardingGuidelines.md",
        title="Onboarding GitHub Hard Gate",
        content="""\
If user has no GitHub account/auth readiness, provide concise setup steps and pause
onboarding. Do not continue intake until account/auth is ready and memory repo bootstrap
succeeds.
""",
    ),
    AtomSpec(
        id="onboarding.section_confirmation_gate",
        intents=frozenset({INTENT_ONBOARDING_IMPORT_REPAIR}),
        priority=5,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"onboarding", "memory"}),
        source_ref="OnboardingGuidelines.md",
        title="Section Confirmation Gate",
        content="""\
Preview one section at a time in readable markdown/text, collect explicit approval, and
stage only approved target sections. Keep unapproved sections out of push scope.
""",
    ),
    AtomSpec(
        id="resume.template_contract",
        intents=frozenset({INTENT_RESUME_DRAFTING}),
        priority=6,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"resume"}),
        source_ref="ResumeBuildingGuidelines.md",
        title="Resume Template Contract",
        content="""\
Objective:
- Convert JD Analysis Output + verified corpus evidence into a tailored
resume draft using the canvas tool in the provided markdown template.

Rules (non-negotiable)
- Every claim must be supported by corpus or current chat.
- If a JD requirement is unsupported, do not claim it.
- Prefer recent, high-impact evidence.
- Do not invent employers, titles, dates, metrics, tools, certs, or education.
- Maintain an evidence ledger while drafting: claim -> source -> section.
- Use provenance tags per claim: corpus, current_chat, or user_confirmed_update.
- If the user shares relevant new facts that are not in corpus, ask 
    whether to persist them to corpus memory before the session ends.
- Do not add fluff: if content does not make an argument for a JD requirement/component, omit it.

Build workflow
1. Evidence retrieval
    - Map each Tier 1 requirement to one or more proof points.
    - Map Tier 2 only where supported.
    - Keep a short evidence map used for section drafting.
    - Surface unsupported Tier 1 requirements as explicit gaps.

2. Formatting
    - Strictly adhere to /mnt/data/ResumeTemplate.md; 
        do not invent alternate section structures unless user explicitly requests it.

3. Section Guidelines
    Target Title Line
    - One line; mirror JD language where truthful.

    Professional Summary
    - 2-4 lines.
    - Include supported years/domain/platforms/outcomes.
    - Use high-signal Tier 1 language naturally.

    Core Competencies
    - Build 2-5 grouped domains.
    - Prefer Tier 1 terms; include Tier 2 only when supported.
    - Target 7-14 high-signal entries.
    
    Professional Experience
    - Reverse chronological.
    - Most relevant roles: 4-7 bullets.
    - Older/less relevant roles: 1-3 bullets.
    - Bullet rules:
        - Action verb start.
        - Show what changed and why it mattered.
        - Include stack/platforms where relevant.
        - Use exact metrics when available.
        - No fabricated numbers.
        - Keep concise (1-2 lines each).
        - Order by impact and JD relevance.

4. Length control before user review
    - Default target: one page.
    - Prioritize relevance over completeness.
    - Remove weaker/redundant bullets before removing high-signal
        evidence.
""",
    ),
    AtomSpec(
        id="resume.confirmation",
        intents=frozenset({INTENT_RESUME_DRAFTING}),
        priority=7,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"resume"}),
        source_ref="ResumeBuildingGuidelines.md",
        title="Resume: User Acceptance",
        content="""\
1. Ask the user if they would like to make any changes or if they would like to export.
2. if they approve or ask to export:
    - RuntimeState: approved_markdown_ready = true.
    - Route to INTENT_PDF_EXPORT.
        """
    ),
    AtomSpec(
        id="jd.markdown_output_contract",
        intents=frozenset({INTENT_JD_ANALYSIS}),
        priority=7,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"jd"}),
        source_ref="JDAnalysisGuidelines.md",
        title="JD Markdown Output Contract",
        content="""\
Objective
- Treat the JD as a requirements document, not marketing copy. Extract constraints, 
weighted requirements, and the hiring risk model before writing resume content.

Rules
- Prioritize hard constraints and literal requirements.
- Do not infer unsupported claims.
- If a requirement is not supported, flag it as a gap.
- In the Binary Gates section, omit any gate not explicitly specified in the JD.
- Use marker statuses throughout the full analysis:
    - 🟢 solid matching corpus evidence
    - 🟡 mediocre/partial evidence alignment
    - 🔴 total gap (no supporting evidence)

Formatting
- Strictly adhere to `mnt/data/JDAnalysisTemplate.md`
""",
    ),
    AtomSpec(
        id="jd.resume_handoff_prompt",
        intents=frozenset({INTENT_JD_ANALYSIS}),
        priority=7,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"jd", "resume"}),
        source_ref="JDAnalysisGuidelines.md",
        title="JD to Resume Handoff",
        content="""\
At the end of JD analysis, 
1. RunTimeState: last_jd_analysis_present = false
2. Ask whether to draft a tailored resume now. If user says yes, route to INTENT_RESUME_DRAFTING.
""",
    ),
    AtomSpec(
        id="load_corpus.pull_and_validate",
        intents=frozenset({INTENT_LOAD_CORPUS}),
        priority=8,
        predicate=_needs_corpus_loaded,
        restrictive=True,
        tags=frozenset({"load_corpus", "memory", "precondition"}),
        source_ref="MemoryPersistenceGuidelines.md",
        title="Load Corpus",
        content="""\
Pull corpus from GitHub:
1. Use CareerCorpusSync.pull() from career_corpus_sync_surface.py to fetch canonical split files from GitHub.
2. Reassemble and hydrate local corpus runtime state.
3. Validate loaded corpus and set RuntimeState corpus_loaded/corpus_valid from real result.
4. If pull reports missing/invalid corpus, route to INTENT_ONBOARDING_IMPORT_REPAIR.
""",
    ),
    AtomSpec(
        id="load_corpus.corpus_missing_or_invalid",
        intents=frozenset({INTENT_LOAD_CORPUS}),
        priority=8,
        predicate=_loaded_and_needs_corpus_repair,
        restrictive=True,
        tags=frozenset({"load_corpus", "memory", "precondition"}),
        source_ref="MemoryPersistenceGuidelines.md",
        title="Load Corpus: Repair Required",
        content="""\
If corpus is missing or invalid after load/validation, do not continue memory-dependent
intents. Route to INTENT_ONBOARDING_IMPORT_REPAIR to rebuild and persist a valid corpus.
""",
    ),
    AtomSpec(
        id="load_corpus.user_view_contract",
        intents=frozenset({INTENT_LOAD_CORPUS}),
        priority=8,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"load_corpus", "memory"}),
        source_ref="instructions.txt",
        title="Load Corpus: User View Request",
        content="""\
If user requested to view corpus (full or section), load first, then return only requested
scope in readable markdown/text (avoid raw JSON unless explicitly asked).
""",
    ),
    AtomSpec(
        id="memory_status.state_block",
        intents=frozenset({INTENT_MEMORY_STATUS}),
        priority=8,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"memory_status", "memory", "conflict:status_output"}),
        source_ref="MemoryStateModel.md",
        title="Memory Status Block Format",
        content="""\
Required status plain text block
KEY: 🟢= true, 🔴 = false
MEMORY STATUS
- repo_exists: <🟢|🔴>
- corpus_exists: <🟢|🔴>
- corpus_loaded: <🟢|🔴>
- onboarding_complete: <🟢|🔴>
- last_written: <timestamp (%m/%d/%y %I:%M %p Local time)| Never>
""",
    ),
    AtomSpec(
        id="memory_status.optional_fields",
        intents=frozenset({INTENT_MEMORY_STATUS}),
        priority=8,
        predicate=_always,
        restrictive=False,
        tags=frozenset({"memory_status"}),
        source_ref="MemoryStateModel.md",
        title="Memory Status Optional Fields",
        content="""\
Optional status fields (show only when relevant)
- validated: include when a validation gate ran in this flow.
- persisted: include when a write attempt occurred this flow.
- fallback_used: include only when fallback path was used.
- method: include for persistence/status-debug contexts.
- retry_count: include when retries were attempted.
- verification: include when verification ran or failed.
""",
    ),
    AtomSpec(
        id="init.deterministic_sequence",
        intents=frozenset({INTENT_INITIALIZATION_OR_SETUP}),
        priority=1,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"initialization"}),
        source_ref="InitializationGuidelines.md",
        title="Initialization Deterministic Sequence",
        content="""\
1. ensure added /mnt/data to sys.path
2. initialize store and sync runtime objects
3. Check Repo Exists
4. Check Corpus Exists
5. runtime_initialized = true
6. emit initialization status (only if user requested initialization directly)
""",
    ),
    AtomSpec(
        id="init.check_repo_exists",
        intents=frozenset({INTENT_INITIALIZATION_OR_SETUP}),
        priority=2,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"initialization"}),
        source_ref="InitializationGuidelines.md",
        title="Initialization Check: Repo Exists",
        content="""\
1. ensure added /mnt/data to sys.path
2. resolve owner (tool call)
3. getMemoryRepo to check repo_exists (tool call)
4. createMemoryRepo only if repo does not exist (tool call)
5. confirm getMemoryRepo (tool call)
""",
    ),
    AtomSpec(
        id="init.check_corpus_exists",
        intents=frozenset({INTENT_INITIALIZATION_OR_SETUP}),
        priority=2,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"initialization", "memory"}),
        source_ref="InitializationGuidelines.md",
        title="Initialization Check: Corpus Exists",
        content="""\
1. after repo check, resolve default branch from getMemoryRepo
2. getBranchRef on default branch (tool call)
3. getGitCommit for head commit (tool call)
4. getGitTree recursively for head tree (tool call)
5. set corpus_exists = true only if CareerCorpus/corpus_index.json exists in tree
""",
    ),
    AtomSpec(
        id="init.github_account_gate",
        intents=frozenset({INTENT_INITIALIZATION_OR_SETUP}),
        priority=3,
        predicate=_always,
        restrictive=True,
        tags=frozenset({"initialization"}),
        source_ref="InitializationGuidelines.md",
        title="Initialization GitHub Account Gate",
        content="""\
If GitHub account/auth is not ready, stop setup and provide concise account setup/auth
steps. Do not continue bootstrap or writes until readiness is confirmed.
""",
    ),
    AtomSpec(
        id="state.require_initialization",
        intents=frozenset(
            {
                INTENT_MEMORY_PERSIST_UPDATE,
                INTENT_LOAD_CORPUS,
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
        title="State Gate: Initialization Required",
        content="""\
Runtime is not initialized or repo does not exist. Block current memory-dependent intent
and route to INTENT_INITIALIZATION_OR_SETUP first.
""",
    ),
    AtomSpec(
        id="state.require_corpus_preflight",
        intents=frozenset({INTENT_JD_ANALYSIS, INTENT_RESUME_DRAFTING, INTENT_MEMORY_PERSIST_UPDATE}),
        priority=10,
        predicate=_needs_corpus_loaded,
        restrictive=True,
        tags=frozenset({"state", "precondition", "memory"}),
        source_ref="JDAnalysisGuidelines.md",
        title="State Gate: Corpus Preflight Required",
        content="""\
Corpus is not loaded. Route to INTENT_LOAD_CORPUS to trigger pull/reassembly before
continuing this intent.
""",
    ),
    AtomSpec(
        id="state.require_onboarding_repair",
        intents=frozenset({INTENT_JD_ANALYSIS, INTENT_RESUME_DRAFTING, INTENT_MEMORY_PERSIST_UPDATE}),
        priority=10,
        predicate=_needs_corpus_repair,
        restrictive=True,
        tags=frozenset({"state", "precondition", "onboarding", "memory"}),
        source_ref="MemoryPersistenceGuidelines.md",
        title="State Gate: Onboarding/Repair Required",
        content="""\
Corpus is missing or invalid after preflight. Route to INTENT_ONBOARDING_IMPORT_REPAIR
before proceeding.
""",
    ),
    AtomSpec(
        id="state.require_jd_before_resume",
        intents=frozenset({INTENT_RESUME_DRAFTING}),
        priority=10,
        predicate=_needs_jd_first,
        restrictive=True,
        tags=frozenset({"state", "precondition", "resume", "jd"}),
        source_ref="instructions.txt",
        title="State Gate: JD Analysis Required",
        content="""\
Resume drafting requires completed JD analysis first. Route to INTENT_JD_ANALYSIS before
drafting.
""",
    ),
    AtomSpec(
        id="state.require_approved_markdown",
        intents=frozenset({INTENT_PDF_EXPORT}),
        priority=10,
        predicate=_needs_approved_markdown,
        restrictive=True,
        tags=frozenset({"state", "precondition", "pdf", "resume"}),
        source_ref="PDFExportGuidelines.md",
        title="State Gate: Approved Markdown Required",
        content="""\
PDF export is blocked until approved_markdown_ready=true. Route to
INTENT_RESUME_DRAFTING review/finalization first.
""",
    ),
    AtomSpec(
        id="state.memory_status_only_when_relevant",
        intents=frozenset({INTENT_MEMORY_STATUS, INTENT_MEMORY_PERSIST_UPDATE, INTENT_FAILURE_RECOVERY}),
        priority=10,
        predicate=_memory_status_requested,
        restrictive=True,
        tags=frozenset({"state", "memory_status", "conflict:status_output"}),
        source_ref="MemoryStateModel.md",
        title="State Rule: Status Emission Trigger",
        content="""\
Emit MEMORY STATUS only when requested, when status changed, or after a failed
operation.
""",
    ),
    AtomSpec(
        id="state.technical_details",
        intents=ALL_INTENT_IDS,
        priority=10,
        predicate=_technical_detail_requested,
        restrictive=False,
        tags=frozenset({"state", "detail_level"}),
        source_ref="instructions.txt",
        title="State Rule: Technical Detail Mode",
        content="""\
Technical detail requested. Include diagnostic fields and operation internals where
relevant.
""",
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
