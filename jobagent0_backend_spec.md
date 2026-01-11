# JobAgent0 Backend Specification

## Project Overview

JobAgent0 is an AI-powered job application automation system that generates tailored resumes and cover letters. The backend receives a user's profile data (`profile.json`) and a job posting, then produces customized application documents with perfect formatting.

The system uses a multi-flow architecture where parallel processes gather intelligence about the job and company, analyze profile-job fit, and generate tailored documents by injecting AI-generated content into LaTeX templates.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INPUT LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  profile.json (user data)          DOM/HTML (job posting from extension)    │
└─────────────────┬───────────────────────────────┬───────────────────────────┘
                  │                               │
                  │                               ▼
                  │                    ┌─────────────────────┐
                  │                    │    MAIN FLOW 1      │
                  │                    │   Job Extraction    │
                  │                    │  (Gemini Flash)     │
                  │                    └──────────┬──────────┘
                  │                               │
                  │                               ▼
                  │                          job.json
                  │                               │
                  ├───────────────┬───────────────┼───────────────┐
                  │               │               │               │
                  ▼               ▼               ▼               ▼
         ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
         │ MAIN FLOW 2  │ │ LITE FLOW 1  │ │              │
         │   Profile    │ │   Company    │ │              │
         │  Matching    │ │  Research    │ │              │
         │ (Hybrid ML)  │ │(Web + Flash) │ │              │
         └──────┬───────┘ └──────┬───────┘ │              │
                │                │         │              │
                ▼                ▼         │              │
    profile_matching.json  company_summary.json           │
                │                │         │              │
                └────────┬───────┴─────────┘              │
                         │                                │
          ┌──────────────┴──────────────┐                 │
          │                             │                 │
          ▼                             ▼                 │
┌─────────────────────┐      ┌─────────────────────┐     │
│    MAIN FLOW 3      │      │    LITE FLOW 2      │     │
│  Resume Generation  │      │  Cover Letter Gen   │     │
│   (Multi-Pass)      │      │   (Multi-Pass)      │     │
└──────────┬──────────┘      └──────────┬──────────┘     │
           │                            │                 │
           ▼                            ▼                 │
  resume_components.json    cover_letter_components.json  │
           │                            │                 │
           ▼                            ▼                 │
      resume.tex               cover_letter.tex           │
           │                            │                 │
           ▼                            ▼                 │
      resume.pdf               cover_letter.pdf           │
           │                            │                 │
           └────────────────────────────┘                 │
                         │                                │
                         ▼                                │
              ┌─────────────────────┐                     │
              │    OUTPUT LAYER     │                     │
              │  Final Documents    │                     │
              └─────────────────────┘                     │
```

---

## Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entry point
│   ├── config.py                   # Environment variables, API keys, model configs
│   │
│   ├── models/                     # Pydantic schemas for all data structures
│   │   ├── __init__.py
│   │   ├── job.py                  # JobSchema
│   │   ├── profile.py              # ProfileSchema (input validation)
│   │   ├── matching.py             # ProfileMatchingSchema
│   │   ├── company.py              # CompanySummarySchema
│   │   ├── resume.py               # ResumeComponentsSchema
│   │   └── cover_letter.py         # CoverLetterComponentsSchema
│   │
│   ├── services/                   # Core business logic
│   │   ├── __init__.py
│   │   ├── job_extractor.py        # Main Flow 1: DOM → job.json
│   │   ├── profile_matcher.py      # Main Flow 2: profile + job → matching analysis
│   │   ├── company_researcher.py   # Lite Flow 1: company research → summary
│   │   ├── resume_generator.py     # Main Flow 3: multi-pass resume generation
│   │   ├── cover_letter_generator.py  # Lite Flow 2: cover letter generation
│   │   └── llm_client.py           # Gemini API wrapper (Flash + Pro)
│   │
│   ├── templates/                  # LaTeX templates
│   │   ├── jake_resume.tex         # Base resume template with placeholders
│   │   └── cover_letter.tex        # Cover letter template
│   │
│   └── utils/                      # Utility functions
│       ├── __init__.py
│       ├── keyword_extractor.py    # TF-IDF, KeyBERT wrapper
│       ├── fuzzy_matcher.py        # RapidFuzz wrapper for skill matching
│       ├── semantic_matcher.py     # Sentence transformers for similarity
│       ├── latex_compiler.py       # Template injection + pdflatex
│       └── web_search.py           # Search API wrapper
│
├── data/                           # Runtime data storage
│   ├── jobs/                       # job.json files (per application)
│   ├── matching/                   # profile_matching.json files
│   ├── companies/                  # company_summary.json (cached)
│   └── outputs/                    # Generated PDFs
│
├── tests/
│   ├── __init__.py
│   ├── test_job_extractor.py
│   ├── test_profile_matcher.py
│   ├── test_resume_generator.py
│   └── fixtures/                   # Sample profile.json, DOM samples
│
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## Data Schemas

### 1. Input: profile.json

This file contains the user's complete professional profile, scraped or manually entered. The backend receives this as input and uses it throughout all flows.

```python
from pydantic import BaseModel, HttpUrl, EmailStr
from typing import Optional

class Project(BaseModel):
    name: str
    organization: Optional[str] = None
    date_range: str  # e.g., "Jan 2024 - Present"
    technologies: list[str]
    bullets: list[str]  # Original bullet points
    link: Optional[HttpUrl] = None

class WorkExperience(BaseModel):
    company: str
    title: str
    location: str
    date_range: str
    bullets: list[str]

class Education(BaseModel):
    institution: str
    degree: str
    date_range: str
    gpa: Optional[str] = None
    relevant_coursework: Optional[list[str]] = None

class Involvement(BaseModel):
    organization: Optional[str]
    role: Optional[str]
    date_range: str
    bullets: list[str]

class ProfileSchema(BaseModel):
    # Contact Information
    name: str
    email: EmailStr
    phone: str
    location: str
    github: Optional[HttpUrl] = None
    linkedin: Optional[HttpUrl] = None
    portfolio: Optional[HttpUrl] = None
    
    # Professional Summary (optional, may be generated)
    summary: Optional[str] = None
    
    # Skills
    programming_languages: list[str]
    frameworks_libraries: list[str]
    tools_platforms: list[str]
    soft_skills: Optional[list[str]] = None
    
    # Experience
    work_experience: Optional[list[WorkExperience]] = None
    projects: list[Project]
    education: Education
    involvements: Optional[list[Involvement]] = None
    certifications: Optional[list[str]] = None
```

---

### 2. job.json (Output of Main Flow 1)

```python
class JobSchema(BaseModel):
    company_name: str
    job_title: str
    job_description: str  # Full text of the job posting
    req_id: Optional[str] = None
    location: Optional[str] = None
    required_skills: list[str]  # Extracted and normalized
    preferred_skills: list[str]  # Extracted and normalized
```

**Example:**
```json
{
    "company_name": "Stripe",
    "job_title": "Software Engineer, Backend",
    "job_description": "We're looking for backend engineers to help build the economic infrastructure for the internet...",
    "req_id": "R-2024-1234",
    "location": "San Francisco, CA (Remote eligible)",
    "required_skills": ["Python", "Go", "SQL", "REST APIs", "Distributed Systems"],
    "preferred_skills": ["Kubernetes", "AWS", "gRPC", "Redis"]
}
```

---

### 3. profile_matching_data.json (Output of Main Flow 2)

```python
class ProjectRelevance(BaseModel):
    project_name: str
    relevance_score: float  # 0.0 to 1.0
    matching_keywords: list[str]
    recommended: bool  # True for top 2-3 projects

