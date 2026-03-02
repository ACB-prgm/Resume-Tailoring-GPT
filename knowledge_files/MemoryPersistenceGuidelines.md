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
- Local mirror path prefix: `/mnt/data/CareerCorpus/`
- Format reference: `/mnt/data/CareerCorpusFormat.md`

## Rules
- One file per section.
- Do not save empty section files.
- If a section is empty, skip that file; if it previously existed, delete it in the same commit.
- `Skills` must be inside `profile.md`.
- Do not persist a metadata section/file.

## Direct read flow
1. Resolve owner: `getAuthenticatedUser`.
2. Ensure repo exists: `getMemoryRepo`, optional `createMemoryRepo`, confirm `getMemoryRepo`.
3. Resolve head: `getBranchRef` -> `getGitCommit` -> `getGitTree(recursive=1)`.
4. Discover canonical section files in `CareerCorpus/`.
5. Read discovered files with `getGitBlob`.
6. Mirror them to `/mnt/data/CareerCorpus/`.

## Direct write flow
1. Ensure repo exists.
2. Determine target section(s).
3. Build section markdown from `/mnt/data/CareerCorpusFormat.md`.
4. For each target section:
   - non-empty content -> write/update file.
   - empty content -> do not write; delete existing file if present.
5. `createGitBlob` for non-empty section files.
6. `createGitTree` with changed section paths.
7. `createGitCommit`.
8. `updateBranchRef`.
9. On success, mirror changed files locally.

## Header contract
- `getGitBlob` and `createGitBlob`: `Accept: application/vnd.github.raw`
- All other memory calls that include `Accept`: `Accept: application/vnd.github+json`

## Retry and failure handling
- One deterministic retry for retryable write failures.
- If retry fails, return explicit failure and next manual step.
- Do not claim persistence success when ref update fails.
