# Memory State Model

## Objective
Keep memory state decisions simple and explicit for markdown section-file memory.

## Required booleans
- `memory_repo_exists`
- `career_corpus_exists` (at least one canonical non-empty section file exists remotely)

## States
- `NO_REPO`: repo missing.
- `REPO_NO_CORPUS`: repo exists, no section files present.
- `CORPUS_READY`: repo and one or more canonical section files exist.
- `PERSIST_FAILED`: write failed after retry.

## Required status block
```text
MEMORY STATUS
- repo_exists: <true|false>
- corpus_exists: <true|false>
- sections_present: <comma-separated section files | none>
- last_written: <friendly timestamp | Never>
```

## Optional fields (show only when relevant)
- `persisted`
- `retry_count`
- `method`

## Status display policy
- Show status only when requested, when state changes, or when a memory operation fails.
- `last_written` comes from the most recent successful write operation.
