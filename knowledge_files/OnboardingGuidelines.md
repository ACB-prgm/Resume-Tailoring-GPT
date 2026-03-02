# Onboarding Guide

## Objective
Create initial career memory as markdown section files and persist them under `CareerCorpus/`.

## Phase order
1. Intro (once per session): purpose and storage model.
2. GitHub/auth gate: ensure account and auth readiness.
3. Intake: LinkedIn PDF/CV upload or manual entry.
4. Confirmation: user reviews section drafts.
5. Finalize: section-file write to GitHub and local mirror update.

## Intro content (concise)
- GPT purpose: tailor resumes using verified evidence.
- Onboarding purpose: establish private persistent storage in user GitHub.
- Corpus definition: reusable markdown section files.
- Intake options: upload LinkedIn PDF/CV or manual setup.

## GitHub gate
- If no GitHub account/auth, provide setup steps and pause.
- If ready, bootstrap repo before intake/write.

## Drafting and confirmation
- Build section drafts using `/mnt/data/CareerCorpusFormat.md`.
- Confirm section by section.
- Skills are always part of Profile section.
- No Metadata section.

## Finalize
1. Prepare section files in recommended order: profile, experience, projects, certifications, education.
2. Write one file per non-empty section under `CareerCorpus/`.
3. Skip empty sections; delete previously existing file if section is now empty.
4. On success, mirror updated files under `/mnt/data/CareerCorpus/`.

## Guardrails
- Do not invent missing details.
- If write fails, report failure and preserve local draft state.
