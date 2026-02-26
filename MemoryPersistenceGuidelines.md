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

## Memory files in fixed repo
- `CareerCorpus.txt` (persistent user career evidence)
- `preferences.txt` (persistent user formatting/style/process preferences)

## Read/update rules
1) Read current values when present:
- `readCareerCorpus`
- `readUserPreferences`

2) Upsert values using base64 content:
- `upsertCareerCorpus`
- `upsertUserPreferences`

3) For updates, include latest file `sha` from the corresponding GET response.

## Operational guardrails
- Never overwrite corpus/preferences with blank content unless user explicitly asks.
- Do not invent memory content; store only user-provided or user-approved updates.
- If new relevant user facts appear in chat and are missing from corpus, ask for explicit confirmation before writing them to `CareerCorpus.txt`.
- Keep commit messages specific (for example: `Update CareerCorpus from approved session edits`).
