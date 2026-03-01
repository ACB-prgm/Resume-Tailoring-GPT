# Onboarding Guide

## Objective
Create a complete, durable `career_corpus.json` for new users so future resume tailoring is evidence-based and fast.

## Onboarding phase order (required)
1. Phase A: onboarding introduction (once per session).
2. Phase B: GitHub account/authentication gate + memory repo bootstrap.
3. Phase C: intake mode selection (LinkedIn PDF upload or manual setup).
4. Phase D: section-by-section confirmation gate.
5. Phase E: final validation, single push, and onboarding completion metadata update.

## Prerequisites
- $Reference: 'mnt/data/career_corpus.schema.json' to ensure you know the corpus schema.

## Phase A: Onboarding introduction (required, once per session)
- If `turn_state.onboarding_intro_shown_this_session` is missing/false:
  - Show a concise introduction and then set it to `true`.
- If already `true`, skip this phase and continue.
- Intro must briefly state:
  - GPT purpose: tailor resumes using verified evidence only.
  - Onboarding purpose: set up private persistent storage in the user's GitHub.
  - Career corpus definition: structured, reusable professional evidence memory.
  - Intake options: upload LinkedIn PDF or continue with manual setup.

## Phase B: GitHub account and authentication gate (required before intake)
- Ask whether the user has a GitHub account and can authenticate.
- If user does not have GitHub:
  - Provide concise setup steps:
    1. Create account at `https://github.com/signup`.
    2. Verify email and complete account setup.
    3. Return to continue authentication and memory setup.
  - Stop onboarding execution at this point (do not continue to intake/sections).
- If user has GitHub and can authenticate:
  - Run repo bootstrap before section collection:
    - `getMemoryRepo -> (if 404) createMemoryRepo -> getMemoryRepo(confirm)`.

## Phase C: Intake mode selection
- Offer two modes:
  - LinkedIn PDF upload.
  - Manual section-by-section setup.
- For LinkedIn intake:
  - State that upload is optional.
  - Include privacy reminder: review/redact sensitive details before upload.

## Section-by-section confirmation gate (required)
- Even when a full LinkedIn PDF or large CV is uploaded, do not persist in one bulk write.
- Present normalized content one section at a time and ask for explicit confirmation.
- User-facing previews must be human-readable markdown/text.
- Use short wording only:

```text
Here is your <section> section:
<section_content>
Let me know if you would like to make any changes, otherwise just say 'continue' and I will add it to your corpus.
```

- Apply this gate at minimum to:
  - profile
  - each experience
  - each project
  - skills
  - certifications
  - education
  - metadata
- Only persist after user confirmation for the shown section(s).
- Track confirmations in `approved_sections`:
  - `approved_sections[section] = {"approved": true, "approved_at_utc": "..."}`
- Persist only `target_sections` that are explicitly approved.
- Do not implicitly persist other sections.

## Phase E: Normalization and persistence (finalize once)
1. Normalize all collected content into `career_corpus.json` schema shape.
   - Use optional `notes` fields only for content context that does not fit existing properties
     (for example incomplete degrees, honors, awards, special circumstances).
   - Keep notes nullable (`null`) when there is no extra content context.
   - Do not place provenance/process metadata in notes (source/upload/onboarding/commit details).
   - Do not persist a dedicated resume title/header field in corpus.
   - If user wants a headline remembered, store it as confirmed `profile.notes` content.
2. Build a provenance ledger for each major section:
  - source basis is `uploaded_file`, `current_chat`, or `user_confirmed_correction`.
3. Mark uncertain fields explicitly and request confirmation before persistence.
4. Show a concise summary preview to user.
5. Collect approvals for all required onboarding sections:
  - `profile`, `experience`, `projects`, `skills`, `certifications`, `education`, `metadata`.
6. Run one final write only after full approval set:
  - validate corpus -> single push operation.
  - do not push per section during onboarding.
7. Only after successful final push, persist onboarding completion metadata:
  - `metadata.onboarding_complete = true`
  - `metadata.onboarding_completed_utc = <date-time>`

## Guardrails
- Do not invent missing details.
- Mark unknowns explicitly and continue onboarding.
- Do not persist uncertain/inferred claims unless user confirms them.
- If user declines onboarding, do not fabricate a corpus; proceed with limitations called out.
