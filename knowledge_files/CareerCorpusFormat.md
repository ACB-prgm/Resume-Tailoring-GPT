# CareerCorpus Markdown Format

## Objective
Provide a recommended markdown structure for section files under `CareerCorpus/`.

## Usage rules
- This is a formatting target, not a hard validator.
- Save one GitHub file per section.
- Do not save an empty file for any section.
- If a section has no data, omit that file.
- If a previously saved section becomes empty, delete that section file.

## Section boundary contract (explicit)
- Treat each file as one numbered section boundary.
- Do not merge boundaries across files.
- Use this order for boundaries:
  1. `CareerCorpus/profile.md`
  2. `CareerCorpus/experience.md`
  3. `CareerCorpus/projects.md`
  4. `CareerCorpus/certifications.md`
  5. `CareerCorpus/education.md`
- Within each file, keep the numbered subsection headers so boundaries remain easy to parse.
- If a subsection has no content yet, keep the header and leave list items blank.

## Canonical section files
- `CareerCorpus/profile.md` (includes Profile + Skills)
- `CareerCorpus/experience.md`
- `CareerCorpus/projects.md`
- `CareerCorpus/certifications.md`
- `CareerCorpus/education.md`

## Do not persist
- No `CareerCorpus/metadata.md`.
- No `CareerCorpus/corpus.md` aggregate file.

## User preferences file (separate from corpus)
- Use top-level `preferences.md` for personal user preferences.
- `preferences.md` is free-form markdown (no strict schema/template).
- Only write `preferences.md` when user explicitly states a preference they want remembered.
- Do not create an empty `preferences.md`.

## Section templates

### `CareerCorpus/profile.md`
```md
<!-- START SECTION 1: PROFILE -->
# 1) Profile
- Full Name:
- Location:
- Email:
- Phone:

## 1.1) Links
- Name (eg. GitHub): URL

## 1.2) Skills
### 1.2.1) Technical
- 

### 1.2.2) Platforms
- 

### 1.2.3) Methods
- 

### 1.2.4) Domains
- 

## 1.3) Notes
- 
<!-- END SECTION 1: PROFILE -->
```

### `CareerCorpus/experience.md`
```md
<!-- START SECTION 2: EXPERIENCE -->
# 2) Experience
## 2.1) Experience Item
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

### 2.1.1) Bullets
- 

### 2.1.2) Outcomes
- 

### 2.1.3) Notes
- 
<!-- Repeat 2.1 blocks for additional experience items -->
<!-- END SECTION 2: EXPERIENCE -->
```

### `CareerCorpus/projects.md`
```md
<!-- START SECTION 3: PROJECTS -->
# 3) Projects
## 3.1) Project Item
- id:
- name:
- role:
- stack:
  - 
- description:

### 3.1.1) Outcomes
- 

### 3.1.2) Notes
- 
<!-- Repeat 3.1 blocks for additional project items -->
<!-- END SECTION 3: PROJECTS -->
```

### `CareerCorpus/certifications.md`
```md
<!-- START SECTION 4: CERTIFICATIONS -->
# 4) Certifications
## 4.1) Certification Item
- id:
- name:
- issuer:
- issue_date:
- status:
- notes:
<!-- Repeat 4.1 blocks for additional certification items -->
<!-- END SECTION 4: CERTIFICATIONS -->
```

### `CareerCorpus/education.md`
```md
<!-- START SECTION 5: EDUCATION -->
# 5) Education
## 5.1) Education Item
- id:
- degree:
- institution:
- graduation_year:
- field_of_study:
- notes:
<!-- Repeat 5.1 blocks for additional education items -->
<!-- END SECTION 5: EDUCATION -->
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
