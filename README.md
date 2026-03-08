# Resume Tailoring GPT (Lite)

Configuration repo for a custom GPT that analyzes JDs, drafts targeted resumes, and manages memory through a user-uploaded markdown corpus file.

## What This GPT Does
- Runs intent-based routing from `instructions.txt`.
- Uses focused knowledge files for onboarding, corpus updates, JD analysis, resume drafting, and PDF export.
- Uses one canonical corpus artifact: `career_corpus.md`.
- Requires corpus upload before JD analysis or resume tailoring.
- Returns updated corpus as downloadable markdown after approved changes.

## Core Files
- `instructions.txt`
  - Routing-first policy and global non-negotiables.
- `knowledge_files/`
  - `OnboardingGuidelines.md`
  - `CareerCorpusFormat.md`
  - `InitializationGuidelines.md`
  - `JDAnalysisGuidelines.md`
  - `ResumeBuildingGuidelines.md`
  - `PDFExportGuidelines.md`
  - `UATGuardrails.md`
  - `FAQ.md`
  - `ResumeTemplate.md`
  - `resume_renderer.py`, `resume_theme.py`

## Memory Model
Canonical artifact:
- `career_corpus.md`

Rules:
- Sectioned markdown structure with explicit numbered boundaries.
- Skills stay in Profile.
- Preferences are optional and live in section 6 of the same corpus file.
- Save/update success is reported only after updated download output is generated.

## Onboarding Approval Model
- Default: section-by-section review and approval.
- Optional: full-corpus review in canvas, then explicit approval.
- Finalization: one downloadable `career_corpus.md` output after final approval.

## Local Validation
Run contract tests:

```bash
python3 -m unittest -v \
  tests/test_instructions_memory_contract.py \
  tests/test_markdown_memory_contracts.py \
  tests/test_no_local_cache_contracts.py \
  tests/test_lite_upload_gate_contracts.py \
  tests/test_lite_corpus_export_contracts.py
```

## Dependency
- `reportlab` (for PDF rendering path)