class RankedSkills(BaseModel):
    languages: list[str]  # Ordered by relevance to job
    frameworks: list[str]
    tools: list[str]

class TailoringSuggestions(BaseModel):
    keywords_to_incorporate: list[str]  # For bullet rewriting
    emphasis_areas: list[str]  # e.g., "backend development", "API design"

class KeywordMatch(BaseModel):
    matched_required: list[str]
    matched_preferred: list[str]
    missing_critical: list[str]  # Required skills not found in profile

class ProfileMatchingSchema(BaseModel):
    overall_match_score: float  # 0-100, for user feedback
    keyword_match: KeywordMatch
    ranked_projects: list[ProjectRelevance]
    ranked_skills: RankedSkills
    tailoring_suggestions: TailoringSuggestions
```

**Example:**
```json
{
    "overall_match_score": 78.5,
    "keyword_match": {
        "matched_required": ["Python", "REST APIs", "SQL"],
        "matched_preferred": ["AWS", "Redis"],
        "missing_critical": ["Go", "Distributed Systems"]
    },
    "ranked_projects": [
        {
            "project_name": "SignalFence",
            "relevance_score": 0.92,
            "matching_keywords": ["Go", "rate limiting", "production-grade"],
            "recommended": true
        },
        {
            "project_name": "JobAgent0",
            "relevance_score": 0.85,
            "matching_keywords": ["Python", "APIs", "automation"],
            "recommended": true
        }
    ],
    "ranked_skills": {
        "languages": ["Python", "Go", "TypeScript", "SQL", "JavaScript"],
        "frameworks": ["FastAPI", "React", "Flask", "Django", "Next.js"],
        "tools": ["AWS", "Docker", "Redis", "PostgreSQL", "Git"]
    },
    "tailoring_suggestions": {
        "keywords_to_incorporate": ["scalable", "distributed", "microservices", "API design"],
        "emphasis_areas": ["backend architecture", "system design", "performance optimization"]
    }
}
```

---

### 4. company_summary.json (Output of Lite Flow 1)

```python
class CompanySummarySchema(BaseModel):
    company_name: str
    industry: str
    mission_or_values: Optional[str] = None  # Consolidated statement
    culture_keywords: list[str]  # 3-5 descriptors: "collaborative", "fast-paced"
    recent_highlight: Optional[str] = None  # One notable fact for cover letter
    tone: str  # "formal" | "conversational" | "startup"
```

**Example:**
```json
{
    "company_name": "Stripe",
    "industry": "Financial Technology / Payments",
    "mission_or_values": "Increase the GDP of the internet by building economic infrastructure that helps businesses of all sizes accept payments and manage their operations online.",
    "culture_keywords": ["rigorous", "user-focused", "long-term thinking", "transparent"],
    "recent_highlight": "Launched Stripe Climate, allowing businesses to direct a fraction of revenue to carbon removal.",
    "tone": "conversational"
}
```

---

### 5. resume_components.json (Output of Main Flow 3)

```python
class RewrittenProject(BaseModel):
    name: str
    organization: Optional[str] = None #Skip if it is a personal project
    date_range: str
    technologies: str  # Comma-separated, ordered by relevance
    bullets: list[str]  # Rewritten bullets
    link: Optional[str] = None

class RewrittenExperience(BaseModel):
    company: str
    title: str
    location: str
    date_range: str
    bullets: list[str]  # Rewritten bullets

class ResumeComponentsSchema(BaseModel):
    # Header
    name: str
    phone: str
    email: str
    github: str  # Just username or full URL
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    location: str
    
    # Tailored Summary
    profile_summary: str  # 2-3 sentences, customized to job
    
    # Skills (ordered by job relevance)
    technical_skills: dict{<<key>>:list[str]} 
    '''
    We will use a dictionary here because we can provide labels to skills according to job descriptions. Store the labels as <<key>> and the skills related to the label as a list of skills (str). 

    Example: 
    Programming Languages: Python, C/C++, JavaScript/TypeScript, SQL, Go
    AI/ML Technologies: LLMs & Context Engineering, RAG, PyTorch, Scikit-Learn, LangChain, LlamaIndex, Pinecone,
    Hugging Face, SpaCy
    Web Development: React, FastAPI, Gin, REST APIs, Templ, Alpine.js, Chrome Extension Development, Streamlit
    Data Science: NumPy, Pandas, Seaborn, Data Analysis & Visualization, Feature Engineering, Hypothesis Testing
    Tools & Platforms: Git, Docker, Linux CLI, PostgreSQL, PyTest, MCP/MCP SDK, AWS (learning)
    Core Concepts: Data Structures & Algorithms, OOP, Spec-Driven Development, Machine Learning & Deep Learning

    In these examples: Programming Languages, AI/ML Technologies etc. are the labels (or <<key>>)
    '''
    # Content Sections
    work_experience: Optional[list[RewrittenExperience]] = None
    projects: list[RewrittenProject]  # Top 2-3, rewritten
    education: Education
    involvements: Optional[list[Involvement]] = None

class RewrittenInvolvement(BaseModel): # Involvements can include other stuff on the resume like volunteering or non paid positions (like school club involvements)
    position_title: str
    organization: str
    date_range: str
    location: str
    bullets: list[str]

```

---

### 6. cover_letter_components.json (Output of Lite Flow 2)

```python
class CoverLetterComponentsSchema(BaseModel):
    date: str  # Formatted date
    recipient: Optional[str] = None  # "Hiring Manager" as fallback
    company_name: str
    job_title: str
    
    opening: str           # Hook + why this role/company (2-3 sentences)
    body_experience: str   # Most relevant project/experience (3-4 sentences)
    body_skills: str       # Skills alignment paragraph (3-4 sentences)
    closing: str           # Call to action + enthusiasm (2-3 sentences)
    
    candidate_name: str
```

---

## Workflow Specifications

### Main Flow 1: Job Extraction

**Purpose:** Extract structured job data from raw HTML/DOM content.

**Input:** Raw HTML string from browser extension  
**Output:** `job.json`  
**Model:** Gemini 2.5 Flash Lite

#### Implementation Steps

1. **Receive DOM content** from browser extension via API endpoint
2. **Clean HTML** - Remove scripts, styles, navigation elements
3. **Send to Gemini Flash** with structured output instructions
4. **Validate response** against `JobSchema`
5. **Normalize skills** - Convert variations to canonical forms:
   - "3+ years Python" → "Python"
   - "JavaScript/TypeScript" → ["JavaScript", "TypeScript"]
   - "React.js" → "React"
6. **Save** to `data/jobs/{job_id}.json`

#### Prompt Template

```python
JOB_EXTRACTION_PROMPT = """
You are extracting structured job posting data from HTML content.

Extract the following fields:
- company_name: The hiring company's name
- job_title: The exact job title
- job_description: The full job description text (preserve formatting)
- req_id: Job requisition ID if present, otherwise null
- location: Job location if specified
- required_skills: List of explicitly required technical skills (normalize to single technologies)
- preferred_skills: List of preferred/nice-to-have skills (normalize to single technologies)

For skills extraction:
- Extract individual technologies, not phrases
- "3+ years of Python experience" → "Python"
- "Experience with React and Node.js" → ["React", "Node.js"]
- Include programming languages, frameworks, tools, platforms
- Do NOT include soft skills in these lists

Respond with valid JSON matching this exact schema:
{schema}
"""
```

#### Service Implementation

```python
# app/services/job_extractor.py

