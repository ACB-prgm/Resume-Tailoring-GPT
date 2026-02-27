# Memory Persistence Guide

## Objective
Persist durable user memory safely in one fixed GitHub repository with strict validation and deterministic status reporting.

## Fixed repository rule
- Use only repository `career-corpus-memory`.
- Do not create or read any alternative memory repository.

## Canonical memory files
- `career_corpus.json`
- `preferences.json`
- Local corpus cache path: `/mnt/data/career_corpus.json`
- Local sync metadata path: `/mnt/data/career_corpus.meta.json`

## Local-first runtime model (required)
- Use `CareerCorpusStore` for all in-session reads/edits.
- Keep corpus loaded in memory; avoid repeated tool fetches.
- Use `CareerCorpusSync` only for explicit:
  - `pull()` (refresh local cache from GitHub)
  - `push()` (persist approved changes to GitHub)
- Do not fetch/decode/parse the full corpus through tools for every edit.

## Startup bootstrap (required)
1. Resolve `{owner}` via `getAuthenticatedUser`.
2. Check fixed repo via `getMemoryRepo`.
3. If `404`, create via `createMemoryRepo` with fixed values:
- `name=career-corpus-memory`
- `private=true`
- `auto_init=true`
4. Optionally call `setMemoryRepoTopics` with `["career-corpus-memory"]`; continue if topic call fails.
5. Check `career_corpus.json` and `preferences.json` existence via read endpoints.
6. Report the canonical check line:
- `Memory repo exists: Yes/No; career_corpus.json exists: Yes/No.`
7. Emit the required status block from `MemoryStateModel.md`.

## Explicit sync behavior
- `pull(force=False)`:
  - Call `readCareerCorpusJson`.
  - If remote `sha` matches `meta.remote_sha` and `force` is false, no-op.
  - Else decode base64 content, replace local `/mnt/data/career_corpus.json`, update meta timestamps and sha.
- `push(message)`:
  - Run schema validation and preflight.
  - Upload only when local store is dirty.
  - Include `sha` for updates.
  - On success, update `meta.remote_sha` and `last_push_utc`.

## Validation + preflight sequence (hard fail)
Before **any** write:
1. Import helpers from `/mnt/data/memory_validation.py`.
2. Read existing JSON (and `sha`) from the target file when present.
3. Apply minimal patch + validate:
- `validate_career_patch(existing, patch)` or `validate_preferences_patch(existing, patch)`
4. Enforce write guard:
- `assert_validated_before_write(validated, context)`
5. Build transport payload:
- `build_upsert_payload(message, merged_json, sha=sha_if_present)`
6. Run preflight:
- `verify_base64_roundtrip(merged_json)` must pass.
7. Only then call upsert endpoint.

## Retry and failure handling
- If GitHub upsert returns `422`, perform exactly one retry after rebuilding payload/preflight.
- If retry fails, stop writes and set state to `PERSIST_FAILED`.
- Provide explicit manual next steps; no async/background promises.

## Persistence outcome contract
- `persisted=true` only when API returns success (`200` or `201`).
- Local fallback files are allowed only as temporary recovery aids and must be labeled:
- `persisted=false`, `fallback_used=true`, `status=NOT PERSISTED`

## Onboarding and repair triggers
- If `career_corpus.json` is missing or schema-invalid, route to onboarding/repair before tailoring.
- Onboarding behavior is defined in `/mnt/data/OnboardingGuidelines.md`.

## Guardrails
- Never overwrite memory with blank content unless user explicitly requests it.
- Never persist inferred or unsupported claims.
- If user introduces new facts not in corpus, ask for explicit persist approval first.
