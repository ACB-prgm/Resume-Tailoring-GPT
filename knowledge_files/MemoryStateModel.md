# Memory State Model

## Objective
Make memory bootstrap and persistence decisions explicit and auditable.

## Required booleans
- `memory_repo_exists`
- `career_corpus_exists` (manifest `corpus_index.json` for split model, or legacy corpus file)
- `onboarding_complete` (required sections approved + validated + persisted)

## States
- `NO_REPO`: `memory_repo_exists=false`, `career_corpus_exists=false`
- `REPO_NO_CORPUS`: `memory_repo_exists=true`, `career_corpus_exists=false`
- `CORPUS_PARTIAL`: `memory_repo_exists=true`, `career_corpus_exists=true`, `onboarding_complete=false`
- `CORPUS_READY`: `memory_repo_exists=true`, `career_corpus_exists=true`, `onboarding_complete=true`, and schema-valid
- `CORPUS_INVALID`: corpus exists but JSON/schema invalid
- `PERSIST_FAILED`: write attempt failed after retry policy

## Required status block
```text
MEMORY STATUS
- repo_exists: <true|false>
- corpus_exists: <true|false>
- onboarding_complete: <true|false>
- validated: <true|false>
- persisted: <true|false>
- fallback_used: <true|false>
- method: <git_blob_utf8|...>
- retry_count: <0|1>
- verification: <ok|failed|not_run>
```

## Status display policy
- Do not show memory status on every turn.
- Show `MEMORY STATUS` only when:
  - user explicitly asks for memory status
  - status has changed since last shown state
  - a memory operation fails
- When shown, render as a compact plain-text code block.

## Transition rules
- `NO_REPO -> REPO_NO_CORPUS`: create fixed repo `career-corpus-memory`.
- `REPO_NO_CORPUS -> CORPUS_PARTIAL`: onboarding started with partial section approvals.
- `CORPUS_PARTIAL -> CORPUS_READY`: all required sections approved + validated + persisted.
- `CORPUS_READY -> PERSIST_FAILED`: write fails after preflight + one retry.
- `CORPUS_INVALID -> REPO_NO_CORPUS`: treat as unavailable corpus and route to repair/onboarding.
- `PERSIST_FAILED -> CORPUS_READY`: only after successful corrected upsert.
