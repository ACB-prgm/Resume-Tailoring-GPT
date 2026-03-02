# Memory State Model

## Objective
Keep memory state decisions simple and explicit for markdown memory.

## Required booleans
- `memory_repo_exists`
- `career_corpus_exists` (`CareerCorpus/corpus.md` exists remotely)
- `onboarding_complete` (stored inside `CareerCorpus/corpus.md`)

## States
- `NO_REPO`: repo missing.
- `REPO_NO_CORPUS`: repo exists, corpus file missing.
- `CORPUS_READY`: repo and corpus file exist.
- `PERSIST_FAILED`: write failed after retry.

## Required status block
```text
MEMORY STATUS
- repo_exists: <true|false>
- corpus_exists: <true|false>
- onboarding_complete: <true|false>
- last_written: <friendly timestamp | Never>
```

## Optional fields (show only when relevant)
- `persisted`
- `retry_count`
- `method`

## Status display policy
- Show status only when requested, when state changes, or when a memory operation fails.
- `last_written` comes from the most recent successful write to `CareerCorpus/corpus.md`.
- Corpus content should follow `/mnt/data/CareerCorpusFormat.md` section order when possible.
