# FAQ

## Purpose
Use this file for meta questions about how this GPT works, what it can access, and how memory behavior is executed.
Do not use this file for resume drafting or corpus content policy.

## Common Questions

### How does this GPT decide what guidance to follow?
It routes user intent using `instructions.txt` and then references the specific knowledge files listed for that intent.

### What memory model is used?
A single uploaded markdown corpus file named `career_corpus.md` is used for session memory. Updated memory is returned as a downloadable `career_corpus.md`.

### What if corpus is missing?
JD analysis and resume drafting are blocked until the user uploads `career_corpus.md`.

### Does onboarding finalize incrementally?
No. Onboarding defaults to section-by-section approval, then generates one finalized downloadable corpus file after explicit approval.

### Can onboarding be reviewed all at once?
Yes, if the user chooses full-corpus review. In that mode, draft markdown is shown in canvas and approved before finalization.

### Where should I send users for behavior clarifications?
Use this FAQ for meta behavior.
Use `OnboardingGuidelines.md`, `InitializationGuidelines.md`, and `UATGuardrails.md` for operational rules.
