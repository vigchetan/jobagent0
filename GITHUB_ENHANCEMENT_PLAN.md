# GitHub Profile Extraction Enhancement Plan

## Overview

Enhance Phase 1 (Resume Upload & Parsing) to automatically extract GitHub profile information and generate a structured project list from public repositories. This will help CS students showcase all their projects in a resume-ready format.

---

## Current Flow vs. Enhanced Flow

### Current Phase 1 Flow
```
PDF Upload → Security Validation → PDF Parsing → Gemini AI Parsing
→ Save resume.json → Done
```

### Enhanced Phase 1 Flow
```
PDF Upload → Security Validation → PDF Parsing → Gemini AI Parsing
→ Save resume.json
→ IF github field exists:
    → GitHub API: Fetch user profile
    → GitHub API: List all public repos
    → For each repo: Fetch README.md
    → Gemini AI: Structure repo data as resume projects
    → Save project_list.md
→ Done
```

---

## Architecture Changes

### 1. Data Model Changes

**File**: `backend/models/resume.py`

**Current State**:
- `ContactInfo` already has `github: Optional[str]` field ✅
- No dedicated storage for extracted GitHub projects

**Required Changes**:
- ✅ No changes to `ContactInfo` model (already supports GitHub)
- Add new model for GitHub project data:

```python
class GitHubProject(BaseModel):
    """Structured project data extracted from GitHub repository"""
    name: str
    description: Optional[str]
    technologies: List[str]
    key_features: List[str]
    role: str  # "Creator", "Contributor", "Maintainer"
    stars: int
    forks: int
    repo_url: str
    readme_summary: str
    relevant_highlights: List[str]  # Resume-worthy achievements
```

- Add field to `ResumeData`:
```python
class ResumeData(BaseModel):
    # ... existing fields ...
    github_projects_extracted: bool = False  # Flag to indicate if extraction happened
```

**Output File**:
- `~/JobAgentWorkspace/project_list.md` - Markdown file with all projects formatted for resume use

---

### 2. New Service: GitHub Extraction Service

**File**: `backend/services/github_service.py` (NEW)

**Responsibilities**:
1. Extract GitHub username from profile URL
2. Fetch user profile metadata (bio, location, etc.)
3. List all public repositories
4. Fetch README.md for each repository
5. Extract repository metadata (stars, forks, language, topics)
6. Handle rate limiting and errors gracefully

**GitHub API Integration**:
- Use GitHub REST API v3
- Authentication: Optional GitHub Personal Access Token (increases rate limit)
- Endpoints needed:
  - `GET /users/{username}` - User profile
  - `GET /users/{username}/repos` - List repositories
  - `GET /repos/{owner}/{repo}/readme` - Fetch README

**Key Methods**:
```python
class GitHubService:
    def __init__(self, github_token: Optional[str] = None):
        """Initialize with optional GitHub token for higher rate limits"""

    def extract_username(self, github_url: str) -> str:
        """Extract username from GitHub profile URL"""
        # Handle: github.com/username, github.com/username/, etc.

    def fetch_user_profile(self, username: str) -> dict:
        """Fetch user profile metadata"""

    def fetch_public_repos(self, username: str) -> List[dict]:
        """Fetch all public repositories for user"""
        # Handles pagination (default 30 per page)

    def fetch_readme(self, owner: str, repo: str) -> Optional[str]:
        """Fetch README.md content for a repository"""
        # Returns None if README doesn't exist

    def extract_repo_metadata(self, repo_data: dict) -> dict:
        """Extract relevant metadata from repo API response"""
        # name, description, language, topics, stars, forks, url
```

**Error Handling**:
- Invalid GitHub URL → Log warning, skip extraction
- Rate limit exceeded → Return partial results with warning
- Network errors → Retry with exponential backoff (max 3 attempts)
- 404 errors (repo/user not found) → Skip and continue

---

### 3. New Service: Project Structuring Service

**File**: `backend/services/project_structurer.py` (NEW)

**Responsibilities**:
1. Take raw GitHub repository data
2. Use Gemini AI to structure as resume-style project descriptions
3. Generate markdown output suitable for resume inclusion

**Key Method**:
```python
class ProjectStructurerService:
    def __init__(self, gemini_service: GeminiService):
        """Initialize with Gemini service"""

    def structure_projects(
        self,
        repos_data: List[dict]
    ) -> str:
        """
        Convert GitHub repos into resume-style project descriptions.

        Args:
            repos_data: List of dicts containing:
                - name, description, readme_content
                - language, topics, stars, forks
                - url, created_at, updated_at

        Returns:
            Markdown-formatted project list
        """
```

**Gemini AI Prompt Design**:

```
System Prompt:
You are a professional resume writer specializing in technical resumes for CS students.
Your task is to convert GitHub repository data into concise, impactful project
descriptions suitable for a resume.

Guidelines:
- Each project should have: title, 1-2 sentence description, key technologies,
  and 2-4 bullet points of achievements/features
- Focus on impact, complexity, and technical skills demonstrated
- Use action verbs (Built, Developed, Implemented, Designed)
- Highlight unique features or impressive metrics (stars, users, performance)
- Filter out trivial projects (homework assignments, forks without contributions)
- Prioritize projects by: stars, recent activity, technical complexity
- Maximum 15 projects total (most impressive ones)
- Format as clean markdown with proper headings and structure

User Prompt:
Here is data for {count} GitHub repositories belonging to the user:

[JSON dump of all repo data with READMEs]

Please structure these as resume-ready project descriptions in markdown format.
```

