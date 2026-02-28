# Resume Building Guide

## Objective
Convert JD Analysis Output + verified corpus evidence into a tailored, ATS-safe resume draft using the canvas tool in the provided markdown template.

## Inputs required
- JD Analysis Output (from `JDAnalysisGuidelines.md`)
- Canonical memory files from persistent memory repo:
  - `career_corpus.json`
  - `preferences.json`
- Current chat facts provided by user
- Resume template markdown

## Evidence rules (non-negotiable)
- Every claim must be supported by corpus or current chat.
- If a JD requirement is unsupported, do not claim it.
- Prefer recent, high-impact evidence.
- Do not invent employers, titles, dates, metrics, tools, certs, or education.
- Maintain an evidence ledger while drafting: `claim -> source -> section`.
- Use provenance tags per claim: `corpus`, `current_chat`, or `user_confirmed_update`.
- If the user shares relevant new facts that are not in corpus, ask whether to persist them to corpus memory before the session ends.
- If `career_corpus.json` is missing, invalid, or schema-noncompliant, route to onboarding/repair before resume drafting.
- Validate corpus/preferences with `/mnt/data/memory_validation_surface.py` before using them for drafting.
- Block unsupported factual inserts unless user explicitly confirms and approves persistence path.
- Resume title/header lines are generated per JD and are not persisted as dedicated corpus fields.

## Build workflow
1) Evidence retrieval
- Map each Tier 1 requirement to one or more proof points.
- Map Tier 2 only where supported.
- Keep a short evidence map used for section drafting.
- Surface unsupported Tier 1 requirements as explicit gaps.

2) Resume construction (ATS-safe)
- Header:
  - Keep as template default unless user requests changes.
- Target Title Line:
  - One line; mirror JD language where truthful.
- Professional Summary:
  - 2-4 lines.
  - Include supported years/domain/platforms/outcomes.
  - Use high-signal Tier 1 language naturally.
- Core Competencies:
  - Build 2-5 grouped domains.
  - Bullet-separated items only (no sentences).
  - Prefer Tier 1 terms; include Tier 2 only when supported.
  - Target 7-15 high-signal entries.
- Professional Experience:
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
- Education:
  - Include only supported degree/institution/year details.

3) Recruiter/ATS alignment check
- Confirm Tier 1 keywords are explicitly represented in:
  - Title line
  - Summary
  - Core Competencies
  - First 2-3 bullets in most relevant role
- Confirm every represented Tier 1 token has a linked evidence ledger entry.

4) Length control before user review
- Default target: one page.
- Prioritize relevance over completeness.
- Remove weaker/redundant bullets before removing high-signal evidence.

## Output format before export
- Prepare markdown in the template for user review in the canvas tool.
- Do not export PDF until user confirms the draft.
