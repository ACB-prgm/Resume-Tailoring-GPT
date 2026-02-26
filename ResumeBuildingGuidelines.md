# Resume Building Guide

## Objective
Convert JD Analysis Output + verified corpus evidence into a tailored, ATS-safe resume draft in the provided markdown template.

## Inputs required
- JD Analysis Output (from `JDAnalysisGuidelines.md`)
- Career corpus file(s) from persistent memory repo (`CareerCorpus.txt`) and/or local corpus file
- Current chat facts provided by user
- User preferences from persistent memory repo (`preferences.txt`) when available
- Resume template markdown

## Evidence rules (non-negotiable)
- Every claim must be supported by corpus or current chat.
- If a JD requirement is unsupported, do not claim it.
- Prefer recent, high-impact evidence.
- Do not invent employers, titles, dates, metrics, tools, certs, or education.
- If the user shares relevant new facts that are not in corpus, ask whether to persist them to corpus memory before the session ends.

## Build workflow
1) Evidence retrieval
- Map each Tier 1 requirement to one or more proof points.
- Map Tier 2 only where supported.
- Keep a short evidence map used for section drafting.

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

4) Length control before user review
- Default target: one page.
- Prioritize relevance over completeness.
- Remove weaker/redundant bullets before removing high-signal evidence.

## Output format before export
- Prepare markdown in the template for user review in canvas.
- Preserve expected structural markers (including `---` rule lines).
- Do not export PDF until user confirms the draft.
