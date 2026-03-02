# CareerCorpus Markdown Format

## Objective
Provide a recommended markdown structure for section files under `CareerCorpus/`.

## Usage rules
- This is a formatting target, not a hard validator.
- Save one GitHub file per section.
- Do not save an empty file for any section.
- If a section has no data, omit that file.
- If a previously saved section becomes empty, delete that section file.

## Canonical section files
- `CareerCorpus/profile.md` (includes Profile + Skills)
- `CareerCorpus/experience.md`
- `CareerCorpus/projects.md`
- `CareerCorpus/certifications.md`
- `CareerCorpus/education.md`

## Do not persist
- No `CareerCorpus/metadata.md`.
- No `CareerCorpus/corpus.md` aggregate file.

## Section templates

### `CareerCorpus/profile.md`
```md
# Profile
- Full Name:
- Location:
- Email:
- Phone:

## Links
- Name (eg. GitHub): URL

## Skills
### Technical
- 

### Platforms
- 

### Methods
- 

### Domains
- 

## Notes
- 
```

### `CareerCorpus/experience.md`
```md
# Experience
## Experience Item
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

### Bullets
- 

### Outcomes
- 

### Notes
- 
```

### `CareerCorpus/projects.md`
```md
# Projects
## Project Item
- id:
- name:
- role:
- stack:
  - 
- description:

### Outcomes
- 

### Notes
- 
```

### `CareerCorpus/certifications.md`
```md
# Certifications
## Certification Item
- id:
- name:
- issuer:
- issue_date:
- status:
- notes:
```

### `CareerCorpus/education.md`
```md
# Education
## Education Item
- id:
- degree:
- institution:
- graduation_year:
- field_of_study:
- notes:
```

## Section order (recommended)
1. `profile.md`
2. `experience.md`
3. `projects.md`
4. `certifications.md`
5. `education.md`

## Legacy-schema alignment (best effort)
- Keep `Profile.full_name` populated when available.
- Keep `Skills` under `Profile` grouped as: technical, platforms, methods, domains.
- Keep repeatable item blocks for experience/projects/certifications/education.
- Do not store metadata as a corpus section; rely on Git history for persistence traceability.
