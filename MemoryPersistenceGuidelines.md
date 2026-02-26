# Memory Persistence Guide

## Objective
Persist long-term user memory in one fixed GitHub repository across sessions.

## Fixed repository rule (mandatory)
- Repository name is constant: `career-corpus-memory`
- Do not create or use any other memory repository.

## Required startup sequence
1) Resolve authenticated user
- Call `getAuthenticatedUser` and read login as `{owner}`.

2) Ensure fixed memory repo exists
- Call `getMemoryRepo` with `{owner}`.
- If `404`, call `createMemoryRepo` with:
  - `name`: `career-corpus-memory`
  - `private`: `true`
  - `auto_init`: `true`

3) Optional topic tagging (no extra scopes beyond `repo`)
- Call `setMemoryRepoTopics` with:
  - `names`: `["career-corpus-memory"]`
- If topic update fails, continue without blocking core workflow.

## Canonical memory files in fixed repo
- `career_corpus.json` (persistent user career evidence)
- `preferences.json` (persistent user formatting/style/process preferences)

## Onboarding trigger
- If `career_corpus.json` is missing (`404`) or invalid JSON/schema, route to onboarding.
- Onboarding should initialize both `career_corpus.json` and `preferences.json`.

## Read/update rules
1) Read current values when present:
- `readCareerCorpusJson`
- `readPreferencesJson`

2) Upsert values using base64 content:
- `upsertCareerCorpusJson`
- `upsertPreferencesJson`

3) For updates, include latest file `sha` from the corresponding GET response.

## Required schema validation sequence (hard fail)
Before writing either JSON file:
1. Read target schema:
  - `/mnt/data/schemas/career_corpus.schema.json`
  - `/mnt/data/schemas/preferences.schema.json`
2. Read current JSON document from memory repo.
3. Apply the minimal intended patch.
4. Validate full resulting JSON against schema.
5. If invalid, reject write and request correction.
6. If valid and user-approved, upsert with correct `sha`.

## Operational guardrails
- Never overwrite corpus/preferences with blank content unless user explicitly asks.
- Do not invent memory content; store only user-provided or user-approved updates.
- If new relevant user facts appear in chat and are missing from corpus, ask for explicit confirmation before writing them to `career_corpus.json`.
- Keep commit messages specific (for example: `Update career_corpus.json from approved session edits`).

## Non-canonical legacy notes
- Legacy `.txt` corpus files may exist from earlier versions.
- Treat legacy text as non-canonical context only; all new writes must use JSON canonical files.
