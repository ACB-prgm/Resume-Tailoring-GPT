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
- Format reference: `/mnt/data/CareerCorpusFormat.md`

## Rules
- One file per section.
- Do not save empty section files.
- `Skills` must be inside `profile.md`.
- Do not persist a metadata section/file.
- Use GitHub section files as the active working source.
- Read and write section files directly by intent/context.
- Write `preferences.md` only when the user explicitly states a preference to remember.
- `preferences.md` has no strict schema/template requirement.
- Do not create or keep an empty `preferences.md`.
- For onboarding, default approval mode is section-by-section.
- If user chooses full-corpus approval, review full draft in canvas and collect explicit final approval.
- In onboarding, push exactly once after approvals; do not push during draft review.

## Direct read flow (on-demand)
1. Resolve owner: `getAuthenticatedUser` (if not already known).
2. Ensure repo exists: `getMemoryRepo`, optional `createMemoryRepo` (if not already exists), confirm `getMemoryRepo`.
3. Resolve head: `getBranchRef` -> `getGitCommit`.
4. Read root tree non-recursively with `getGitTree`.
5. Locate `CareerCorpus` subtree SHA and read that subtree non-recursively with `getGitTree`.
6. Read only sections required for the current intent using `getGitBlob`.
7. Read `preferences.md` only when needed for current intent.

### Intent read scope
- `jd_analysis`: `profile`, `experience`, `projects`, optional `preferences`.
- `resume_drafting`: `profile`, `experience`, `projects`, `education`, `certifications`, optional `preferences`.
- `memory_persist_update`: only sections being edited, plus optional `preferences`.
- `memory_status`: tree/head probe first; fetch blob content only if user asks for content-level detail.
- `onboarding_import_repair`: fetch only sections needed to repair/merge current onboarding flow.

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
10. Use the updated remote section files as the source for subsequent reads/writes.

## Header contract
- `getGitBlob` and `createGitBlob`: `Accept: application/vnd.github.raw`
- All other memory calls that include `Accept`: `Accept: application/vnd.github+json`

## Retry and failure handling
- One deterministic retry for retryable write failures.
- If retry fails, return explicit failure and next manual step.
- Do not claim persistence success when ref update fails.