from app.models.job import JobSchema
from app.services.llm_client import GeminiClient
from app.config import settings
import json

class JobExtractor:
    def __init__(self):
        self.llm = GeminiClient(model="gemini-2.5-flash-lite")
    
    async def extract(self, html_content: str) -> JobSchema:
        """Extract job data from HTML content."""
        
        # Clean HTML (remove scripts, styles, etc.)
        cleaned_html = self._clean_html(html_content)
        
        # Build prompt
        prompt = JOB_EXTRACTION_PROMPT.format(
            schema=JobSchema.model_json_schema(),
            html_content=cleaned_html
        )
        
        # Call LLM
        response = await self.llm.generate(
            prompt=prompt,
            response_format="json"
        )
        
        # Parse and validate
        job_data = json.loads(response)
        job = JobSchema(**job_data)
        
        # Normalize skills
        job.required_skills = self._normalize_skills(job.required_skills)
        job.preferred_skills = self._normalize_skills(job.preferred_skills)
        
        return job
    
    def _clean_html(self, html: str) -> str:
        """Remove non-content HTML elements."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script, style, nav, footer elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
        
        return soup.get_text(separator='\n', strip=True)
    
    def _normalize_skills(self, skills: list[str]) -> list[str]:
        """Normalize skill names to canonical forms."""
        SKILL_ALIASES = {
            "js": "JavaScript",
            "ts": "TypeScript",
            "react.js": "React",
            "reactjs": "React",
            "node.js": "Node.js",
            "nodejs": "Node.js",
            "postgres": "PostgreSQL",
            "k8s": "Kubernetes",
            # Add more skill aliases and normalized pairs to this dictionary
        }
        
        normalized = []
        for skill in skills:
            skill_lower = skill.lower().strip()
            canonical = SKILL_ALIASES.get(skill_lower, skill.strip())
            if canonical not in normalized:
                normalized.append(canonical)
        
        return normalized
```

---

### Main Flow 2: Profile Matching & Analysis

**Purpose:** Compare user profile against job requirements, rank relevant content, and generate tailoring suggestions.

**Input:** `profile.json`, `job.json`  
**Output:** `profile_matching_data.json`  
**Models:** Hybrid approach (ML + Gemini Flash for recommendations)

#### Implementation Steps

1. **Load inputs** - Parse profile.json and job.json
2. **Keyword extraction** - Extract key terms from job_description using TF-IDF
3. **Direct skill matching** - Compare profile skills against required/preferred skills using fuzzy matching
4. **Project ranking** - Score each project's relevance using semantic similarity + keyword overlap
5. **Skills reordering** - Reorder profile skills by relevance to job
6. **LLM recommendations** - Generate tailoring suggestions using Gemini Flash
7. **Compile results** - Assemble profile_matching_data.json

#### Dependencies

```
# requirements.txt additions for Main Flow 2
keybert>=0.8.0
sentence-transformers>=2.2.0
rapidfuzz>=3.0.0
scikit-learn>=1.3.0
```

#### Service Implementation

```python
# app/services/profile_matcher.py

from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util
from rapidfuzz import fuzz, process
from app.models.matching import ProfileMatchingSchema, ProjectRelevance, KeywordMatch
from app.models.profile import ProfileSchema
from app.models.job import JobSchema
from app.services.llm_client import GeminiClient

class ProfileMatcher:
    def __init__(self):
        self.keyword_model = KeyBERT()
        self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.llm = GeminiClient(model="gemini-2.5-flash-lite")
    
    async def analyze(self, profile: ProfileSchema, job: JobSchema) -> ProfileMatchingSchema:
        """Perform comprehensive profile-job matching analysis."""
        
        # Step 1: Extract keywords from job description
        job_keywords = self._extract_keywords(job.job_description)
        
        # Step 2: Match skills
        keyword_match = self._match_skills(profile, job)
        
        # Step 3: Rank projects
        ranked_projects = self._rank_projects(profile.projects, job)
        
        # Step 4: Rank skills by relevance
        ranked_skills = self._rank_skills(profile, job)
        
        # Step 5: Calculate overall score
        overall_score = self._calculate_overall_score(keyword_match, ranked_projects)
        
        # Step 6: Generate tailoring suggestions (LLM)
        tailoring = await self._generate_suggestions(profile, job, keyword_match)
        
        return ProfileMatchingSchema(
            overall_match_score=overall_score,
            keyword_match=keyword_match,
            ranked_projects=ranked_projects,
            ranked_skills=ranked_skills,
            tailoring_suggestions=tailoring
        )
    
    def _extract_keywords(self, text: str, top_n: int = 20) -> list[str]:
        """Extract important keywords from job description."""
        keywords = self.keyword_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=top_n
        )
        return [kw[0] for kw in keywords]
    
    def _match_skills(self, profile: ProfileSchema, job: JobSchema) -> KeywordMatch:
        """Match profile skills against job requirements using fuzzy matching."""
        
        # Combine all profile skills
        profile_skills = (
            profile.programming_languages +
            profile.frameworks_libraries +
            profile.tools_platforms
        )
        profile_skills_lower = [s.lower() for s in profile_skills]
        
        matched_required = []
        matched_preferred = []
        missing_critical = []
        
        # Check required skills
        for skill in job.required_skills:
            match = process.extractOne(
                skill.lower(),
                profile_skills_lower,
                scorer=fuzz.ratio
            )
            if match and match[1] >= 80:  # 80% similarity threshold
                matched_required.append(skill)
            else:
                missing_critical.append(skill)
        
        # Check preferred skills
        for skill in job.preferred_skills:
            match = process.extractOne(
                skill.lower(),
                profile_skills_lower,
                scorer=fuzz.ratio
            )
            if match and match[1] >= 80:
                matched_preferred.append(skill)
        
        return KeywordMatch(
            matched_required=matched_required,
            matched_preferred=matched_preferred,
            missing_critical=missing_critical
        )
    
    def _rank_projects(self, projects: list, job: JobSchema) -> list[ProjectRelevance]:
        """Rank projects by relevance to job using semantic similarity."""
        
        # Create job context embedding
        job_context = f"{job.job_title} {job.job_description} {' '.join(job.required_skills)}"
        job_embedding = self.semantic_model.encode(job_context)
        
        ranked = []
        for project in projects:
            # Create project text
            project_text = f"{project.name} {' '.join(project.technologies)} {' '.join(project.bullets)}"
            project_embedding = self.semantic_model.encode(project_text)
            
            # Calculate similarity
            similarity = util.cos_sim(job_embedding, project_embedding).item()
            
            # Find matching keywords
            matching_keywords = [
                skill for skill in job.required_skills + job.preferred_skills
                if skill.lower() in project_text.lower()
            ]
            
            ranked.append(ProjectRelevance(
                project_name=project.name,
                relevance_score=round(similarity, 3),
                matching_keywords=matching_keywords,
                recommended=False  # Set later
            ))
        
        # Sort by relevance and mark top 2-3 as recommended
        ranked.sort(key=lambda x: x.relevance_score, reverse=True)
        for i, project in enumerate(ranked[:3]):
            project.recommended = True
        
        return ranked
    
    def _rank_skills(self, profile: ProfileSchema, job: JobSchema) -> dict:
        """Reorder profile skills by relevance to job."""
        
        all_job_skills = job.required_skills + job.preferred_skills
        job_skills_lower = [s.lower() for s in all_job_skills]
        
        def skill_relevance(skill: str) -> float:
            """Higher score = more relevant."""
            skill_lower = skill.lower()
            
            # Exact match in required = highest
            if skill_lower in [s.lower() for s in job.required_skills]:
                return 3.0
            
            # Exact match in preferred
            if skill_lower in [s.lower() for s in job.preferred_skills]:
                return 2.0
            
            # Fuzzy match
            match = process.extractOne(skill_lower, job_skills_lower, scorer=fuzz.ratio)
            if match and match[1] >= 70:
                return 1.0 + (match[1] / 100)
            
            # Check if mentioned in job description
            if skill_lower in job.job_description.lower():
                return 0.5
            
            return 0.0
        
        return {
            "languages": sorted(profile.programming_languages, key=skill_relevance, reverse=True)[:5],
            "frameworks": sorted(profile.frameworks_libraries, key=skill_relevance, reverse=True)[:8],
            "tools": sorted(profile.tools_platforms, key=skill_relevance, reverse=True)[:5]
        }
    
    def _calculate_overall_score(self, keyword_match: KeywordMatch, projects: list) -> float:
        """Calculate overall match score (0-100)."""
        
        # Required skills match (60% weight)
        total_required = len(keyword_match.matched_required) + len(keyword_match.missing_critical)
        required_score = (len(keyword_match.matched_required) / max(total_required, 1)) * 60
        
        # Preferred skills match (20% weight)
        preferred_count = len(keyword_match.matched_preferred)
        preferred_score = min(preferred_count * 4, 20)  # Cap at 20
        
        # Top project relevance (20% weight)
        if projects:
            top_project_score = projects[0].relevance_score * 20
        else:
            top_project_score = 0
        
        return round(required_score + preferred_score + top_project_score, 1)
    
    async def _generate_suggestions(self, profile: ProfileSchema, job: JobSchema, match: KeywordMatch) -> dict:
        """Generate tailoring suggestions using LLM."""
        
        prompt = f"""