**Output Format** (`project_list.md`):
```markdown
# GitHub Projects

*Automatically extracted from GitHub profile on {date}*
*Total repositories analyzed: {count}*

---

## Project 1: [Project Name]
**Technologies**: Python, FastAPI, PostgreSQL, Docker

A brief 1-2 sentence description of what the project does and its purpose.

- Built RESTful API handling 10,000+ requests/day with 99.9% uptime
- Implemented caching layer reducing database queries by 60%
- Deployed containerized application using Docker and GitHub Actions
- Achieved 500+ stars on GitHub with active community contributions

**Repository**: [github.com/user/repo](https://github.com/user/repo)

---

## Project 2: [Another Project]
...
```

---

### 4. Prompt Engineering

**File**: `backend/config/prompts.py`

**New Constant**:
```python
PROJECT_STRUCTURING_SYSTEM_PROMPT = """
You are a professional resume writer specializing in technical resumes for
computer science students and software engineers. Your task is to convert
GitHub repository data into concise, impactful project descriptions suitable
for inclusion in a professional resume.

Guidelines for structuring projects:
1. Each project should include:
   - Clear, descriptive title
   - 1-2 sentence overview of the project's purpose and impact
   - List of key technologies used
   - 2-4 bullet points highlighting achievements, features, or technical complexity

2. Writing style:
   - Use strong action verbs (Built, Developed, Implemented, Designed, Engineered)
   - Focus on measurable impact and technical skills demonstrated
   - Highlight unique features, performance metrics, or user adoption
   - Be concise and specific (avoid vague statements)

3. Project prioritization and filtering:
   - Prioritize projects with higher stars, recent activity, and technical complexity
   - Filter out trivial projects (basic tutorials, simple homework, unmodified forks)
   - Include a maximum of 15 projects (most impressive ones only)
   - Sort by significance (most impressive first)

4. Technical emphasis:
   - Highlight architecture decisions and system design
   - Mention scalability, performance optimizations, or efficiency improvements
   - Include relevant metrics (users, throughput, response time, test coverage)
   - Showcase collaboration (contributors, pull requests, community engagement)

5. Output format:
   - Clean markdown with proper headings (##) for each project
   - Technologies listed as bold keywords
   - Bullet points for achievements/features
   - Include repository URL as clickable link

Remember: These projects will be read by recruiters and hiring managers.
Make them compelling, concrete, and focused on demonstrable skills.
"""
```

---

### 5. API Route Changes

**File**: `backend/api/routes.py`

**Endpoint**: `POST /api/resume` (upload_resume)

**Current Logic**:
```python
async def upload_resume(file: UploadFile):
    # ... validation ...
    # ... PDF parsing ...
    resume_data = gemini_service.parse_resume(pdf_text)
    # Save to resume.json
    # Return success
```

**Enhanced Logic**:
```python
async def upload_resume(file: UploadFile):
    # ... existing validation and parsing ...
    resume_data = gemini_service.parse_resume(pdf_text)

    # Save resume.json (existing)
    workspace.save_resume(resume_data)

    # NEW: Check if GitHub profile exists
    github_url = resume_data.contact_info.github

    if github_url:
        logger.info(f"GitHub profile found: {github_url}")

        try:
            # Extract GitHub projects
            github_service = GitHubService(
                github_token=settings.github_token  # Optional
            )

            # Fetch all repo data
            username = github_service.extract_username(github_url)
            repos = github_service.fetch_public_repos(username)

            # Fetch READMEs for each repo
            repos_with_readmes = []
            for repo in repos:
                readme = github_service.fetch_readme(username, repo['name'])
                repos_with_readmes.append({
                    **repo,
                    'readme_content': readme
                })

            # Structure with AI
            project_structurer = ProjectStructurerService(gemini_service)
            project_markdown = project_structurer.structure_projects(
                repos_with_readmes
            )

            # Save to project_list.md
            project_list_path = workspace.get_project_list_path()
            with open(project_list_path, 'w', encoding='utf-8') as f:
                f.write(project_markdown)

            logger.info(f"GitHub projects extracted: {len(repos)} repos")

            # Update resume data flag
            resume_data.github_projects_extracted = True
            workspace.save_resume(resume_data)

        except Exception as e:
            # Log error but don't fail the entire upload
            logger.error(f"GitHub extraction failed: {e}")
            logger.info("Continuing without GitHub projects")

    # Return success (existing)
    return ResumeUploadResponse(
        success=True,
        message="Resume uploaded and parsed successfully",
        resume_path=str(resume_path),
        github_projects_extracted=resume_data.github_projects_extracted
    )
```

---

### 6. Configuration Changes

**File**: `backend/config/__init__.py`

**Add GitHub Token**:
```python
class Settings(BaseSettings):
    # ... existing settings ...

    # GitHub API Configuration
    github_token: Optional[str] = Field(
        default=None,
        description="GitHub Personal Access Token for higher API rate limits"
    )
```

**File**: `.env.example`

**Add**:
```bash
# GitHub API (Optional - increases rate limit from 60 to 5000 requests/hour)
GITHUB_TOKEN=ghp_your_token_here_optional
```

---

### 7. Workspace Utility Changes

**File**: `backend/utils/workspace.py`

**Add New Function**:
```python
def get_project_list_path() -> Path:
    """
    Get path to GitHub projects markdown file.

    Returns:
        Path to ~/JobAgentWorkspace/project_list.md
    """
    workspace_dir = Path(settings.workspace_path).expanduser()
    return workspace_dir / "project_list.md"
```

---

### 8. New Dependencies

**File**: `pyproject.toml`

**Add**:
```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "PyGithub>=2.1.1",  # GitHub API wrapper
    "requests>=2.31.0",  # For direct API calls (alternative to PyGithub)
]
```

**Installation**:
```bash
uv add PyGithub
# OR
uv add requests
```

---

## Implementation Phases

### Phase 1: Core GitHub Extraction (MVP)
1. Create `github_service.py` with basic API integration
2. Implement username extraction and repo listing
3. Fetch README for each repo
4. Test with real GitHub profiles

### Phase 2: AI Structuring
1. Create `project_structurer.py`
2. Design and test Gemini prompt for project formatting
3. Implement markdown generation
4. Test output quality with various repo types

