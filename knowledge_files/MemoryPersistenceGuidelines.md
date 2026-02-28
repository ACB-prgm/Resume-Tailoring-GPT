# Memory Persistence Guide

## Objective
Persist durable user memory safely in one fixed GitHub repository with strict validation and deterministic status reporting.

## Fixed repository rule
- Use only repository `career-corpus-memory`.
- Do not create or read any alternative memory repository.

## Canonical memory files
- Split corpus files (remote canonical):
  - `corpus_index.json` (manifest)
  - `corpus_profile.json`, `corpus_summary_facts.json`, `corpus_skills.json`,
    `corpus_certifications.json`, `corpus_education.json`, `corpus_metadata.json`
  - `corpus_experience_<id>.json` (one file per experience)
  - `corpus_project_<id>.json` (one file per project)
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
- Before Python imports, bootstrap:
  - add `/mnt/data` to `sys.path`.
- Do not run direct Git writes before store/sync bootstrap completes.

## Startup bootstrap (required)
1. Resolve `{owner}` via `getAuthenticatedUser`.
2. Run deterministic bootstrap: `getMemoryRepo -> (if 404) createMemoryRepo -> getMemoryRepo(confirm)`.
3. Enforce `repo_create_attempted_this_turn` guard (no double create in same turn).
4. Optionally call `setMemoryRepoTopics` with `["career-corpus-memory"]`; continue if topic call fails.
5. Initialize store/sync objects.
6. Check split corpus presence via manifest `corpus_index.json` (legacy `career_corpus.json` may still be read).
7. Report the canonical check line:
- `Memory repo exists: Yes/No; career corpus exists: Yes/No.`
8. Emit the required status block from `MemoryStateModel.md`.

## Explicit sync behavior
- `pull(force=False)`:
  - Resolve branch head and load `corpus_index.json` from Git tree/blob APIs.
  - For Git read calls, send:
    - `getBranchRef`, `getGitCommit`, `getGitTree`: `Accept: application/vnd.github+json`
    - `getGitBlob`: `Accept: application/vnd.github.raw`
  - If manifest sha matches `meta.remote_file_sha` and `force` is false, no-op.
  - Else read referenced split files, assemble local `/mnt/data/career_corpus.json`, update meta.
- `pull_if_stale_before_write(force=False)`:
  - Use before a section commit flow.
  - If local store is already loaded and has `remote_file_sha`, skip pre-write pull.
  - This reduces redundant `getGitBlob` calls before write.
- `push(message)`:
  - Accept `target_sections` + `approved_sections` for guarded section writes.
  - Reject write if target sections are not explicitly approved.
  - Reject write when changed/deleted paths include unapproved sections.
  - Run schema validation and UTF-8 payload diagnostics.
  - Upload only when local store is dirty.
  - Materialize split docs + manifest and per-file hashes.
  - Determine changed/deleted paths vs `meta.remote_file_hashes`.
  - Use Git Data flow only:
    - `createGitBlob` -> `createGitTree` -> `createGitCommit` -> `updateBranchRef`
  - On success, verify changed/deleted paths by tree/blob SHA match from the committed tree.
  - Persisted success requires successful write and verification.
  - Update meta fields:
    - `remote_blob_sha`, `remote_commit_sha`, `remote_branch`, `remote_file_sha`,
      `remote_file_hashes`, `last_verified_utc`, `last_push_method`.

## Validation + preflight sequence (hard fail)
Before **any** write:
0. Confirm initialization completed (owner resolved, repo checked/created, store/sync initialized).
1. Import helpers from `/mnt/data/memory_validation.py`.
2. Validate full target document:
- `validate_career_corpus(...)` / `validate_preferences(...)`
3. For onboarding/import flows, present section preview(s) and get explicit user confirmation before write.
   - Required prompt style:
   - `Here is your <section> section:`
   - `<section_content>`
   - `If this looks good, let me know and I'll save it to the corpus.`
4. Run diagnostics:
- `diagnose_payload_integrity(canonical_json_text(...))`
5. Enforce write guard:
- `assert_validated_before_write(validated, context)`
  - `assert_sections_explicitly_approved(approved_sections, target_sections)` when section writes are used
6. Execute Git Data write flow.
7. Verify committed tree/blob SHAs match expected changed paths.

## Retry and failure handling
- Retryable errors: `409`, transient `422`, and transient tool transport failures.
- Perform exactly one retry using fresh ref/commit state.
- If retry fails, stop writes and set state to `PERSIST_FAILED`.
- Provide explicit manual next steps; no async/background promises.

## Persistence outcome contract
- `persisted=true` only when ref update succeeds AND post-write verification hash matches.
- Local fallback files are allowed only as temporary recovery aids and must be labeled:
- `persisted=false`, `fallback_used=true`, `status=NOT PERSISTED`
- Push status must include:
  - `method`, `retry_count`, `verification`, `error_code`

## Onboarding and repair triggers
- If assembled corpus is missing/invalid or split manifest/files are missing/invalid, route to onboarding/repair before tailoring.
- Onboarding behavior is defined in `/mnt/data/OnboardingGuidelines.md`.

## Guardrails
- Never overwrite memory with blank content unless user explicitly requests it.
- Never persist inferred or unsupported claims.
- If user introduces new facts not in corpus, ask for explicit persist approval first.