Analyze this job-profile match and provide tailoring suggestions.

Job Title: {job.job_title}
Company: {job.company_name}
Required Skills Matched: {match.matched_required}
Required Skills Missing: {match.missing_critical}
Preferred Skills Matched: {match.matched_preferred}

Provide:
1. keywords_to_incorporate: 5-8 action words and technical terms from the job description that should be woven into resume bullets
2. emphasis_areas: 3-5 broader themes to emphasize (e.g., "backend architecture", "team collaboration")

Respond with JSON only:
{{"keywords_to_incorporate": [...], "emphasis_areas": [...]}}
"""
        
        response = await self.llm.generate(prompt, response_format="json")
        return json.loads(response)
```

---

### Lite Flow 1: Company Research

**Purpose:** Gather company intelligence for cover letter personalization.

**Input:** `job.json` (specifically `company_name`)  
**Output:** `company_summary.json`  
**Model:** Gemini 2.5 Flash Lite

#### Implementation Steps

1. **Extract company name** from job.json
2. **Check cache** - If recent summary exists (<7 days), return cached version
3. **Generate search queries:**
   - `"{company} mission values"`
   - `"{company} company culture"`
   - `"{company} engineering team"` (for tech roles)
   - `"{company} recent news 2024"`
4. **Execute searches** - Use search API (SerpAPI, Google Custom Search, or similar)
5. **Aggregate results** - Combine top 2-3 results per query
6. **Send to Gemini Flash** - Extract structured summary
7. **Validate and cache** - Save to `data/companies/{company_slug}.json`

#### Service Implementation

```python
# app/services/company_researcher.py

from app.models.company import CompanySummarySchema
from app.services.llm_client import GeminiClient
from app.utils.web_search import SearchClient
from app.config import settings
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

class CompanyResearcher:
    def __init__(self):
        self.llm = GeminiClient(model="gemini-2.5-flash-lite")
        self.search = SearchClient()
        self.cache_dir = Path("data/companies")
        self.cache_ttl = timedelta(days=7)
    
    async def research(self, company_name: str) -> CompanySummarySchema:
        """Research company and generate summary."""
        
        # Check cache
        cached = self._get_cached(company_name)
        if cached:
            return cached
        
        # Generate search queries
        queries = [
            f"{company_name} mission statement values",
            f"{company_name} company culture workplace",
            f"{company_name} engineering team tech stack",
            f"{company_name} recent news 2024 2025",
        ]
        
        # Execute searches
        search_results = []
        for query in queries:
            results = await self.search.search(query, num_results=3)
            search_results.extend(results)
        
        # Combine results into context
        context = self._format_search_results(search_results)
        
        # Generate summary with LLM
        summary = await self._generate_summary(company_name, context)
        
        # Cache and return
        self._cache_summary(company_name, summary)
        return summary
    
    def _get_cached(self, company_name: str) -> CompanySummarySchema | None:
        """Check for valid cached summary."""
        cache_file = self.cache_dir / f"{self._slugify(company_name)}.json"
        
        if cache_file.exists():
            data = json.loads(cache_file.read_text())
            cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
            
            if datetime.now() - cached_at < self.cache_ttl:
                del data["_cached_at"]
                return CompanySummarySchema(**data)
        
        return None
    
    def _cache_summary(self, company_name: str, summary: CompanySummarySchema):
        """Cache company summary."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / f"{self._slugify(company_name)}.json"
        
        data = summary.model_dump()
        data["_cached_at"] = datetime.now().isoformat()
        
        cache_file.write_text(json.dumps(data, indent=2))
    
    def _slugify(self, name: str) -> str:
        """Convert company name to filename-safe slug."""
        return name.lower().replace(" ", "_").replace(".", "")[:50]
    
    def _format_search_results(self, results: list) -> str:
        """Format search results for LLM context."""
        formatted = []
        for r in results:
            formatted.append(f"Source: {r['title']}\n{r['snippet']}\n")
        return "\n---\n".join(formatted)
    
    async def _generate_summary(self, company_name: str, context: str) -> CompanySummarySchema:
        """Generate company summary from search results."""
        
        prompt = f"""
Based on the following search results about {company_name}, extract a structured company summary.

Search Results:
{context}

Extract:
- industry: The company's primary industry/sector
- mission_or_values: A 1-2 sentence summary of their mission or core values (null if not found)
- culture_keywords: 3-5 words describing their culture (e.g., "innovative", "collaborative")
- recent_highlight: One notable recent achievement, launch, or news item (null if not found)
- tone: The appropriate tone for a cover letter - "formal", "conversational", or "startup"

Respond with JSON only:
{{
    "company_name": "{company_name}",
    "industry": "...",
    "mission_or_values": "...",
    "culture_keywords": ["...", "..."],
    "recent_highlight": "...",
    "tone": "..."
}}
"""
        
        response = await self.llm.generate(prompt, response_format="json")
        data = json.loads(response)
        return CompanySummarySchema(**data)