### Phase 3: Integration
1. Modify `routes.py` to call GitHub extraction after resume parsing
2. Update workspace utilities
3. Add configuration for GitHub token
4. Test end-to-end flow

### Phase 4: Error Handling & Edge Cases
1. Handle rate limiting gracefully
2. Handle repos without READMEs
3. Filter out low-quality/forked repos
4. Add retry logic for network failures
5. Add user feedback for long-running extractions

---

## Technical Considerations

### 1. Performance & Rate Limiting

**GitHub API Rate Limits**:
- **Unauthenticated**: 60 requests/hour
- **Authenticated**: 5,000 requests/hour

**Estimation**:
- User with 20 repos: 1 (user profile) + 1 (list repos) + 20 (READMEs) = 22 requests
- With authentication: Can handle ~227 resume uploads/hour
- Without authentication: Can handle ~2 resume uploads/hour

**Solution**:
- Require GitHub token for production use
- Implement caching (cache repo data for 24 hours)
- Add exponential backoff for rate limit errors

### 2. Processing Time

**Estimated Time**:
- GitHub API calls: ~2-5 seconds (depends on repo count)
- README fetching: ~1 second per repo
- Gemini AI structuring: ~3-5 seconds
- **Total for 20 repos**: ~25-30 seconds

**User Experience**:
- Show progress indicator: "Step 2 of 3: Extracting GitHub projects..."
- Make extraction async (don't block resume upload response)
- OR: Make it a separate endpoint that runs after upload

### 3. Data Quality

**Challenges**:
- READMEs vary widely in quality
- Some repos may be trivial (forks, homework)
- READMEs can be very long (token limits)

**Solutions**:
- Filter repos by stars/activity before README fetch
- Truncate very long READMEs (first 2000 chars)
- Let AI filter out trivial projects in structuring phase

### 4. Privacy & Security

**Considerations**:
- Only fetch **public** repositories
- Don't store GitHub token in resume.json
- Respect GitHub's API terms of service
- Don't expose user's private information

---

## File Structure After Enhancement

```
~/JobAgentWorkspace/
├── resume.json                      # Parsed resume data
├── project_list.md                  # NEW: GitHub projects (markdown)
└── jobs/
    ├── senior-backend-engineer-google/
    │   ├── job.json
    │   ├── cover_letter.tex
    │   ├── cover_letter.pdf
    │   ├── resume.tex                # Can reference project_list.md content
    │   └── resume.pdf
    └── ...
```

---

## Future Enhancements (Out of Scope)

1. **LinkedIn Integration**: Extract LinkedIn profile projects
2. **Manual Project Addition**: UI to manually add non-GitHub projects
3. **Project Filtering UI**: Let user select which projects to include
4. **Project Categories**: Categorize by language/domain (Web Dev, ML, etc.)
5. **Contribution Analysis**: Analyze commit history for actual contributions to forks
6. **Project Refresh**: Re-fetch GitHub projects on demand
7. **Multi-Source Projects**: Combine GitHub, GitLab, Bitbucket

---

## Benefits for CS Students

1. **Comprehensive Project Portfolio**: Automatically captures all public work
2. **Time Savings**: No manual project description writing
3. **Consistency**: AI ensures professional formatting across all projects
4. **Discoverability**: Highlights projects that might be forgotten
5. **Metrics**: Includes stars/forks as social proof
6. **Up-to-date**: Can be refreshed before each application cycle

---

## Testing Strategy

### Unit Tests
- `test_github_service.py`: Test username extraction, API calls
- `test_project_structurer.py`: Test markdown generation

### Integration Tests
- Test full flow with mock GitHub API
- Test error handling (rate limits, 404s, network errors)

### Manual Testing
- Test with real GitHub profiles of varying sizes
- Test with profiles containing different project types
- Verify markdown output quality and formatting

---

## Documentation Updates Required

### CLAUDE.md
- Update "Phase 1: Resume Upload & Parsing Flow" section
- Add "GitHub Project Extraction" subsection
- Document new services and their responsibilities
- Update workspace structure diagram

### README.md
- Mention GitHub project extraction feature
- Note that GitHub token is optional but recommended
- Add example of project_list.md output

### .env.example
- Add GITHUB_TOKEN with explanation

---

## Risk Assessment

### High Risk
- **Rate limiting**: Could block resume uploads if not handled
  - *Mitigation*: Require GitHub token, implement caching

### Medium Risk
- **Processing time**: 30+ seconds could feel slow
  - *Mitigation*: Async processing, clear progress indicators

- **Gemini token limits**: Many long READMEs could exceed context
  - *Mitigation*: Truncate READMEs, process in batches

### Low Risk
- **GitHub API changes**: API is stable and versioned
- **Invalid GitHub URLs**: Easy to validate and skip

---

## Success Metrics

- ✅ Successfully extracts projects for 95%+ of valid GitHub profiles
- ✅ Processing time < 45 seconds for users with < 30 repos
- ✅ AI-generated project descriptions rated "resume-ready" by users
- ✅ No failures due to rate limiting (with token)
- ✅ Zero security vulnerabilities introduced

---

## Implementation Checklist

- [ ] Create `backend/services/github_service.py`
- [ ] Create `backend/services/project_structurer.py`
- [ ] Add `PROJECT_STRUCTURING_SYSTEM_PROMPT` to `backend/config/prompts.py`
- [ ] Add `github_token` to `backend/config/__init__.py`
- [ ] Add `get_project_list_path()` to `backend/utils/workspace.py`
- [ ] Add `github_projects_extracted` field to `ResumeData` model
- [ ] Modify `upload_resume()` in `backend/api/routes.py`
- [ ] Add `PyGithub` or `requests` dependency to `pyproject.toml`
- [ ] Update `.env.example` with GitHub token
- [ ] Write unit tests for GitHub service
- [ ] Write unit tests for project structurer
- [ ] Update CLAUDE.md documentation
- [ ] Update README.md with new feature
- [ ] Test end-to-end with real GitHub profiles
- [ ] Test error handling and edge cases
- [ ] Add progress indicators to frontend

---

*Document created: 2025-12-31*
*Status: Planning Phase - Ready for Implementation*

---
---
---

# Company Research Enhancement Plan

## Overview

Enhance Phase 2 (Job Posting Extraction) to automatically research companies and extract valuable information like core values, mission, culture, and recent news. This enriched company data will be used to personalize cover letters and demonstrate genuine interest in the organization.

---

## Current Flow vs. Enhanced Flow

### Current Phase 2 Flow
```
User navigates to job page → Clicks "Generate"
→ Extract page text + URL
→ POST /api/job with {raw_text, url}
→ Gemini AI: Parse job posting (job_title, company, description)
→ Create job folder
→ Save job.json
→ Done
```

### Enhanced Phase 2 Flow
```
User navigates to job page → Clicks "Generate"
→ Extract page text + URL
→ POST /api/job with {raw_text, url}
→ Gemini AI: Parse job posting (job_title, company, description)
→ Create job folder
→ Save job.json
→ NEW: Company Research Pipeline:
    → Web Search: "{company_name} core values mission"
    → Web Search: "{company_name} company culture work environment"
    → Web Search: "{company_name} recent news achievements"
    → Fetch top 5-7 search results
    → Gemini AI: Synthesize into structured company profile
    → Save company_research.json
→ Done
```

---

## Architecture Changes

### 1. Data Model Changes

**File**: `backend/models/company.py` (NEW)

**New Models**:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CompanyResearch(BaseModel):
    """Structured company research data for personalized applications"""

    company_name: str
    research_date: datetime = Field(default_factory=datetime.now)

    # Core company information
    mission_statement: Optional[str] = Field(
        None,
        description="Company's mission or purpose statement"
    )
    core_values: List[str] = Field(
        default_factory=list,
        description="List of company's stated core values"
    )
    company_culture: Optional[str] = Field(
        None,
        description="Summary of company culture and work environment"
    )

    # Company details
    industry: Optional[str] = Field(
        None,
        description="Primary industry or sector"
    )
    company_size: Optional[str] = Field(
        None,
        description="Employee count range (e.g., '1000-5000 employees')"
    )
    headquarters: Optional[str] = Field(
        None,
        description="Location of headquarters"
    )
    founded_year: Optional[int] = None

    # Recent information
    recent_news: List[str] = Field(
        default_factory=list,
        description="Recent notable news, achievements, or initiatives (max 5)"
    )
    notable_products: List[str] = Field(
        default_factory=list,
        description="Key products, services, or projects"
    )

    # Cover letter talking points
    why_work_here: List[str] = Field(
        default_factory=list,
        description="Compelling reasons to work at this company (for cover letters)"
    )
    alignment_opportunities: List[str] = Field(
        default_factory=list,
        description="How applicant can align with company values/mission"
    )

    # Metadata
    sources: List[str] = Field(
        default_factory=list,
        description="URLs of sources used for research"
    )
    confidence_score: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in research quality (0-1)"
    )


