# Initialization Guide

## Objective
Run a deterministic startup sequence before any memory read/write so repo bootstrap, store/sync setup, and status reporting are unambiguous.

## Mandatory startup order
1. Add `/mnt/data` to `sys.path` before imports.
2. Confirm GitHub account/auth readiness (`github_account_ready`).
3. Resolve owner via `getAuthenticatedUser`.
4. Call `getMemoryRepo(owner)` exactly once.
5. If `404`, call `createMemoryRepo` exactly once.
6. Call `getMemoryRepo(owner)` one final time to confirm.
7. Instantiate:
   - `CareerCorpusStore(path="/mnt/data/career_corpus.json", meta_path="/mnt/data/career_corpus.meta.json")`
   - `CareerCorpusSync(...)`
8. Emit `INITIALIZATION STATUS` and continue only if `github_account_ready=true` and `repo_exists=true`.

## No-GitHub branch (hard gate)
- If `github_account_ready=false`, do not proceed with memory bootstrap/write steps.
- Provide concise setup instructions and pause:
  1. Create account: `https://github.com/signup`.
  2. Verify account and sign in.
  3. Return to continue authentication and memory setup.
- Stop condition: wait for user confirmation that GitHub account/auth is ready.

## Surface-only import rule
- Import memory runtime APIs from:
  - `/mnt/data/career_corpus_store_surface.py`
  - `/mnt/data/career_corpus_sync_surface.py`
  - `/mnt/data/memory_validation_surface.py`
- Treat `*_core.py` modules as internal implementation; do not call them directly from GPT workflow steps.

## Deterministic repo bootstrap rule
- Required sequence: `get -> (optional create) -> get_confirm`.
- Use turn guard `repo_create_attempted_this_turn`.
- Never call `createMemoryRepo` twice in the same turn.

## GitHub Accept header contract (memory operations)
- During setup-adjacent memory API calls:
  - `getGitBlob` and `createGitBlob`: `Accept: application/vnd.github.raw`
  - All other calls that include an `Accept` header: `Accept: application/vnd.github+json`
- Apply this map even when schema `const` constraints are missing or ignored.

## Required initialization status block
```text
INITIALIZATION STATUS
- owner_resolved: <true|false>
- github_account_ready: <true|false>
- repo_exists: <true|false>
- repo_created_this_turn: <true|false>
- repo_create_attempted_this_turn: <true|false>
- store_initialized: <true|false>
- sync_initialized: <true|false>
```

## Architecture lock
- No direct Git writes before store/sync bootstrap completes.
- All writes must flow: `load -> pull_if_stale_before_write -> in-memory update -> validate -> push`.
