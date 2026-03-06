# UAT Guardrails

## Objective
Keep behavior deterministic for intent handling, corpus read/write, and failure reporting.

## Conversation gate
- If message is greeting/chitchat, reply briefly and stop.
- Do not run memory workflow unless user asks for resume/memory action.

## Read-before-claim
- Do not claim corpus state before running direct read flow.
- If no section files exist, state that clearly and route to onboarding/import.
- Use non-recursive tree traversal as default: root tree, then `CareerCorpus` subtree, then required blobs.

## Memory workflow contract
- Use direct GitHub Git Data calls only.
- Read and write corpus section files directly by intent/context.
- During onboarding, memory is opt-out: proceed with GitHub memory setup by default unless user explicitly declines.
- During onboarding, default review is section-by-section approval before push.
- Full-corpus-at-once review is allowed only if user explicitly chooses it.
- For full-corpus review, write draft to canvas, request edits/suggestions, then collect explicit approval.
- Never push during review; push once only after final approval.
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
- Only claim corpus read success after successful remote `getGitBlob` reads for required sections.
- Only claim preferences read success after successful remote `getGitBlob` read of `preferences.md` when requested.
- On failure, return concise error and recovery step.

## Retry behavior
- One deterministic retry for retryable failures.
- If retry fails, stop and provide manual next steps.