class CompanyResearchRequest(BaseModel):
    """Request to research a company"""
    company_name: str


class CompanyResearchResponse(BaseModel):
    """Response from company research endpoint"""
    success: bool
    company_name: Optional[str] = None
    research_saved: bool = False
    error: Optional[str] = None
```

**File**: `backend/models/job.py`

**Update JobData**:
```python
class JobData(BaseModel):
    # ... existing fields ...

    company_researched: bool = Field(
        default=False,
        description="Flag indicating if company research was performed"
    )
```

---

### 2. New Service: Company Research Service

**File**: `backend/services/company_research_service.py` (NEW)

**Responsibilities**:
1. Perform web searches for company information
2. Fetch and parse search results
3. Extract relevant content from company websites, news articles, LinkedIn
4. Use Gemini AI to synthesize information into structured format
5. Handle errors and partial data gracefully

**Key Methods**:

```python
from typing import List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI

class CompanyResearchService:
    """Service for researching companies via web search and AI synthesis"""

    def __init__(self, gemini_service: GeminiService):
        """Initialize with Gemini service for AI synthesis"""
        self.gemini_service = gemini_service
        self.llm = gemini_service.llm

    def research_company(self, company_name: str) -> CompanyResearch:
        """
        Research a company and return structured data.

        Args:
            company_name: Name of the company to research

        Returns:
            CompanyResearch object with structured company information

        Raises:
            ValueError: If company research fails completely
        """
        # 1. Perform web searches
        search_results = self._perform_searches(company_name)

        # 2. Fetch content from top results
        web_content = self._fetch_web_content(search_results)

        # 3. Synthesize with AI
        company_data = self._synthesize_with_ai(
            company_name=company_name,
            web_content=web_content
        )

        return company_data

    def _perform_searches(self, company_name: str) -> Dict[str, List[dict]]:
        """
        Perform multiple web searches for different aspects of company.

        Returns:
            Dict with keys: 'core_values', 'culture', 'news'
            Each value is a list of search results
        """
        search_queries = {
            'core_values': f'{company_name} core values mission statement',
            'culture': f'{company_name} company culture work environment',
            'news': f'{company_name} recent news achievements 2025',
            'about': f'{company_name} about company products services',
        }

        results = {}
        for category, query in search_queries.items():
            # Use WebSearch or similar tool
            # Return top 3-5 results per category
            results[category] = self._web_search(query, max_results=3)

        return results

    def _fetch_web_content(
        self,
        search_results: Dict[str, List[dict]]
    ) -> List[Dict[str, str]]:
        """
        Fetch actual content from search result URLs.

        Args:
            search_results: Categorized search results

        Returns:
            List of dicts with {url, title, content, category}
        """
        web_content = []

        for category, results in search_results.items():
            for result in results[:3]:  # Top 3 per category
                try:
                    # Use WebFetch or requests to get content
                    content = self._fetch_url_content(result['url'])

                    # Truncate to avoid token limits
                    content_truncated = content[:5000]

                    web_content.append({
                        'url': result['url'],
                        'title': result['title'],
                        'content': content_truncated,
                        'category': category
                    })
                except Exception as e:
                    logger.warning(f"Failed to fetch {result['url']}: {e}")
                    continue

        return web_content

    def _synthesize_with_ai(
        self,
        company_name: str,
        web_content: List[Dict[str, str]]
    ) -> CompanyResearch:
        """
        Use Gemini AI to synthesize web content into structured company data.

        Args:
            company_name: Company name
            web_content: List of fetched web content

        Returns:
            CompanyResearch object
        """
        # Build prompt with all web content
        prompt = self._build_synthesis_prompt(company_name, web_content)

        # Use structured output
        structured_llm = self.llm.with_structured_output(
            schema=CompanyResearch,
            method="json_mode"
        )

        company_data: CompanyResearch = structured_llm.invoke(prompt)

        # Add metadata
        company_data.company_name = company_name
        company_data.sources = [item['url'] for item in web_content]

        return company_data

    def _build_synthesis_prompt(
        self,
        company_name: str,
        web_content: List[Dict[str, str]]
    ) -> str:
        """
        Build prompt for AI synthesis of company information.
        """
        # Detailed prompt construction
        # See prompts.py for full implementation
        pass

    def _web_search(self, query: str, max_results: int = 3) -> List[dict]:
        """
        Perform web search and return results.
        Uses WebSearch tool or similar.
        """
        # Implementation using available web search tools
        pass

    def _fetch_url_content(self, url: str) -> str:
        """
        Fetch content from a URL.
        Uses WebFetch tool or requests library.
        """
        # Implementation using WebFetch or requests
        pass
