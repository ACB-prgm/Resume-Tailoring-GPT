# Resume Tailoring GPT

Configuration repo for a custom GPT that analyzes JDs, drafts targeted resumes, and persists career memory in GitHub as markdown.

Repository: https://github.com/ACB-prgm/Resume-Tailoring-GPT/tree/main

## What This GPT Does
- Runs intent-based routing from `instructions.txt`.
- Uses focused knowledge files for onboarding, persistence, JD analysis, resume drafting, and PDF export.
- Stores career memory as markdown section files in the user's private GitHub repo.
- Uses remote-first memory reads/writes.
- Uses direct section-target reads/writes by intent/context.
- Supports optional user preference memory in `preferences.md`.

## Core Files
- `instructions.txt`
  - Routing-first policy and global non-negotiables.
- `knowledge_files/`
  - `OnboardingGuidelines.md`
  - `MemoryPersistenceGuidelines.md`
  - `MemoryStateModel.md`
  - `CareerCorpusFormat.md`
  - `InitializationGuidelines.md`
  - `JDAnalysisGuidelines.md`
  - `ResumeBuildingGuidelines.md`
  - `PDFExportGuidelines.md`
  - `UATGuardrails.md`
  - `FAQ.md`
  - `ResumeTemplate.md`
  - `resume_renderer.py`, `resume_theme.py`
- `github_action_schema.json`
  - Tool-layer contract used by GitHub tool calls.

## Memory Model
Canonical corpus files (remote):
- `CareerCorpus/profile.md`
- `CareerCorpus/experience.md`
- `CareerCorpus/projects.md`
- `CareerCorpus/certifications.md`
- `CareerCorpus/education.md`

Optional top-level file:
- `preferences.md` (only when user explicitly asks to remember a preference)

Rules:
- No empty section files.
- `Skills` stays in `profile.md`.
- No corpus metadata file.
- Push only after required approvals.

## Onboarding Approval Model
- Default: section-by-section review and approval.
- Optional: full-corpus review in canvas, then explicit approval.
- Push once at the end after final approval.

## Local Validation
Run contract tests:

```bash
python3 -m unittest -v \
  tests/test_instructions_memory_contract.py \
  tests/test_markdown_memory_contracts.py \
  tests/test_github_action_schema_markdown_contract.py
```

## Dependency
- `reportlab` (for PDF rendering path)
