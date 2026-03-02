# Initialization Guide

## Objective
Run deterministic startup for direct GitHub markdown memory operations.

## Mandatory startup order
1. Add `/mnt/data` to `sys.path` before Python imports.
2. Confirm GitHub account/auth readiness.
3. Resolve owner using `getAuthenticatedUser`.
4. `getMemoryRepo(owner)`.
5. If `404`, `createMemoryRepo` once, then confirm with `getMemoryRepo(owner)`.
6. Resolve branch/head references with `getBranchRef` and `getGitCommit` when memory read/write is requested.
7. Load format guide `/mnt/data/CareerCorpusFormat.md` before any corpus write operation.

## No-GitHub branch
- If account/auth is not ready, stop memory flow and give concise setup steps.

## Required initialization status block
```text
INITIALIZATION STATUS
- owner_resolved: <true|false>
- github_account_ready: <true|false>
- repo_exists: <true|false>
- repo_created_this_turn: <true|false>
```

## Header contract
- `getGitBlob` and `createGitBlob`: `Accept: application/vnd.github.raw`
- All other calls that include `Accept`: `Accept: application/vnd.github+json`

## Architecture lock
- Use direct GitHub tool-call workflow only.
- Do not rely on Python store/sync/validation modules.
- Corpus writes are section-scoped updates within `CareerCorpus/corpus.md`.