```

---

### 3. Prompt Engineering

**File**: `backend/config/prompts.py`

**New Constant**:

```python
COMPANY_RESEARCH_SYSTEM_PROMPT = """
You are a professional company research analyst specializing in helping job
applicants understand potential employers. Your task is to synthesize web
content about a company into a structured profile that will be used to
personalize job application materials (cover letters and resumes).

Your responsibilities:
1. Extract factual, verifiable information about the company
2. Identify core values, mission, and culture
3. Highlight recent achievements and notable initiatives
4. Generate compelling "why work here" talking points
5. Suggest ways applicants can align with company values

Guidelines for company research:

1. **Core Values & Mission**:
   - Extract the company's stated mission statement verbatim if available
   - List core values as they appear on official sources
   - Describe company culture based on employee reviews, company statements
   - Be objective - don't embellish or invent values

2. **Company Information**:
   - Identify industry, company size, headquarters location
   - Note founding year if mentioned
   - List notable products, services, or projects
   - Focus on information relevant to job seekers

3. **Recent News & Achievements**:
   - Prioritize recent news (last 6-12 months)
   - Include product launches, funding rounds, awards, expansions
   - Mention notable partnerships or initiatives
   - Maximum 5 most relevant news items

4. **Cover Letter Talking Points**:
   - Generate 3-5 compelling reasons someone would want to work here
   - Base these on: company mission, growth, innovation, culture, impact
   - Make them specific to this company (not generic statements)
   - Focus on aspects that appeal to professionals

5. **Alignment Opportunities**:
   - Suggest 3-5 ways an applicant can align with company values
   - Examples: "Contributing to sustainability initiatives", "Building scalable
     systems that impact millions", "Collaborative innovation in AI research"
   - Make these actionable and specific

6. **Quality & Confidence**:
   - Only include information you can verify from the provided sources
   - If information is scarce, be honest (don't fabricate)
   - Set confidence_score based on quality/quantity of sources:
     - 1.0: Excellent sources (official website, recent news, LinkedIn)
     - 0.7: Good sources but some gaps
     - 0.5: Limited or outdated information
     - 0.3: Very little reliable information found

7. **Writing Style**:
   - Be concise and factual
   - Use professional language
   - Avoid marketing jargon unless it's a direct quote
   - Focus on information useful for job applications

Remember: This research will be used to personalize cover letters. Prioritize
information that helps applicants demonstrate genuine interest and cultural fit.
"""


def build_company_research_prompt(
    company_name: str,
    web_content: List[Dict[str, str]]
) -> str:
    """
    Build the user prompt for company research synthesis.

    Args:
        company_name: Name of the company
        web_content: List of dicts with url, title, content, category

    Returns:
        Formatted prompt string
    """
    # Organize content by category
    content_by_category = {
        'core_values': [],
        'culture': [],
        'news': [],
        'about': []
    }

    for item in web_content:
        category = item.get('category', 'about')
        content_by_category[category].append(item)

    # Build prompt sections
    prompt_parts = [
        f"Research and synthesize information about: {company_name}\n",
        "I have gathered the following web content:\n\n"
    ]

    # Add content for each category
    for category, items in content_by_category.items():
        if items:
            prompt_parts.append(f"--- {category.upper()} ---\n")
            for item in items:
                prompt_parts.append(f"Source: {item['title']}\n")
                prompt_parts.append(f"URL: {item['url']}\n")
                prompt_parts.append(f"Content:\n{item['content']}\n\n")

    prompt_parts.append(
        f"\nPlease synthesize this information into a structured company "
        f"profile for {company_name}. Extract core values, mission, culture, "
        f"recent news, and generate compelling talking points for job applications."
    )

    return "".join(prompt_parts)
```

---

### 4. API Route Changes

**File**: `backend/api/routes.py`

**Endpoint**: `POST /api/job` (capture_job)

**Current Logic**:
```python
async def capture_job(request: JobPostingRequest):
    # ... parse job posting ...
    job_data = gemini_service.parse_job_posting(request.raw_text, request.url)
    # Create job folder
    job_slug = workspace.create_job_folder(job_data.job_title, job_data.company)
    # Save job.json
    # Return success
