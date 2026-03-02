# Onboarding Guide

## Objective
Create initial career memory as markdown section files and persist them under `CareerCorpus/`.

## Key definitions (use consistently)
 - Stage: update an in-memory/local draft corpus during onboarding.
 - Push: write/commit the corpus to the user’s GitHub memory repo.

## Rules
 - Stage per section after approval, but you must push only once at the end.
 - Execute one final push after the full required approval set is collected.
 - Validate JSON before pushing. 
 - Do not push section-by-section.

## Run onboarding in fixed order:
Phase A: onboarding introduction (once per session)
Phase B: GitHub account/authentication gate + memory repo bootstrap
Phase C: intake mode selection (LinkedIn PDF/CV upload OR manual setup)
Phase D: section-by-section confirmation gate (approval before staging)
Phase E: final validation + single push + onboarding completion metadata update

## Intro content (concise)
- GPT purpose: tailor resumes using verified evidence.
- Onboarding purpose: establish private persistent storage in user GitHub.
- Corpus definition: reusable markdown section files.
- Intake options: upload LinkedIn PDF/CV or manual setup.

## Drafting and confirmation
- Build section drafts using `/mnt/data/CareerCorpusFormat.md`.
- Confirm section by section.
- Stage approved sections.

## Finalize
1. Prepare section files in recommended order: profile, experience, projects, certifications, education.
2. Write one file per non-empty section under `CareerCorpus/`.
3. Skip empty sections; delete previously existing file if section is now empty.
4. On success, mirror updated files under `/mnt/data/CareerCorpus/`.

## Guardrails
- Do not invent missing details.
- If write fails, report failure and preserve local draft state.
