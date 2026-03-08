# Initialization Guide

## Objective
Run deterministic startup for session-based corpus upload/download workflows.

## Required initialization flow
1. Confirm whether `career_corpus.md` is already uploaded in the current session.
2. If missing, request upload before any corpus-dependent workflow.
3. If uploaded, confirm the file is readable markdown.
4. Parse section boundaries using `/mnt/data/CareerCorpusFormat.md`.
5. Confirm presence/absence of core sections for the active intent.
6. Set session state to ready when parse succeeds.
7. If parse fails, run one deterministic retry, then return clear recovery instructions.

## Missing-corpus branch
- If the user asks for JD analysis or resume drafting without corpus upload:
  - stop the workflow,
  - request `career_corpus.md` upload,
  - resume only after upload succeeds.

## Rules
- Use upload/download flow only.
- Keep initialization focused on corpus readiness and section discovery.
- Preferences are handled only as the optional Preferences section inside `career_corpus.md`.
