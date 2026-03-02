# Initialization Guide

## Objective
Run deterministic startup for direct GitHub markdown memory operations.

## Mandatory startup order
1. Add `/mnt/data` to `sys.path` before Python imports.
2. Confirm GitHub account/auth readiness.
3. Resolve owner using `getAuthenticatedUser`.
4. `getMemoryRepo(owner)`.
5. If `404`, `createMemoryRepo` once, then confirm with `getMemoryRepo(owner)`.
6. Resolve branch/head references with `getBranchRef` and `getGitCommit`.
7. Get repo tree with `getGitTree(recursive=1)` to discover existing memory files.
8. If top-level `preferences.md` exists, load it with `getGitBlob` and mirror to `/mnt/data/preferences.md`.
9. Load format guide `/mnt/data/CareerCorpusFormat.md` before corpus writes.

## No-GitHub branch
- If account/auth is not ready, stop memory flow and give concise setup steps.

## Header contract
- `getGitBlob` and `createGitBlob`: `Accept: application/vnd.github.raw`
- All other calls that include `Accept`: `Accept: application/vnd.github+json`

## Architecture lock
- Use direct GitHub tool-call workflow only.
- Corpus persistence is section-scoped files under `CareerCorpus/`.
- User preferences persist in top-level `preferences.md` (free-form markdown).
- Do not write empty section files.
- Keep skills in `profile.md`.