```

---

### Main Flow 3: Resume Generation

**Purpose:** Generate a tailored resume using multi-pass LLM processing and LaTeX template injection.

**Input:** `profile.json`, `job.json`, `profile_matching_data.json`  
**Output:** `resume_components.json` → `resume.tex` → `resume.pdf`

#### Generation Strategy (Multi-Pass)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PASS 1: SELECTION                            │
│                    (Gemini 2.5 Flash)                           │
├─────────────────────────────────────────────────────────────────┤
│  Input: Full profile, ranked_projects from matching data        │
│  Task:  Select which projects/experiences to include            │
│  Output: selection.json                                         │
│          - selected_projects: ["ProjectA", "ProjectB"]          │
│          - selected_experiences: [...]                          │
│          - selected_involvements: [...]                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PASS 2: REWRITING                            │
│                    (Gemini 2.5 Pro)                             │
├─────────────────────────────────────────────────────────────────┤
│  Input: Original bullets, job description, target keywords      │
│  Task:  Rewrite bullets to emphasize relevant skills            │
│  Rules:                                                         │
│    - Maintain truthfulness (rephrase, don't fabricate)          │
│    - Incorporate target keywords naturally                      │
│    - Keep bullets concise (1-2 lines)                           │
│    - Use strong action verbs                                    │
│  Output: rewritten_content.json                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PASS 3: SUMMARY                              │
│                    (Gemini 2.5 Flash)                           │
├─────────────────────────────────────────────────────────────────┤
│  Input: Job title, company, selected content, matched skills    │
│  Task:  Generate 2-3 sentence professional summary              │
│  Output: profile_summary string                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PASS 4: ASSEMBLY                             │
│                    (No LLM - Pure Logic)                        │
├─────────────────────────────────────────────────────────────────┤
│  Task:                                                          │
│    1. Merge all passes into resume_components.json              │
│    2. Inject values into LaTeX template                         │
│    3. Compile to PDF using pdflatex                             │
│  Output: resume.pdf                                             │
└─────────────────────────────────────────────────────────────────┘
```

#### Service Implementation

```python
# app/services/resume_generator.py

from app.models.profile import ProfileSchema
from app.models.job import JobSchema
from app.models.matching import ProfileMatchingSchema
from app.models.resume import ResumeComponentsSchema, RewrittenProject
from app.services.llm_client import GeminiClient
from app.utils.latex_compiler import LatexCompiler
import json

class ResumeGenerator:
    def __init__(self):
        self.flash = GeminiClient(model="gemini-2.5-flash-lite")
        self.pro = GeminiClient(model="gemini-2.5-pro")
        self.latex = LatexCompiler()
    
    async def generate(
        self,
        profile: ProfileSchema,
        job: JobSchema,
        matching: ProfileMatchingSchema
    ) -> tuple[ResumeComponentsSchema, bytes]:
        """
        Generate tailored resume through multi-pass process.
        Returns (components, pdf_bytes).
        """
        
        # Pass 1: Selection
        selection = await self._pass_selection(profile, matching)
        
        # Pass 2: Rewriting
        rewritten = await self._pass_rewriting(profile, job, matching, selection)
        
        # Pass 3: Summary
        summary = await self._pass_summary(profile, job, matching, rewritten)
        
        # Pass 4: Assembly
        components = self._assemble_components(profile, matching, selection, rewritten, summary)
        
        # Compile to PDF
        pdf_bytes = self.latex.compile(components)
        
        return components, pdf_bytes
    
    async def _pass_selection(
        self,
        profile: ProfileSchema,
        matching: ProfileMatchingSchema
    ) -> dict:
        """Pass 1: Select which content to include."""
        
        # Get recommended projects from matching
        recommended = [p.project_name for p in matching.ranked_projects if p.recommended]
        
        prompt = f"""
Select content for a tailored resume based on relevance rankings.

Available Projects (ranked by relevance):
{json.dumps([{"name": p.project_name, "score": p.relevance_score} for p in matching.ranked_projects], indent=2)}

Available Work Experience:
{json.dumps([{"company": e.company, "title": e.title} for e in (profile.work_experience or [])], indent=2)}

Available Involvements:
{json.dumps([{"org": i.organization, "role": i.role} for i in (profile.involvements or [])], indent=2)}

Guidelines:
- Select 2-3 most relevant projects (pre-ranked suggestions: {recommended})
- Select 1-2 work experiences if highly relevant
- Select 0-2 involvements if they add value
- Prioritize technical depth and relevance

Respond with JSON:
{{
    "selected_projects": ["Project Name 1", "Project Name 2"],
    "selected_experiences": ["Company Name"],
    "selected_involvements": ["Organization Name"]
}}
"""
        
        response = await self.flash.generate(prompt, response_format="json")
        return json.loads(response)
    
    async def _pass_rewriting(
        self,
        profile: ProfileSchema,
        job: JobSchema,
        matching: ProfileMatchingSchema,
        selection: dict
    ) -> dict:
        """Pass 2: Rewrite bullets with Gemini Pro."""
        
        keywords = matching.tailoring_suggestions["keywords_to_incorporate"]
        emphasis = matching.tailoring_suggestions["emphasis_areas"]
        
        rewritten = {"projects": [], "experiences": []}
        
        # Rewrite selected projects
        for project in profile.projects:
            if project.name in selection["selected_projects"]:
                rewritten_bullets = await self._rewrite_bullets(
                    original_bullets=project.bullets,
                    context_type="project",
                    context_name=project.name,
                    job=job,
                    keywords=keywords,
                    emphasis=emphasis
                )
                rewritten["projects"].append({
                    "name": project.name,
                    "bullets": rewritten_bullets
                })
        
        # Rewrite selected experiences
        for exp in (profile.work_experience or []):
            if exp.company in selection["selected_experiences"]:
                rewritten_bullets = await self._rewrite_bullets(
                    original_bullets=exp.bullets,
                    context_type="experience",
                    context_name=f"{exp.title} at {exp.company}",
                    job=job,
                    keywords=keywords,
                    emphasis=emphasis
                )
                rewritten["experiences"].append({
                    "company": exp.company,
                    "bullets": rewritten_bullets
                })
        
        return rewritten
    
    async def _rewrite_bullets(
        self,
        original_bullets: list[str],
        context_type: str,
        context_name: str,
        job: JobSchema,
        keywords: list[str],
        emphasis: list[str]
    ) -> list[str]:
        """Rewrite individual bullets using Gemini Pro."""
        
        prompt = f"""
You are rewriting resume bullets for a {job.job_title} position at {job.company_name}.

Context: {context_type} - {context_name}

Original Bullets:
{chr(10).join(f'- {b}' for b in original_bullets)}

Target Keywords to incorporate naturally: {keywords}
Emphasis Areas: {emphasis}

Guidelines:
1. MAINTAIN TRUTHFULNESS - rephrase and emphasize, do NOT add claims not supported by original
2. Incorporate relevant keywords where they fit naturally
3. Use strong action verbs (Developed, Implemented, Designed, Optimized, Led, etc.)
4. Quantify impact where possible (keep original numbers, don't invent)
5. Keep each bullet to 1-2 lines maximum
6. Focus on technical depth and measurable outcomes

Respond with JSON array of rewritten bullets:
["Rewritten bullet 1", "Rewritten bullet 2", ...]
"""
        
        response = await self.pro.generate(prompt, response_format="json")
        return json.loads(response)
    
    async def _pass_summary(
        self,
        profile: ProfileSchema,
        job: JobSchema,
        matching: ProfileMatchingSchema,
        rewritten: dict
    ) -> str:
        """Pass 3: Generate professional summary."""
        
        prompt = f"""
Write a 2-3 sentence professional summary for a {job.job_title} position at {job.company_name}.

Candidate: {profile.name}
Education: {profile.education.degree} from {profile.education.institution}
Key Matched Skills: {matching.keyword_match.matched_required}
Top Projects Being Featured: {[p['name'] for p in rewritten['projects']]}

Guidelines:
- Reference the specific role naturally
- Highlight 2-3 strongest skill alignments
- Keep professional but not generic
- Do NOT start with "I am" or "My name is"

Respond with the summary text only (no JSON, no quotes).
"""
        
        response = await self.flash.generate(prompt, response_format="text")
        return response.strip()
    
    def _assemble_components(
        self,
        profile: ProfileSchema,
        matching: ProfileMatchingSchema,
        selection: dict,
        rewritten: dict,
        summary: str
    ) -> ResumeComponentsSchema:
        """Pass 4: Assemble final resume components."""
        
        # Build projects list with rewritten bullets
        projects = []
        for project in profile.projects:
            if project.name in selection["selected_projects"]:
                # Find rewritten bullets
                rewritten_data = next(
                    (p for p in rewritten["projects"] if p["name"] == project.name),
                    None
                )
                
                projects.append(RewrittenProject(
                    name=project.name,
                    organization=project.organization,
                    date_range=project.date_range,
                    technologies=", ".join(project.technologies[:6]),  # Top 6 technologies
                    bullets=rewritten_data["bullets"] if rewritten_data else project.bullets,
                    link=str(project.link) if project.link else None
                ))
        
        return ResumeComponentsSchema(
            # Header
            name=profile.name,
            phone=profile.phone,
            email=profile.email,
            github=str(profile.github) if profile.github else "",
            linkedin=str(profile.linkedin) if profile.linkedin else None,
            portfolio=str(profile.portfolio) if profile.portfolio else None,
            location=profile.location,
            
            # Summary
            profile_summary=summary,
            
            # Skills (use ranked order from matching)
            programming_languages=matching.ranked_skills["languages"],
            frameworks_libraries=matching.ranked_skills["frameworks"],
            tools_platforms=matching.ranked_skills["tools"],
            
            # Content
            projects=projects,
            education=profile.education,
            work_experience=None,  # Add if selected
            involvements=None  # Add if selected
        )
```

