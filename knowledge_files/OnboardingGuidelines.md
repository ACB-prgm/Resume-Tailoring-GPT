# Onboarding Guide

## Objective
Create initial career memory as markdown and persist it to `CareerCorpus/corpus.md`.

## Phase order
1. Intro (once per session): purpose and storage model.
2. GitHub/auth gate: ensure account and auth readiness.
3. Intake: LinkedIn PDF/CV upload or manual entry.
4. Confirmation: user reviews corpus draft.
5. Finalize: single write to remote corpus file and local mirror update.

## Intro content (concise)
- GPT purpose: tailor resumes using verified evidence.
- Onboarding purpose: establish private persistent memory in user GitHub.
- Corpus definition: reusable markdown evidence document.
- Intake options: upload LinkedIn PDF/CV or manual setup.

## GitHub gate
- If no GitHub account/auth, provide setup steps and pause.
- If ready, bootstrap repo before intake/write.

## Drafting and confirmation
- Build one markdown corpus draft.
- Present readable markdown preview.
- Apply user corrections before final write.

## Finalize
1. Write `CareerCorpus/corpus.md` via Git Data flow.
2. On success, overwrite `/mnt/data/CareerCorpus/corpus.md`.
3. Mark onboarding completion inside corpus content (frontmatter or explicit metadata section).

## Guardrails
- Do not invent missing details.
- If corpus write fails, do not mark onboarding complete.