```

**Enhanced Logic**:
```python
async def capture_job(request: JobPostingRequest):
    # ... existing job parsing ...
    job_data = gemini_service.parse_job_posting(request.raw_text, request.url)

    # Create job folder
    job_slug = workspace.create_job_folder(job_data.job_title, job_data.company)

    # Save job.json (existing)
    job_path = workspace.get_job_path(job_slug)
    with open(job_path / "job.json", 'w') as f:
        f.write(job_data.model_dump_json(indent=2))

    # NEW: Research company
    company_name = job_data.company

    if company_name:
        logger.info(f"Researching company: {company_name}")

        try:
            # Initialize company research service
            company_research_service = CompanyResearchService(gemini_service)

            # Perform research
            company_data = company_research_service.research_company(
                company_name=company_name
            )

            # Save to company_research.json in job folder
            research_path = job_path / "company_research.json"
            with open(research_path, 'w', encoding='utf-8') as f:
                f.write(company_data.model_dump_json(indent=2))

            logger.info(
                f"Company research completed. "
                f"Confidence: {company_data.confidence_score}"
            )

            # Update job data flag
            job_data.company_researched = True

            # Re-save job.json with updated flag
            with open(job_path / "job.json", 'w') as f:
                f.write(job_data.model_dump_json(indent=2))

        except Exception as e:
            # Log error but don't fail the entire job capture
            logger.error(f"Company research failed: {e}")
            logger.info("Continuing without company research")

    # Return success
    return JobCaptureResponse(
        success=True,
        job_slug=job_slug,
        company_researched=job_data.company_researched
    )
```

---

### 5. Cover Letter Generation Integration

**File**: `backend/services/latex_generator.py`

**Modify**: `generate_cover_letter()` method

**Current Logic**:
```python
def generate_cover_letter(
    resume_data: ResumeData,
    job_data: JobData
) -> str:
    # Build prompt with resume + job
    # Generate with Gemini
    # Return LaTeX
```

**Enhanced Logic**:
```python
def generate_cover_letter(
    resume_data: ResumeData,
    job_data: JobData,
    company_research: Optional[CompanyResearch] = None
) -> str:
    """
    Generate cover letter with optional company research enrichment.

    Args:
        resume_data: Parsed resume data
        job_data: Job posting data
        company_research: Optional company research data

    Returns:
        LaTeX code for cover letter
    """
    # Build enhanced prompt
    prompt = self._build_cover_letter_prompt(
        resume_data=resume_data,
        job_data=job_data,
        company_research=company_research
    )

    # Generate with Gemini
    response = self.llm.invoke(prompt)
    latex_code = self._extract_latex(response.content)

    return latex_code


def _build_cover_letter_prompt(
    self,
    resume_data: ResumeData,
    job_data: JobData,
    company_research: Optional[CompanyResearch] = None
) -> str:
    """Build prompt for cover letter generation with company research."""

    prompt_parts = [
        COVER_LETTER_SYSTEM_PROMPT,
        "\n\n--- RESUME DATA ---\n",
        resume_data.model_dump_json(indent=2),
        "\n\n--- JOB POSTING ---\n",
        job_data.model_dump_json(indent=2),
    ]

    # NEW: Add company research if available
    if company_research:
        prompt_parts.extend([
            "\n\n--- COMPANY RESEARCH ---\n",
            company_research.model_dump_json(indent=2),
            "\n\nUse this company research to:",
            "\n- Demonstrate specific knowledge of company values and culture",
            "\n- Reference recent company achievements or initiatives",
            "\n- Explain genuine alignment with company mission",
            "\n- Show enthusiasm based on specific company attributes",
            "\n- Make the cover letter highly personalized and authentic",
        ])

    prompt_parts.append(
        "\n\nGenerate a compelling, personalized cover letter in LaTeX format."
    )

    return "".join(prompt_parts)
```

**File**: `backend/api/routes.py`

**Modify**: `generate_documents()` endpoint

```python
async def generate_documents(request: GenerateRequest):
    # ... load resume.json and job.json ...

    # NEW: Load company research if available
    company_research = None
    research_path = job_path / "company_research.json"

    if research_path.exists():
        with open(research_path, 'r') as f:
            research_data = json.load(f)
            company_research = CompanyResearch(**research_data)
        logger.info("Using company research for cover letter generation")

    # Generate cover letter with company research
    cover_letter_tex = latex_generator.generate_cover_letter(
        resume_data=resume_data,
        job_data=job_data,
        company_research=company_research  # NEW
    )

    # ... rest of generation flow ...
```

---

### 6. Updated Cover Letter System Prompt

**File**: `backend/config/prompts.py`

**Update**: `COVER_LETTER_SYSTEM_PROMPT`

```python
COVER_LETTER_SYSTEM_PROMPT = """
You are a professional cover letter writer specializing in creating compelling,
personalized cover letters for job applications.

# Guidelines for cover letter writing:

1. **Structure** (3-4 paragraphs):
   - Opening: Express enthusiasm for the specific role and company
   - Body (1-2 paragraphs): Highlight relevant experience and skills
   - Alignment: Show understanding of company values and culture
   - Closing: Reiterate interest and call to action

2. **Personalization**:
   - Reference specific job requirements and how you meet them
   - Mention company values, mission, or recent achievements
   - Demonstrate genuine interest (not generic statements)
   - Use company research to show you've done your homework

3. **Company Research Integration** (if provided):
   - Reference company core values naturally in context
   - Mention recent news, products, or initiatives
   - Align your experience with company mission
   - Show enthusiasm for specific aspects of company culture
   - Use "why work here" points to demonstrate fit

4. **Writing style**:
   - Professional but warm tone
   - Active voice and strong action verbs
   - Specific examples and achievements
   - Concise (keep under 1 page)
   - Authentic and genuine (not overly formal)

5. **LaTeX formatting**:
   - Use standard document class (letter, article)
   - Clean, professional layout
   - Self-contained (no external file references)
   - Proper spacing and margins

Remember: A great cover letter tells a story of why you're the right fit for
THIS role at THIS company. Use company research to make it specific and authentic.
"""
```

---

### 7. Configuration Changes

**File**: `backend/config/__init__.py`

No additional configuration needed - uses existing `GOOGLE_API_KEY` for Gemini.

Web search functionality will use:
- Built-in WebSearch tool (if available)
- OR external API (Serper, SerpAPI, etc.) - would require new API key

**Optional Addition** (if using external search API):
```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Web Search API (Optional)
    search_api_key: Optional[str] = Field(
        default=None,
        description="API key for web search (Serper, SerpAPI, etc.)"
    )
    search_api_provider: str = Field(
        default="serper",
        description="Search API provider: 'serper', 'serpapi', 'builtin'"
    )
