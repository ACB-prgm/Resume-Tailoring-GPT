# Memory State Model

## Objective
Keep memory state decisions simple and explicit for remote-only markdown section-file memory.

## Required booleans
- `memory_repo_exists`: GH tool call has been used to confirm existence of memory repo.
- `corpus_exists`: at least one canonical non-empty section file exists remotely.
- `preferences_exists`: top-level `preferences.md` exists remotely.

## Required status fields
- `last_written`: timestamp of most recent successful write operation.
- `last_remote_read_utc`: timestamp of most recent successful remote blob read.
- `last_remote_read_scope`: optional list/string of sections read in the most recent remote read.

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
- preferences_exists: <✅|❌>
- last_written: <timestamp (%m/%d/%y %I:%M %p Local time)| Unknown | Never>
- last_remote_read_utc: <timestamp (%m/%d/%y %I:%M %p Local time)| Unknown | Never>
```

## Status display policy
- Show status only when requested, when state changes, or when a memory operation fails.
- Required status output: `memory_repo_exists`, `corpus_exists`, `preferences_exists`, `last_written`.
- Optional fields when relevant: `last_remote_read_utc`, `last_remote_read_scope`, `persisted`, `retry_count`, `verification`.
