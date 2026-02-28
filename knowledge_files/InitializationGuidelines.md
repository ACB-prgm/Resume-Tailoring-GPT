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

## Deterministic repo bootstrap rule
- Required sequence: `get -> (optional create) -> get_confirm`.
- Use turn guard `repo_create_attempted_this_turn`.
- Never call `createMemoryRepo` twice in the same turn.

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
