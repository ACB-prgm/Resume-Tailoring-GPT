# Memory Persistence Guide

## Objective
Persist and retrieve memory as markdown section files in GitHub.

## Fixed repository rule
- Use only repository `career-corpus-memory`.

## Canonical section files
- `CareerCorpus/profile.md` (includes skills)
- `CareerCorpus/experience.md`
- `CareerCorpus/projects.md`
- `CareerCorpus/certifications.md`
- `CareerCorpus/education.md`
- `preferences.md` (top-level repo file for user preferences, free-form markdown)
- Local mirror path prefix: `/mnt/data/CareerCorpus/`
- Format reference: `/mnt/data/CareerCorpusFormat.md`

## Rules
- One file per section.
- Do not save empty section files.
- If a section is empty, skip that file; if it previously existed, delete it in the same commit.
- `Skills` must be inside `profile.md`.
- Do not persist a metadata section/file.
- Write `preferences.md` only when the user explicitly states a preference to remember.
- `preferences.md` has no strict schema/template requirement.
- Do not create or keep an empty `preferences.md`.

## Direct read flow
1. Resolve owner: `getAuthenticatedUser`.
2. Ensure repo exists: `getMemoryRepo`, optional `createMemoryRepo`, confirm `getMemoryRepo`.
3. Resolve head: `getBranchRef` -> `getGitCommit` -> `getGitTree(recursive=1)`.
4. Discover canonical section files in `CareerCorpus/`.
5. Read discovered files with `getGitBlob`.
6. If top-level `preferences.md` exists, read it with `getGitBlob`.
7. Mirror section files to `/mnt/data/CareerCorpus/` and `preferences.md` to `/mnt/data/preferences.md`.

## Direct write flow
1. Ensure repo exists.
2. Determine target section(s).
3. Build section markdown from `/mnt/data/CareerCorpusFormat.md`.
4. For each target section:
   - non-empty content -> write/update file.
   - empty content -> do not write; delete existing file if present.
5. For preferences:
   - if user explicitly provided a preference note, write/update top-level `preferences.md`.
   - if resulting preference content is empty, do not write it.
6. `createGitBlob` for non-empty changed files.
7. `createGitTree` with changed paths.
8. `createGitCommit`.
9. `updateBranchRef`.
10. On success, mirror changed section files locally and mirror `preferences.md` to `/mnt/data/preferences.md` when changed.

## Header contract
- `getGitBlob` and `createGitBlob`: `Accept: application/vnd.github.raw`
- All other memory calls that include `Accept`: `Accept: application/vnd.github+json`

## Retry and failure handling
- One deterministic retry for retryable write failures.
- If retry fails, return explicit failure and next manual step.
- Do not claim persistence success when ref update fails.