---

### Lite Flow 2: Cover Letter Generation

**Purpose:** Generate a personalized cover letter using job, profile, and company data.

**Input:** `job.json`, `profile.json`, `profile_matching_data.json`, `company_summary.json`  
**Output:** `cover_letter_components.json` → `cover_letter.tex` → `cover_letter.pdf`

#### Implementation Steps

1. **Load all inputs** - job, profile, matching data, company summary
2. **Generate opening paragraph** - Hook + why this company/role
3. **Generate body (experience)** - Most relevant project/experience
4. **Generate body (skills)** - Skills alignment + value proposition
5. **Generate closing** - Call to action + enthusiasm
6. **Assemble components** - Build cover_letter_components.json
7. **Inject into template** - LaTeX template injection
8. **Compile to PDF**

#### Service Implementation

```python
# app/services/cover_letter_generator.py

from app.models.profile import ProfileSchema
from app.models.job import JobSchema
from app.models.matching import ProfileMatchingSchema
from app.models.company import CompanySummarySchema
from app.models.cover_letter import CoverLetterComponentsSchema
from app.services.llm_client import GeminiClient
from app.utils.latex_compiler import LatexCompiler
from datetime import datetime

class CoverLetterGenerator:
    def __init__(self):
        self.llm = GeminiClient(model="gemini-2.5-flash-lite")
        self.latex = LatexCompiler()
    
    async def generate(
        self,
        profile: ProfileSchema,
        job: JobSchema,
        matching: ProfileMatchingSchema,
        company: CompanySummarySchema
    ) -> tuple[CoverLetterComponentsSchema, bytes]:
        """Generate personalized cover letter."""
        
        # Generate each section
        opening = await self._generate_opening(profile, job, company)
        body_experience = await self._generate_body_experience(profile, job, matching)
        body_skills = await self._generate_body_skills(profile, job, matching)
        closing = await self._generate_closing(profile, job, company)
        
        # Assemble components
        components = CoverLetterComponentsSchema(
            date=datetime.now().strftime("%B %d, %Y"),
            recipient=None,  # "Hiring Manager" in template
            company_name=job.company_name,
            job_title=job.job_title,
            opening=opening,
            body_experience=body_experience,
            body_skills=body_skills,
            closing=closing,
            candidate_name=profile.name
        )
        
        # Compile to PDF
        pdf_bytes = self.latex.compile_cover_letter(components)
        
        return components, pdf_bytes
    
    async def _generate_opening(
        self,
        profile: ProfileSchema,
        job: JobSchema,
        company: CompanySummarySchema
    ) -> str:
        """Generate opening paragraph."""
        
        tone_instruction = {
            "formal": "Use professional, formal language",
            "conversational": "Use a warm but professional tone",
            "startup": "Use an energetic, direct tone"
        }.get(company.tone, "Use professional language")
        
        prompt = f"""
Write an opening paragraph (2-3 sentences) for a cover letter.

Position: {job.job_title}
Company: {job.company_name}
Company Mission: {company.mission_or_values or 'Not available'}
Company Culture: {', '.join(company.culture_keywords)}

Candidate Background: {profile.education.degree} from {profile.education.institution}

Guidelines:
- {tone_instruction}
- Express genuine interest in the role
- Reference something specific about the company (mission, culture, or recent news)
- Do NOT use generic phrases like "I am writing to apply"
- Make it compelling and specific

Company Highlight (optional to reference): {company.recent_highlight or 'None'}

Respond with the paragraph text only.
"""
        
        return (await self.llm.generate(prompt, response_format="text")).strip()
    
    async def _generate_body_experience(
        self,
        profile: ProfileSchema,
        job: JobSchema,
        matching: ProfileMatchingSchema
    ) -> str:
        """Generate body paragraph about relevant experience."""
        
        # Get top recommended project
        top_project = next(
            (p for p in matching.ranked_projects if p.recommended),
            matching.ranked_projects[0] if matching.ranked_projects else None
        )
        
        if top_project:
            project = next(p for p in profile.projects if p.name == top_project.project_name)
            project_context = f"""
Project: {project.name}
Technologies: {', '.join(project.technologies)}
Description: {' '.join(project.bullets[:2])}
"""
        else:
            project_context = "No specific project available"
        
        prompt = f"""
Write a body paragraph (3-4 sentences) highlighting relevant experience for this role.

Position: {job.job_title}
Required Skills: {job.required_skills}

{project_context}

Guidelines:
- Focus on the most relevant project or experience
- Connect technical work to the job requirements
- Highlight specific technologies or approaches used
- Show impact or outcomes where possible
- Keep it concise but substantive

Respond with the paragraph text only.
"""
        
        return (await self.llm.generate(prompt, response_format="text")).strip()
    
    async def _generate_body_skills(
        self,
        profile: ProfileSchema,
        job: JobSchema,
        matching: ProfileMatchingSchema
    ) -> str:
        """Generate body paragraph about skills alignment."""
        
        prompt = f"""
Write a body paragraph (3-4 sentences) about skills alignment and value proposition.

Position: {job.job_title}
Company: {job.company_name}

Skills Matched to Requirements: {matching.keyword_match.matched_required}
Additional Relevant Skills: {matching.keyword_match.matched_preferred}
Areas to Emphasize: {matching.tailoring_suggestions['emphasis_areas']}

Guidelines:
- Highlight how your skills directly address their needs
- Mention 2-3 specific technologies confidently
- Include soft skills or collaboration abilities
- Express enthusiasm for the technical challenges
- Avoid simply listing skills - weave them into a narrative

Respond with the paragraph text only.
"""
        
        return (await self.llm.generate(prompt, response_format="text")).strip()
    
    async def _generate_closing(
        self,
        profile: ProfileSchema,
        job: JobSchema,
        company: CompanySummarySchema
    ) -> str:
        """Generate closing paragraph."""
        
        prompt = f"""
Write a closing paragraph (2-3 sentences) for the cover letter.

Position: {job.job_title}
Company: {job.company_name}
Candidate: {profile.name}

Guidelines:
- Express enthusiasm for the opportunity
- Include a soft call to action (interview, discussion)
- Thank them for their consideration
- Match the tone: {company.tone}
- Do NOT be overly formal or use "Sincerely" (that goes in signature)

Respond with the paragraph text only.
"""
        
        return (await self.llm.generate(prompt, response_format="text")).strip()
```

