# Phase 1 - JD Analysis (Requirements-first)

## Objective
Treat the JD as a requirements document, not marketing copy. Extract constraints, weighted requirements, and the hiring risk model before writing resume content.

## Required workflow
1) Extract Binary Gates (eligibility/location/travel/degree/years/platforms/certs).  
Mark each gate as:
- Supported by corpus/current chat
- Exclude if not supported or unknown (do not claim)
- Only include gates that are explicitly present in the JD; omit unspecified gates from output.

2) Build Tiered keyword sets:
- Tier 1 Required keywords (ranked by explicit required language, repetition frequency, and presence across summary/responsibilities/qualifications)
- Tier 2 Preferred keywords (nice-to-have only)

3) Build 2-4 Core Skill Clusters (dominant themes).

4) Write one-sentence Core Need (why this role exists).

5) Create a Translation Map:
- JD Term -> equivalent supported evidence -> target placement (Summary / Core Competencies / Role bullets)

6) Run Recruiter Search Simulation:
- Build a recruiter-style Boolean query.
- Ensure Tier 1 tokens appear in:
  - Title line
  - Summary (2-4 lines)
  - Core Competencies
  - First 2-3 bullets in the most relevant role

7) Ask for resume drafting handoff:
- Ask: Would you like me to draft a tailored resume for this role now?
- If yes, route to `intent_resume_drafting` from `instructions.txt`.

## Rules
- Ignore company marketing/culture fluff.
- Prioritize hard constraints and literal requirements.
- Do not infer unsupported claims.
- If a requirement is not supported, flag it as a gap.
- In the Binary Gates section, omit any gate not explicitly specified in the JD.

## Standardized markdown output template (must be produced every run before resume writing)
- Output must be in markdown.
- Keep it concise and evidence-based.
- Use this structure:

```md
## JD Analysis Output

### Target Role
- Title(s):
- Seniority:
- Domain:

### Binary Gates
Include only gates explicitly specified in the JD. Omit all unspecified gates.
- Work authorization:
  - Status: Supported | Not supported/Unknown
  - Evidence:
- Location / hybrid:
  - Status: Supported | Not supported/Unknown
  - Evidence:
- Travel:
  - Status: Supported | Not supported/Unknown
  - Evidence:
- Degree:
  - Status: Supported | Not supported/Unknown
  - Evidence:
- Years of experience:
  - Status: Supported | Not supported/Unknown
  - Evidence:
- Platforms / tools:
  - Status: Supported | Not supported/Unknown
  - Evidence:
- Certifications:
  - Status: Supported | Not supported/Unknown
  - Evidence:

### Tier 1 Required Keywords (ranked)
1.
2.
3.

### Tier 2 Preferred Keywords
- 
- 

### Core Skill Clusters (2-4)
- Cluster 1:
- Cluster 2:

### Core Need (one sentence)
- 

### Translation Map
- JD term:
  - Equivalent evidence:
  - Placement: Summary | Core Competencies | Role bullets
- JD term:
  - Equivalent evidence:
  - Placement: Summary | Core Competencies | Role bullets

### Recruiter Search Simulation
- Boolean query:
- Tier 1 token coverage check:
  - Title line: Pass | Fail
  - Summary: Pass | Fail
  - Core Competencies: Pass | Fail
  - First 2-3 bullets in most relevant role: Pass | Fail

### Candidate Alignment to Role (concise, experience-based)
- Overall alignment: Strong | Moderate | Limited
- Experience alignment breakdown:
  - Requirement:
    - Supporting experience evidence:
    - Alignment status: Match | Partial | Gap
  - Requirement:
    - Supporting experience evidence:
    - Alignment status: Match | Partial | Gap
- Top gaps (if any):
  - Gap:
  - Gap:
```
