# Memory Persistence Guide

## Objective
Persist and retrieve memory using one markdown file in GitHub with a local mirror copy.

## Fixed repository rule
- Use only repository `career-corpus-memory`.
- Do not create or read alternative memory repositories.

## Canonical memory files
- Remote canonical: `CareerCorpus/corpus.md`
- Local mirror: `/mnt/data/CareerCorpus/corpus.md`
- Format reference: `/mnt/data/CareerCorpusFormat.md`

## Direct read flow
1. Resolve owner: `getAuthenticatedUser`.
2. Ensure repo exists: `getMemoryRepo`, optional `createMemoryRepo`, confirm `getMemoryRepo`.
3. Resolve head: `getBranchRef` -> `getGitCommit` -> `getGitTree(recursive=1)`.
4. Locate `CareerCorpus/corpus.md`.
5. If found, read with `getGitBlob` and overwrite local mirror.
6. If not found, treat corpus as missing and route to onboarding/import.

## Direct write flow
1. Ensure repo exists.
2. Load current corpus markdown (local mirror first, then remote if needed).
3. Determine target section(s) for this write:
   - `Profile`, `Skills`, `Experience`, `Projects`, `Certifications`, `Education`, `Metadata`.
4. Replace only target section blocks and preserve all non-target sections.
5. Reorder/normalize headings to match `/mnt/data/CareerCorpusFormat.md` as much as possible.
6. Build final markdown corpus text.
7. `createGitBlob` for markdown text.
8. `createGitTree` path `CareerCorpus/corpus.md`.
9. `createGitCommit`.
10. `updateBranchRef`.
11. Only after successful ref update, overwrite local mirror.

## Header contract
- `getGitBlob` and `createGitBlob`: `Accept: application/vnd.github.raw`
- All other memory calls that include `Accept`: `Accept: application/vnd.github+json`

## Simplification rules
- No schema validation.
- No manifest/index file.
- No split-doc assembly logic.
- No section approval or validation gates in the write path.
- Format adherence is best-effort against `/mnt/data/CareerCorpusFormat.md`.

## Retry and failure handling
- One deterministic retry for retryable write failures.
- If retry fails, return explicit failure and next manual step.
- Do not claim persistence success when ref update fails.

## Onboarding completion storage
- Keep onboarding completion state inside `CareerCorpus/corpus.md` (frontmatter or explicit metadata section).
