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
page_count = renderer.exceeds_one_page(markdown_text)

max_pages = 1  # set to 2 only for approved senior-scope resumes

if page_count > max_pages:
    # Do not export yet; return to editing and shorten content.
    ...
else:
    renderer.render(markdown_text, output_path)
```

## Page-length enforcement
- `renderer.exceeds_one_page(markdown_text)` now returns an integer page count.
- Set `max_pages` to:
  - `1` for default/mid-level roles
  - `2` only when senior scope is explicitly allowed
- If `page_count > max_pages`, do not export.
- Reduce content and re-check until `page_count <= max_pages`.

## Output requirements
- Format: A4 PDF.
- Page target: 1 page by default; up to 2 pages only for approved senior-scope roles.
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
