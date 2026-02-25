# PDF Export Guide

## Objective
Generate the final PDF from approved markdown without changing approved content.

## Preconditions
- User has confirmed final markdown draft in canvas.
- Markdown is frozen for export.

## Required export pipeline
```python
import sys
sys.path.append("/mnt/data")
from resume_renderer import ResumeRenderer
from resume_theme import ResumeTheme

theme = ResumeTheme()
renderer = ResumeRenderer(theme)

if renderer.exceeds_one_page(markdown_text):
    # Do not export yet; return to editing and shorten content.
    ...
else:
    renderer.render(markdown_text, output_path)
```

## Page-length enforcement
- `renderer.exceeds_one_page(markdown_text)` must run before export.
- If `True`, do not export.
- Reduce content and re-check until it returns `False`.

## Output requirements
- Format: single-page A4 PDF.
- ATS-safe: no tables/columns/decorative layouts that hide critical text.
- File naming:
  - `Aaron Bastian Resume - <TargetRole> - <CompanyIfKnown>.pdf`
  - If company unknown: `Aaron Bastian Resume - <TargetRole>.pdf`
- Attach only the PDF artifact.
- Include a brief Change Log in chat:
  - Top targeted keywords
  - Roles/projects emphasized
  - Exclusions due to missing evidence
  - Explicit assumptions (ideally none)

## Guardrails
- Do not regenerate or rewrite resume content during export.
- If page length fails, return to drafting stage and edit content first.
