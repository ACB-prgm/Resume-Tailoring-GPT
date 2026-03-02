# Memory State Model

## Objective
Keep memory state decisions simple and explicit for markdown section-file memory.

## Required booleans
- `memory_repo_exists`: GH tool call has been used to confirm existence of memory repo.
- `corpus_exists`: at least one canonical non-empty section file exists remotely.
- `corpus_loaded`: The corpus has been fetched from GH and stored locally.
- `preferences_exists`: top-level `preferences.md` exists remotely.
- `preferences_loaded`: `preferences.md` has been fetched and mirrored locally.

## States
- `NO_REPO`: repo missing.
- `REPO_NO_CORPUS`: repo exists, no section files present.
- `CORPUS_READY`: repo and one or more canonical section files exist.
- `PERSIST_FAILED`: write failed after retry.

## Required memory status plain text code block
- KEY: ✅ = true, ❌ = false
```text
MEMORY STATUS
- memory_repo_exists: <✅|❌>
- corpus_exists: <✅|❌>
- corpus_loaded: <✅|❌>
- preferences_exists: <✅|❌>
- preferences_loaded: <✅|❌>
- last_written: <timestamp (%m/%d/%y %I:%M %p Local time)| Unknown | Never>
```

## Status display policy
- Show status only when requested, when state changes, or when a memory operation fails.
- `last_written` comes from the most recent successful write operation.