```

---

### 8. Workspace Structure After Enhancement

```
~/JobAgentWorkspace/
├── resume.json                           # Parsed resume data
├── project_list.md                       # GitHub projects (from Phase 1 enhancement)
└── jobs/
    ├── senior-backend-engineer-google/
    │   ├── job.json                      # Job posting data
    │   ├── company_research.json         # NEW: Company research data
    │   ├── cover_letter.tex              # Uses company research
    │   ├── cover_letter.pdf
    │   ├── resume.tex
    │   └── resume.pdf
    └── ...
```

---

## Implementation Phases

### Phase 1: Core Company Research
1. Create `CompanyResearch` data model in `backend/models/company.py`
2. Create `CompanyResearchService` with web search integration
3. Implement basic web search and content fetching
4. Test with known companies (Google, Microsoft, Amazon)

### Phase 2: AI Synthesis
1. Design `COMPANY_RESEARCH_SYSTEM_PROMPT` in `prompts.py`
2. Implement `_synthesize_with_ai()` method
3. Test synthesis quality with various companies
4. Iterate on prompt based on output quality

### Phase 3: Integration with Job Capture
1. Modify `capture_job()` endpoint to trigger research
2. Save `company_research.json` in job folders
3. Update `JobData` model with `company_researched` flag
4. Test end-to-end job capture flow

### Phase 4: Cover Letter Enhancement
1. Modify `generate_cover_letter()` to accept company research
2. Update cover letter system prompt
3. Modify `generate_documents()` to load company research
4. Test cover letter quality improvements

### Phase 5: Error Handling & Optimization
1. Handle companies with minimal online presence
2. Implement caching for duplicate company research
3. Add retry logic for failed web fetches
4. Optimize search queries for better results

---

## Technical Considerations

### 1. Web Search Integration

**Options**:

**Option A: Use Built-in WebSearch Tool** (Preferred if available)
- Pros: No additional API keys, built-in Claude Code functionality
- Cons: May have rate limits or restrictions

**Option B: External Search API**
- **Serper API**: $5/1000 searches, fast, reliable
- **SerpAPI**: $50/5000 searches, comprehensive
- **Brave Search API**: Free tier available
- Pros: More control, higher rate limits
- Cons: Additional API key required, extra cost

**Recommendation**: Start with WebSearch tool, fallback to external API if needed.

### 2. Performance & Timing

**Estimated Time** (per company):
- Web searches: ~2-3 seconds (4 queries)
- Content fetching: ~3-5 seconds (fetch 12 URLs)
- AI synthesis: ~3-5 seconds
- **Total**: ~8-13 seconds per company

**Impact on User Experience**:
- Job capture becomes ~10 seconds longer
- Still acceptable with progress indicators
- Could be made async/background process

### 3. Data Quality Challenges

**Challenges**:
- Small/unknown companies may have limited online presence
- Information may be outdated
- Marketing content vs. authentic company culture
- Conflicting information from different sources

**Solutions**:
- Use `confidence_score` to indicate data quality
- Prioritize official sources (company website, LinkedIn)
- Include source URLs for transparency
- Gracefully handle missing information (don't fabricate)

### 4. Caching Strategy

**Problem**: Same company researched multiple times (multiple job postings)

**Solution**:
```
~/JobAgentWorkspace/
├── company_cache/
│   ├── google.json         # Cached for 7 days
│   ├── microsoft.json
│   └── amazon.json
```

**Cache Logic**:
- Check cache before researching
- Use cached data if < 7 days old
- Invalidate on manual refresh request
- Saves time and API calls

---

## Cover Letter Quality Improvements

### Before (Without Company Research):
```
Dear Hiring Manager,

I am writing to express my interest in the Software Engineer position at Google.

I have 3 years of experience in full-stack development using Python and
JavaScript. In my previous role, I built scalable web applications and
improved system performance.

I am excited about this opportunity and believe my skills would be a great fit.

Best regards,
[Name]
```

### After (With Company Research):
```
Dear Hiring Manager,

I am thrilled to apply for the Software Engineer position at Google. As someone
deeply aligned with Google's mission to "organize the world's information and
make it universally accessible," I've followed Google's recent advances in AI
with great interest, particularly the Gemini model launch and its integration
across Google products.

I have 3 years of experience building scalable systems that impact millions of
users. At my previous company, I architected a microservices platform that
reduced latency by 60% and improved system reliability to 99.9% uptime - the
kind of engineering excellence that aligns with Google's focus on building
products at planetary scale.

What excites me most about Google is your commitment to "boldness and innovation"
as a core value. I resonate with this deeply - in my current role, I proposed
and led a complete system redesign that initially seemed risky but ultimately
transformed our infrastructure. I'm eager to bring this same innovative thinking
to Google's collaborative, high-impact engineering culture.

