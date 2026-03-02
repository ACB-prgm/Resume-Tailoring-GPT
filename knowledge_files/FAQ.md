# FAQ

## Purpose
Use this file for meta questions about how this GPT works, what it can access, and how memory behavior is executed.  
Do not use this file for resume drafting or corpus content policy.

## Repository
- Source repository: https://github.com/ACB-prgm/Resume-Tailoring-GPT/tree/main

## Common Questions

### How does this GPT decide what guidance to follow?
It routes user intent using `instructions.txt` and then references the specific knowledge files listed for that intent.

### Can this GPT read tool-layer schema files directly?
No. Tool-layer definitions are not read as normal knowledge files during response generation.  
Use "github tool call" instructions in `instructions.txt` and the relevant knowledge guides.

### What memory model is used?
Markdown section files in GitHub under `CareerCorpus/`, plus optional top-level `preferences.md` when explicitly requested by the user.

### Does onboarding push immediately?
No. Onboarding defaults to section-by-section approval, with one final push only after explicit approval.

### Can onboarding be reviewed all at once?
Yes, if the user chooses full-corpus review. In that mode, draft markdown should be shown in canvas and approved before final push.

### Where should I send users for system behavior clarifications?
Use this FAQ for meta behavior.  
Use `OnboardingGuidelines.md`, `MemoryPersistenceGuidelines.md`, `InitializationGuidelines.md`, and `UATGuardrails.md` for operational rules.

