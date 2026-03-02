# CareerCorpus Markdown Format

## Objective
Provide a recommended markdown structure for `CareerCorpus/corpus.md` that mirrors the legacy JSON schema shape without hard validation.

## Usage rules
- This is a format target, not a strict validator.
- Writes should follow this section order as closely as possible.
- Section-scoped updates should replace only targeted sections and preserve untouched sections.
- If the file is missing, initialize from this format skeleton.

## Recommended document skeleton

```md
---
schema_version: "1.0.0"
last_updated_utc: "<ISO-8601 UTC>"
source: "onboarding|user_update|manual_import"
onboarding_complete: false
onboarding_completed_utc: null
---

# Career Corpus

## Profile
- Full Name:
- Location:
- Email:
- Phone:

### Links
| Name | URL |
|---|---|
| LinkedIn | |
| GitHub | |

### Notes
- 

## Skills
### Technical
- 

### Platforms
- 

### Methods
- 

### Domains
- 

### Notes
- 

## Experience
### Experience Item
- id:
- employer:
- title:
- start_date:
- end_date:
- location:
- tools:
  - 
- domain_tags:
  - 

#### Bullets
- 

#### Outcomes
- 

#### Notes
- 

## Projects
### Project Item
- id:
- name:
- role:
- stack:
  - 
- description:

#### Outcomes
- 

#### Notes
- 

## Certifications
### Certification Item
- id:
- name:
- issuer:
- issue_date:
- status:
- notes:

## Education
### Education Item
- id:
- degree:
- institution:
- graduation_year:
- field_of_study:
- notes:

## Metadata
- last_updated_utc:
- source:
- onboarding_complete:
- onboarding_completed_utc:
```

## Section order (recommended)
1. `Profile`
2. `Skills`
3. `Experience`
4. `Projects`
5. `Certifications`
6. `Education`
7. `Metadata`

## Field guidance by legacy schema
- Keep `Profile.full_name` populated whenever available.
- Keep `Skills` grouped under: technical, platforms, methods, domains.
- Keep each experience/project/certification/education entry as a repeatable item block.
- Keep onboarding and update provenance in frontmatter and/or `Metadata` section.

