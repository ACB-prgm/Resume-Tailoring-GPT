# Initialization Guide

## Objective
Run a deterministic startup sequence before any memory read/write so repo bootstrap, store/sync setup, and status reporting are unambiguous.

## Mandatory startup order
1. Add `/mnt/data` to `sys.path` before imports.
2. Resolve owner via `getAuthenticatedUser`.
3. Call `getMemoryRepo(owner)` exactly once.
4. If `404`, call `createMemoryRepo` exactly once.
5. Call `getMemoryRepo(owner)` one final time to confirm.
6. Instantiate:
   - `CareerCorpusStore(path="/mnt/data/career_corpus.json", meta_path="/mnt/data/career_corpus.meta.json")`
   - `CareerCorpusSync(...)`
7. Emit `INITIALIZATION STATUS` and continue only if `repo_exists=true`.

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
- repo_exists: <true|false>
- repo_created_this_turn: <true|false>
- repo_create_attempted_this_turn: <true|false>
- store_initialized: <true|false>
- sync_initialized: <true|false>
```

## Architecture lock
- No direct Git writes before store/sync bootstrap completes.
- All writes must flow: `load -> pull_if_stale_before_write -> in-memory update -> validate -> push`.
