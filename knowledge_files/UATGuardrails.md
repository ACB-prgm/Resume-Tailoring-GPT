# UAT Guardrails

## Objective
Keep behavior deterministic for intent handling, corpus read/write, and failure reporting.

## Conversation gate
- If message is greeting/chitchat, reply briefly and stop.
- Do not run memory workflow unless user asks for resume/memory action.

## Read-before-claim
- Do not claim corpus state before running the direct read flow.
- If corpus file is missing, state that clearly and route to onboarding/import.

## Memory workflow contract
- Memory read/write uses direct GitHub Git Data calls only.
- Canonical remote file is `CareerCorpus/corpus.md`.
- Local mirror is `/mnt/data/CareerCorpus/corpus.md` and must be updated after successful read/write.

## Header contract
- `getGitBlob` and `createGitBlob`: `Accept: application/vnd.github.raw`
- All other calls that include `Accept`: `Accept: application/vnd.github+json`

## Truthfulness contract
- Only claim persistence success after successful `updateBranchRef`.
- Only claim corpus loaded after successful `getGitBlob` and local mirror update.
- On failure, return concise error and recovery step.

## Retry behavior
- One deterministic retry for retryable failures.
- If retry fails, stop and provide manual next steps.