---

## LaTeX Template: Jake's Resume

The resume uses Jake's Resume template with placeholder injection. Placeholders use the format `<<PLACEHOLDER_NAME>>` for string replacement.

### Template Structure

```latex
% app/templates/jake_resume.tex

%-------------------------
% Resume in LaTeX
% Based on: https://github.com/jakegut/resume
%-------------------------

\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\input{glyphtounicode}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

\pdfgentounicode=1

% Custom commands
\newcommand{\resumeItem}[1]{\item\small{#1 \vspace{-2pt}}}
\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}
\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}
\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}
\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\begin{document}

%----------HEADING----------
\begin{center}
    \textbf{\Huge \scshape <<NAME>>} \\ \vspace{1pt}
    \small <<PHONE>> $|$ 
    \href{mailto:<<EMAIL>>}{\underline{<<EMAIL>>}} $|$ 
    \href{<<LINKEDIN>>}{\underline{<<LINKEDIN_DISPLAY>>}} $|$
    \href{<<GITHUB>>}{\underline{<<GITHUB_DISPLAY>>}}
\end{center}

%----------SUMMARY----------
\section{Summary}
<<PROFILE_SUMMARY>>

%-----------EDUCATION-----------
\section{Education}
\resumeSubHeadingListStart
  \resumeSubheading
    {<<EDUCATION_INSTITUTION>>}{<<EDUCATION_DATES>>}
    {<<EDUCATION_DEGREE>>}{<<EDUCATION_LOCATION>>}
\resumeSubHeadingListEnd

%-----------TECHNICAL SKILLS-----------
\section{Technical Skills}
\begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
     \textbf{Languages}{: <<LANGUAGES>>} \\
     \textbf{Frameworks}{: <<FRAMEWORKS>>} \\
     \textbf{Developer Tools}{: <<TOOLS>>}
    }}
\end{itemize}

%-----------PROJECTS-----------
\section{Projects}
\resumeSubHeadingListStart
<<PROJECTS_CONTENT>>
\resumeSubHeadingListEnd

%-----------EXPERIENCE-----------
<<EXPERIENCE_SECTION>>

%-----------INVOLVEMENTS-----------
<<INVOLVEMENTS_SECTION>>

\end{document}
```

### Template Injection Utility

```python
# app/utils/latex_compiler.py

import subprocess
import tempfile
from pathlib import Path
from app.models.resume import ResumeComponentsSchema

class LatexCompiler:
    def __init__(self):
        self.template_dir = Path("app/templates")
    
    def compile(self, components: ResumeComponentsSchema) -> bytes:
        """Inject components into template and compile to PDF."""
        
        # Load template
        template = (self.template_dir / "jake_resume.tex").read_text()
        
        # Perform replacements
        latex_content = self._inject_components(template, components)
        
        # Compile to PDF
        return self._compile_latex(latex_content)
    
    def _inject_components(self, template: str, c: ResumeComponentsSchema) -> str:
        """Replace placeholders with actual content."""
        
        replacements = {
            "<<NAME>>": self._escape_latex(c.name),
            "<<PHONE>>": self._escape_latex(c.phone),
            "<<EMAIL>>": self._escape_latex(c.email),
            "<<LINKEDIN>>": c.linkedin or "",
            "<<LINKEDIN_DISPLAY>>": self._format_linkedin(c.linkedin),
            "<<GITHUB>>": c.github,
            "<<GITHUB_DISPLAY>>": self._format_github(c.github),
            "<<PROFILE_SUMMARY>>": self._escape_latex(c.profile_summary),
            "<<EDUCATION_INSTITUTION>>": self._escape_latex(c.education.institution),
            "<<EDUCATION_DATES>>": self._escape_latex(c.education.date_range),
            "<<EDUCATION_DEGREE>>": self._escape_latex(c.education.degree),
            "<<EDUCATION_LOCATION>>": "",  # Add if needed
            "<<LANGUAGES>>": self._escape_latex(", ".join(c.programming_languages)),
            "<<FRAMEWORKS>>": self._escape_latex(", ".join(c.frameworks_libraries)),
            "<<TOOLS>>": self._escape_latex(", ".join(c.tools_platforms)),
            "<<PROJECTS_CONTENT>>": self._format_projects(c.projects),
            "<<EXPERIENCE_SECTION>>": self._format_experience(c.work_experience),
            "<<INVOLVEMENTS_SECTION>>": self._format_involvements(c.involvements),
        }
        
        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        
        return result
    
    def _format_projects(self, projects: list) -> str:
        """Format projects section."""
        items = []
        for p in projects:
            item = f"""\\resumeProjectHeading
      {{\\textbf{{{self._escape_latex(p.name)}}} $|$ \\emph{{{self._escape_latex(p.technologies)}}}}}{{{p.date_range}}}
      \\resumeItemListStart
"""
            for bullet in p.bullets:
                item += f"        \\resumeItem{{{self._escape_latex(bullet)}}}\n"
            item += "      \\resumeItemListEnd"
            items.append(item)
        
        return "\n".join(items)
    
    def _format_experience(self, experiences: list | None) -> str:
        """Format experience section."""
        if not experiences:
            return ""
        
        content = "\\section{Experience}\n\\resumeSubHeadingListStart\n"
        for exp in experiences:
            content += f"""  \\resumeSubheading
    {{{self._escape_latex(exp.company)}}}{{{exp.date_range}}}
    {{{self._escape_latex(exp.title)}}}{{{self._escape_latex(exp.location)}}}
    \\resumeItemListStart
"""
            for bullet in exp.bullets:
                content += f"      \\resumeItem{{{self._escape_latex(bullet)}}}\n"
            content += "    \\resumeItemListEnd\n"
        
        content += "\\resumeSubHeadingListEnd"
        return content
    
    def _format_involvements(self, involvements: list | None) -> str:
        """Format involvements section."""
        if not involvements:
            return ""
        
        # Similar to experience formatting
        return ""  # Implement as needed
    
    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters."""
        if not text:
            return ""
        
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\^{}',
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text
    
    def _format_linkedin(self, url: str | None) -> str:
        """Extract LinkedIn display text."""
        if not url:
            return ""
        # Extract username from URL
        return url.split("/in/")[-1].rstrip("/")
    
    def _format_github(self, url: str) -> str:
        """Extract GitHub display text."""
        if not url:
            return ""
        return url.replace("https://github.com/", "github.com/")
    
    def _compile_latex(self, latex_content: str) -> bytes:
        """Compile LaTeX to PDF using pdflatex."""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Write .tex file
            tex_file = tmpdir / "resume.tex"
            tex_file.write_text(latex_content)
            
            # Run pdflatex (twice for references)
            for _ in range(2):
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "resume.tex"],
                    cwd=tmpdir,
                    capture_output=True,
                    timeout=30
                )
            
            # Read PDF
            pdf_file = tmpdir / "resume.pdf"
            if pdf_file.exists():
                return pdf_file.read_bytes()
            else:
                raise RuntimeError(f"PDF compilation failed: {result.stderr.decode()}")
```