I would love the opportunity to contribute to Google's mission and learn from
some of the world's best engineers.

Best regards,
[Name]
```

**Key Improvements**:
- ✅ Specific mission statement reference
- ✅ Recent company news (Gemini launch)
- ✅ Core value alignment ("boldness and innovation")
- ✅ Cultural fit demonstration
- ✅ Genuine enthusiasm based on research
- ✅ More personalized and authentic

---

## Benefits

### For Job Applicants:
1. **Highly Personalized Cover Letters**: Reference actual company values and news
2. **Demonstrates Research**: Shows genuine interest beyond job description
3. **Cultural Fit**: Align experience with company culture and mission
4. **Authenticity**: Specific details make cover letters more believable
5. **Competitive Edge**: Stand out with knowledge of recent achievements

### For Recruiters/Hiring Managers:
1. **Clear Signal**: Applicant did their homework
2. **Cultural Alignment**: Values match demonstrated upfront
3. **Quality Filter**: Less generic, more thoughtful applications

---

## Testing Strategy

### Unit Tests
- `test_company_research_service.py`:
  - Test web search functionality
  - Test content fetching
  - Test AI synthesis
  - Test error handling (no results, failed fetches)

- `test_company_models.py`:
  - Test Pydantic model validation
  - Test JSON serialization

### Integration Tests
- Test full flow with mock web search
- Test cover letter generation with/without company research
- Test caching mechanism
- Test error handling when research fails

### Manual Testing
- Test with large, well-known companies (Google, Amazon, Microsoft)
- Test with small/unknown companies
- Test with startups vs. established companies
- Verify cover letter quality improvements
- Check confidence scores accuracy

### Quality Evaluation
- Compare cover letters with vs. without company research
- Measure user satisfaction with personalization
- Track confidence scores distribution
- Monitor API costs and performance

---

## Risk Assessment

### High Risk
- **Web search quality**: Poor search results = poor research
  - *Mitigation*: Use multiple search queries, prioritize official sources

- **API costs**: External search APIs can be expensive
  - *Mitigation*: Implement caching, use built-in tools when possible

### Medium Risk
- **Processing time**: 10+ seconds added to job capture
  - *Mitigation*: Clear progress indicators, consider async processing

- **Data accuracy**: Web content may be outdated or incorrect
  - *Mitigation*: Use confidence scores, include source URLs, prioritize recent content

### Low Risk
- **Privacy concerns**: All research is from public sources
- **Rate limiting**: Can be managed with caching
- **Model hallucination**: Structured output reduces risk

---

## Success Metrics

- ✅ Successfully researches 90%+ of companies (confidence > 0.5)
- ✅ Processing time < 15 seconds per company
- ✅ Cover letters demonstrably more personalized (user feedback)
- ✅ 80%+ of companies have mission/values extracted
- ✅ Cache hit rate > 40% (for repeated companies)
- ✅ Zero API cost overruns (if using paid search API)

---

## Implementation Checklist

### Models & Data
- [ ] Create `backend/models/company.py` with `CompanyResearch` model
- [ ] Update `JobData` model with `company_researched` flag
- [ ] Create `JobCaptureResponse` with company research status

### Services
- [ ] Create `backend/services/company_research_service.py`
- [ ] Implement web search integration (WebSearch tool or external API)
- [ ] Implement web content fetching
- [ ] Implement AI synthesis method

### Prompts
- [ ] Add `COMPANY_RESEARCH_SYSTEM_PROMPT` to `backend/config/prompts.py`
- [ ] Add `build_company_research_prompt()` function
- [ ] Update `COVER_LETTER_SYSTEM_PROMPT` with company research guidelines

### API Routes
- [ ] Modify `capture_job()` to trigger company research
- [ ] Save `company_research.json` in job folders
- [ ] Modify `generate_documents()` to load company research

### Cover Letter Integration
- [ ] Update `generate_cover_letter()` signature to accept company research
- [ ] Modify `_build_cover_letter_prompt()` to include research
- [ ] Test cover letter quality improvements

### Optimization
- [ ] Implement company research caching (7-day TTL)
- [ ] Add error handling for failed research
- [ ] Add retry logic for web fetches
- [ ] Optimize search queries

### Testing
- [ ] Write unit tests for `CompanyResearchService`
- [ ] Write unit tests for company models
- [ ] Write integration tests for full flow
- [ ] Manual testing with various company types
- [ ] Quality evaluation of generated cover letters

### Documentation
- [ ] Update CLAUDE.md with company research flow
- [ ] Update README.md with new feature
- [ ] Document search API setup (if using external)
- [ ] Add example company_research.json to docs

### Frontend (Optional)
- [ ] Add progress indicator: "Researching company..."
- [ ] Show company research status in UI
- [ ] Add manual refresh button for company research

---

## Future Enhancements (Out of Scope)

1. **Company Comparison**: Compare multiple companies for decision-making
2. **Glassdoor Integration**: Include employee reviews and ratings
3. **Salary Data**: Include salary ranges from Glassdoor/Levels.fyi
4. **Interview Prep**: Generate company-specific interview questions
5. **Company News Alerts**: Notify when new news about target companies
6. **LinkedIn Company Page**: Extract data from LinkedIn company pages
7. **Manual Research Input**: Allow users to add custom company notes
8. **Research Quality Feedback**: Let users rate research accuracy

---

## Cost Analysis (if using external search API)

### Serper API Pricing
- $5 per 1,000 searches
- 4 searches per company = $0.02 per company
- 100 job applications = $2.00

### Expected Usage
- Average user: 10-50 job applications per month
- Cost per user: $0.20 - $1.00/month
- Very affordable for the value provided

### Recommendation
- Start with built-in WebSearch (free)
- Offer external API as premium option
- Implement caching to minimize API calls

---

*Section added: 2025-12-31*
*Status: Planning Phase - Ready for Implementation*
