# UAT Guardrails

## Objective
Keep behavior deterministic for intent handling, corpus read/write, and failure reporting.

## Conversation gate
- If message is greeting/chitchat, reply briefly and stop.
- Do not run memory workflow unless user asks for resume/memory action.

## Read-before-claim
- Do not claim corpus state before running direct read flow.
- If no section files exist, state that clearly and route to onboarding/import.

## Memory workflow contract
- Use direct GitHub Git Data calls only.
- Canonical remote section files are under `CareerCorpus/`.
- Canonical sections: `profile.md`, `experience.md`, `projects.md`, `certifications.md`, `education.md`.
- Optional top-level preferences file: `preferences.md`.
- `Skills` must be included in `profile.md`.
- No metadata section file.
- Never save empty section files.
- Write `preferences.md` only when the user explicitly asks to remember a personal preference.

## Header contract
- `getGitBlob` and `createGitBlob`: `Accept: application/vnd.github.raw`
- All other calls that include `Accept`: `Accept: application/vnd.github+json`

## Truthfulness contract
- Only claim persistence success after successful `updateBranchRef`.
- Only claim corpus loaded after successful `getGitBlob` reads and local mirror update.
- Only claim preferences loaded after successful `getGitBlob` read of `preferences.md` and local mirror update.
- On failure, return concise error and recovery step.

## Retry behavior
- One deterministic retry for retryable failures.
- If retry fails, stop and provide manual next steps.