---

## LLM Client Wrapper

```python
# app/services/llm_client.py

import google.generativeai as genai
from app.config import settings

class GeminiClient:
    def __init__(self, model: str = "gemini-2.5-flash-lite"):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(model)
    
    async def generate(
        self,
        prompt: str,
        response_format: str = "text",  # "text" or "json"
        temperature: float = 0.7
    ) -> str:
        """Generate response from Gemini."""
        
        generation_config = {
            "temperature": temperature,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        if response_format == "json":
            generation_config["response_mime_type"] = "application/json"
        
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        return response.text
```

---

## API Endpoints

```python
# app/main.py

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import Response
from app.models.profile import ProfileSchema
from app.models.job import JobSchema
from app.services.job_extractor import JobExtractor
from app.services.profile_matcher import ProfileMatcher
from app.services.company_researcher import CompanyResearcher
from app.services.resume_generator import ResumeGenerator
from app.services.cover_letter_generator import CoverLetterGenerator
import json

app = FastAPI(title="JobAgent0 Backend")

# Initialize services
job_extractor = JobExtractor()
profile_matcher = ProfileMatcher()
company_researcher = CompanyResearcher()
resume_generator = ResumeGenerator()
cover_letter_generator = CoverLetterGenerator()


@app.post("/api/extract-job")
async def extract_job(html_content: str):
    """Main Flow 1: Extract job data from HTML."""
    job = await job_extractor.extract(html_content)
    return job.model_dump()


@app.post("/api/analyze-match")
async def analyze_match(profile: ProfileSchema, job: JobSchema):
    """Main Flow 2: Analyze profile-job match."""
    matching = await profile_matcher.analyze(profile, job)
    return matching.model_dump()


@app.post("/api/research-company")
async def research_company(company_name: str):
    """Lite Flow 1: Research company."""
    summary = await company_researcher.research(company_name)
    return summary.model_dump()


@app.post("/api/generate-resume")
async def generate_resume(
    profile: ProfileSchema,
    job: JobSchema
):
    """Main Flow 3: Generate tailored resume."""
    
    # Run matching analysis
    matching = await profile_matcher.analyze(profile, job)
    
    # Generate resume
    components, pdf_bytes = await resume_generator.generate(profile, job, matching)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=resume.pdf"}
    )


@app.post("/api/generate-cover-letter")
async def generate_cover_letter(
    profile: ProfileSchema,
    job: JobSchema
):
    """Lite Flow 2: Generate tailored cover letter."""
    
    # Run matching and company research
    matching = await profile_matcher.analyze(profile, job)
    company = await company_researcher.research(job.company_name)
    
    # Generate cover letter
    components, pdf_bytes = await cover_letter_generator.generate(
        profile, job, matching, company
    )
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=cover_letter.pdf"}
    )


@app.post("/api/generate-application")
async def generate_full_application(
    profile: ProfileSchema,
    html_content: str
):
    """
    Complete pipeline: Extract job → Analyze → Generate both documents.
    Returns JSON with both PDFs as base64.
    """
    import base64
    
    # Flow 1: Extract job
    job = await job_extractor.extract(html_content)
    
    # Flow 2: Analyze match
    matching = await profile_matcher.analyze(profile, job)
    
    # Lite Flow 1: Research company
    company = await company_researcher.research(job.company_name)
    
    # Flow 3: Generate resume
    resume_components, resume_pdf = await resume_generator.generate(
        profile, job, matching
    )
    
    # Lite Flow 2: Generate cover letter
    cover_letter_components, cover_letter_pdf = await cover_letter_generator.generate(
        profile, job, matching, company
    )
    
    return {
        "job": job.model_dump(),
        "matching_score": matching.overall_match_score,
        "resume_pdf": base64.b64encode(resume_pdf).decode(),
        "cover_letter_pdf": base64.b64encode(cover_letter_pdf).decode()
    }
```

---

## Configuration

```python
# app/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: str
    SEARCH_API_KEY: str  # SerpAPI or Google Custom Search
    
    # Model Configuration
    GEMINI_FLASH_MODEL: str = "gemini-2.5-flash-lite"
    GEMINI_PRO_MODEL: str = "gemini-2.5-pro"
    
    # Cache Configuration
    COMPANY_CACHE_TTL_DAYS: int = 7
    
    # Matching Thresholds
    FUZZY_MATCH_THRESHOLD: int = 80
    MIN_PROJECT_RELEVANCE: float = 0.3
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Dependencies

```
# requirements.txt

# Web Framework
fastapi>=0.104.0
uvicorn>=0.24.0

# LLM
google-generativeai>=0.3.0

# ML/NLP
keybert>=0.8.0
sentence-transformers>=2.2.0
rapidfuzz>=3.0.0
scikit-learn>=1.3.0

# Web Scraping/Search
beautifulsoup4>=4.12.0
httpx>=0.25.0

# Data Validation
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Utilities
python-multipart>=0.0.6
python-dotenv>=1.0.0
```

---

## Docker Configuration

```dockerfile
# Dockerfile

FROM python:3.11-slim

# Install LaTeX
RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml

version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SEARCH_API_KEY=${SEARCH_API_KEY}
    volumes:
      - ./data:/app/data
```

---

## Testing Strategy

```python
# tests/test_profile_matcher.py

import pytest
from app.services.profile_matcher import ProfileMatcher
from app.models.profile import ProfileSchema
from app.models.job import JobSchema

@pytest.fixture
def sample_profile():
    return ProfileSchema(
        name="Test User",
        email="test@example.com",
        # ... complete profile
    )

@pytest.fixture
def sample_job():
    return JobSchema(
        company_name="Test Corp",
        job_title="Software Engineer",
        job_description="Looking for Python developers...",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        preferred_skills=["Docker", "AWS"]
    )

@pytest.mark.asyncio
async def test_skill_matching(sample_profile, sample_job):
    matcher = ProfileMatcher()
    result = await matcher.analyze(sample_profile, sample_job)
    
    assert result.overall_match_score >= 0
    assert result.overall_match_score <= 100
    assert len(result.ranked_projects) > 0

@pytest.mark.asyncio
async def test_project_ranking(sample_profile, sample_job):
    matcher = ProfileMatcher()
    result = await matcher.analyze(sample_profile, sample_job)
    
    # Verify projects are sorted by relevance
    scores = [p.relevance_score for p in result.ranked_projects]
    assert scores == sorted(scores, reverse=True)
```

---

## Summary

This specification defines a complete backend system for JobAgent0 with:

1. **Main Flow 1**: DOM extraction → job.json using Gemini Flash
2. **Main Flow 2**: Hybrid ML + LLM profile matching and analysis
3. **Lite Flow 1**: Company research with caching
4. **Main Flow 3**: Multi-pass resume generation (Selection → Rewriting → Summary → Assembly)
5. **Lite Flow 2**: Cover letter generation using all gathered intelligence
6. **Template injection**: Jake's Resume LaTeX template with placeholder replacement
7. **API endpoints**: RESTful FastAPI endpoints for each flow and a complete pipeline endpoint

The system prioritizes accuracy through truthfulness constraints in bullet rewriting, relevance through semantic similarity scoring, and formatting consistency through template injection rather than raw LaTeX generation.
