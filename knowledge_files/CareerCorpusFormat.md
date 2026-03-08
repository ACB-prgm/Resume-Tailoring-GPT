# Career Corpus Markdown Format

## Objective
Provide a recommended markdown structure for a single corpus file: `career_corpus.md`.

## Usage rules
- This is a formatting target, not a hard validator.
- Keep all corpus content in one file: `career_corpus.md`.
- Keep explicit numbered section boundaries.
- If a section has no data, keep the section header and leave placeholders blank.

## Section boundary contract (explicit)
Use this exact section order in `career_corpus.md`:
1. Profile (includes Skills)
2. Experience
3. Projects
4. Certifications
5. Education
6. Preferences (optional)

## `career_corpus.md` template
```md
<!-- START SECTION 1: PROFILE -->
# 1) Profile
- Full Name:
- Location:
- Email:
- Phone:

## 1.1) Links
- Name: URL

## 1.2) Skills
### 1.2.1) Technical
- 

### 1.2.2) Platforms
- 

### 1.2.3) Domains
- 

## 1.3) Notes
- 
<!-- END SECTION 1: PROFILE -->

<!-- START SECTION 2: EXPERIENCE -->
# 2) Experience
## 2.1) Experience Title
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

<!-- START SECTION 3: PROJECTS -->
# 3) Projects
## 3.1) Project Title
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

<!-- START SECTION 4: CERTIFICATIONS -->
# 4) Certifications
## 4.1) Certification Title
- issuer:
- issue_date:
- status:
- url:
- notes:
<!-- Repeat 4.1 blocks for additional certification items -->
<!-- END SECTION 4: CERTIFICATIONS -->

<!-- START SECTION 5: EDUCATION -->
# 5) Education
## 5.1) Education Title
- degree:
- institution:
- graduation_year:
- field_of_study:
- notes:
<!-- Repeat 5.1 blocks for additional education items -->
<!-- END SECTION 5: EDUCATION -->

<!-- START SECTION 6: PREFERENCES -->
# 6) Preferences (Optional)
- Resume preferences:
- Role preferences:
- Communication preferences:
- Notes:
<!-- END SECTION 6: PREFERENCES -->
```
