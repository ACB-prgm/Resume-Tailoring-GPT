# Onboarding Guide

## Objective
Create a complete, durable `career_corpus.json` for new users so future resume tailoring is evidence-based and fast.

## When onboarding runs
- Run onboarding if `career_corpus.json` is missing or invalid.
- Re-run onboarding when user explicitly asks to rebuild their corpus.

## Opening explanation (required)
Explain that the career corpus is:
- A complete and detailed professional history (like a highly detailed CV).
- Persistent memory used to tailor each resume to each JD.
- The primary evidence source for claims in resume output.

## Optional LinkedIn PDF intake (first prompt)
Start onboarding with this optional suggestion:
- Ask the user to download their LinkedIn profile as a PDF and upload it for context.
- State clearly this step is optional.
- Include privacy reminder: user should review/redact sensitive details before upload.

## Uploaded-source ingestion receipt (required)
- If user uploads corpus text, resume text, or LinkedIn PDF-derived text, read it before assessment.
- Default intake mode for user uploads is context-first:
  - read/analyze uploaded content directly in model context first.
  - use Python/regex extraction only when needed for reliability or when user requests it.
- Emit this receipt before any quality claim:

```text
INGESTION RECEIPT
- source: <filename>
- read_confirmed: yes
- sections_detected: [profile, experience, projects, skills, ...]
- gaps_detected: [missing dates, missing metrics, unknown employer/location, ...]
```

## Normalization summary (required before approvals)
Emit a compact normalization summary before section previews:

```text
NORMALIZATION SUMMARY
- detected_sections: [profile, experience, projects, skills, certifications, education, metadata]
- counts:
  - experience: <n>
  - projects: <n>
  - certifications: <n>
  - education: <n>
  - skills.technical: <n>
- ambiguous_fields: [<field/path>, ...]
```

## Section-by-section confirmation gate (required)
- Even when a full LinkedIn PDF or large CV is uploaded, do not persist in one bulk write.
- Present normalized content one section at a time and ask for explicit confirmation.
- User-facing previews must be human-readable markdown/text.
- Do not print raw JSON objects unless the user explicitly asks for raw JSON.
- Use short wording only:

```text
Here is your <section> section:
<section_content>
If this looks good, let me know and I'll save it to the corpus.
```

- Apply this gate at minimum to:
  - profile
  - experience
  - projects
  - skills
  - certifications
  - education
  - metadata
- Links preview format (required):
  - show each link as `- <name>: <url>`
  - never show links as raw JSON objects in normal flow
- Only persist after user confirmation for the shown section(s).
- Track confirmations in `approved_sections`:
  - `approved_sections[section] = {"approved": true, "approved_at_utc": "..."}`
- Persist only `target_sections` that are explicitly approved.
- Do not implicitly persist other sections.
- For scaffolding, ask explicitly:
  - `Create empty sections now? Yes/No.`

## Guided interview sections (required)
Collect structured data in this order if upload is missing or incomplete:
1. Profile and contact basics
- Name, location, email/phone (if user wants included), links.
- Link format must be objects:
  - `{"name": "GitHub", "url": "https://github.com/ACB-prgm"}`

2. Experience (chronological, detailed)
- Employer, title, dates, location.
- Core responsibilities.
- Tools/platforms used.
- Quantified outcomes and business impact.

3. Projects
- Project name, role, stack, scope, measurable outcomes.

4. Skills / tools / methods
- Technical stacks, platforms, process methods, domain strengths.

5. Certifications
- Name, issuer, date/status.

6. Education
- Degree, institution, graduation year.

7. Measurable outcomes summary
- Reusable metrics (time saved, cost reduction, quality/reliability improvements).

## Normalization and persistence
1. Normalize all collected content into `career_corpus.json` schema shape.
   - Use optional `notes` fields only for content context that does not fit existing properties
     (for example incomplete degrees, honors, awards, special circumstances).
   - Keep notes nullable (`null`) when there is no extra content context.
   - Do not place provenance/process metadata in notes (source/upload/onboarding/commit details).
   - Do not persist a dedicated resume title/header field in corpus.
   - If user wants a headline remembered, store it as confirmed `profile.notes` content.
2. Initialize `preferences.json` with defaults if missing.
3. Build a provenance ledger for each major section:
- source basis is `uploaded_file`, `current_chat`, or `user_confirmed_correction`.
4. Mark uncertain fields explicitly and request confirmation before persistence.
5. Show a concise summary preview to user.
6. Ask for explicit confirmation before first save.
7. Validate both documents with `/mnt/data/memory_validation_surface.py` before writing.
8. Persist only schema-valid JSON via memory repo upsert operations.

## Guardrails
- Do not invent missing details.
- Mark unknowns explicitly and continue onboarding.
- Do not persist uncertain/inferred claims unless user confirms them.
- If user declines onboarding, do not fabricate a corpus; proceed with limitations called out.
