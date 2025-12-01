# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**JobAgent0** is a professional Chrome extension that uses AI to automate job application document generation. The system parses uploaded resumes into structured JSON and generates tailored cover letters and resumes for specific job postings using Gemini AI.

**Current Status**: Phase 1 MVP - **Complete**
- ✅ Resume upload and parsing with AI
- ✅ Job posting capture from web pages
- ✅ LaTeX document generation (cover letters and resumes)
- ✅ Modern UI with dark/monochrome branding
- ✅ Secure content script injection
- ✅ Progress indicators and enhanced UX

## Development Commands

### Backend Development

```bash
# Install dependencies (use uv, not pip - this is an externally managed environment)
uv sync

# Install with dev dependencies
uv sync --all-extras

# Run backend server (development mode with auto-reload)
uvicorn backend.main:app --reload --host localhost --port 8000

# Alternative: Run via Python module
python -m backend.main

# Run tests (when available)
pytest
```

### Environment Setup

Required: Create `.env` file from `.env.example` with valid `GOOGLE_API_KEY` (Gemini API key).

### Chrome Extension Development

Load unpacked extension from `/frontend` directory in Chrome at `chrome://extensions/` with Developer mode enabled.

## Architecture Overview

### Backend Flow

The resume parsing pipeline follows this sequence:

1. **API Entry** (`backend/api/routes.py`): FastAPI endpoint receives PDF upload
2. **File Validation**: Multi-layer security validation
   - File extension check (.pdf only)
   - File size validation (max 10MB)
   - **MIME type validation** using python-magic (prevents malicious files disguised as PDFs)
3. **PDF Parsing** (`backend/services/pdf_parser.py`): PyMuPDF4LLMLoader extracts text while preserving layout
4. **AI Parsing** (`backend/services/gemini_service.py`): Gemini 2.0 Flash converts text to structured JSON
5. **Data Storage**: Saves to `~/JobAgentWorkspace/resume.json`

### Key Architectural Patterns

**Structured Output with LangChain**: The system uses LangChain's `with_structured_output()` method with Gemini's JSON mode to enforce Pydantic schema compliance. This is critical for maintaining data integrity.

```python
structured_llm = self.llm.with_structured_output(
    schema=ResumeData, method="json_mode"
)
resume_data: ResumeData = structured_llm.invoke(prompt)
```

**Modern FastAPI Lifespan Management**: Uses the modern `lifespan` context manager pattern instead of deprecated `@app.on_event()` decorators. This ensures compatibility with FastAPI 0.109.0+ and provides a clean way to handle both startup and shutdown events.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting JobAgent0 Resume Parser")
    ensure_workspace_exists()
    yield
    # Shutdown
    logger.info("Shutting down JobAgent0 Resume Parser")

app = FastAPI(lifespan=lifespan)
```

**Settings Management**: Uses Pydantic Settings with `.env` file. The `Settings` class in `backend/config.py` provides properties like `workspace_path` (expands `~`) and `origins_list` (parses comma-separated CORS origins).

**Workspace Organization**: All data lives in `~/JobAgentWorkspace/`:
- `resume.json` - Parsed resume data
- `jobs/` - Future job-specific folders (Phase 2+)

Workspace path resolution happens in `backend/utils/workspace.py` using `settings.workspace_path`.

**CORS Configuration**: FastAPI CORS middleware is configured to accept `chrome-extension://*` and `http://localhost:*` origins. These are parsed from the `ALLOWED_ORIGINS` env var by `settings.origins_list`.

### Data Models

The Pydantic models in `backend/models/resume.py` are comprehensive and designed to preserve ALL information from resumes. Key models:
- `ResumeData`: Root model containing all resume sections
- `ContactInfo`, `Education`, `Experience`, `Project`, `Skill`, etc.
- `raw_text` field preserves original PDF text

When modifying these models, ensure backward compatibility with existing `resume.json` files.

### Chrome Extension Architecture

**Manifest V3** extension with modern, secure design:

**Core Files**:
- `popup.html`: Main UI structure with semantic sections
- `popup.css`: Modern design system with custom fonts and dark theme
- `popup.js`: Handles file upload, state management, API communication
- `content.js`: Dynamically injected for job posting extraction
- `background.js`: Service worker (minimal use currently)
- `manifest.json`: Extension configuration with minimal permissions

**Security & Permissions**:
- **Dynamic Content Script Injection**: Uses `chrome.scripting.executeScript()` instead of `content_scripts` with `<all_urls>`
- **Principle of Least Privilege**: Only requests `activeTab`, `storage`, `tabs`, and `scripting` permissions
- **Temporary Access**: Content script injected only when user clicks "Generate" button
- **No Permanent Monitoring**: Extension cannot read all browsing activity

**Design System**:
- **Typography**:
  - GC-Matrix font for "JobAgent0" logo (distinctive branding)
  - Reddit Sans font for interface text (modern readability)
- **Color Scheme**: Dark/monochrome theme
  - Primary: #1A1A1A (near black for buttons)
  - Accent: #2C3E50 (dark slate for hover states)
  - Maintains green success (#4CAF50) and red error (#C62828) states
- **Visual Elements**:
  - Modern rounded corners (12-16px on buttons/containers)
  - Material Design-inspired shadows for depth
  - Smooth transitions with cubic-bezier easing
  - Progress indicators for multi-step operations

**State Management**:
- Chrome Storage API: Persists `resumeUploaded` state
- Loading states with progress indicators ("Step 1 of 3")
- Descriptive loading messages for better UX

Extension expects backend running locally at `http://localhost:8000`. No remote deployment in Phase 1.

## Important Implementation Notes

### Package Management

This project uses `uv` for package management because it's an externally managed Python environment. Never use `pip install` - always use `uv sync` or `uv add <package>`.

**Key Dependencies**:
- `python-magic`: Required for MIME type validation to prevent malicious file uploads
- `langchain-google-genai`: For Gemini AI integration
- `fastapi`: Web framework with modern lifespan management
- `pymupdf4llm`: PDF parsing while preserving layout

### Gemini API Usage

Model: `gemini-2.0-flash-exp` with temperature=0 for deterministic extraction. The prompt in `_build_parsing_prompt()` emphasizes preservation of ALL information - do not summarize or omit content.

### Error Handling

- PDF parsing errors raise `ValueError` in `PDFParserService`
- API routes catch `ValueError` and return HTTP 400
- Generic exceptions in routes return `ResumeUploadResponse` with `success=false` and `error` message

### Security Validation

**Multi-Layer File Upload Security** (`backend/api/routes.py`):

1. **File Extension Check**: Basic validation that filename ends with `.pdf`
2. **File Size Limit**: Maximum 10MB to prevent DoS attacks
3. **MIME Type Validation**: Uses `python-magic` library to verify actual file content matches PDF signature
   - Reads file magic bytes to determine true file type
   - Rejects files with mismatched MIME types (e.g., executables renamed as `.pdf`)
   - Logs security warnings when invalid MIME types are detected

```python
# MIME type validation prevents malicious uploads
mime = magic.from_buffer(content, mime=True)
if mime != 'application/pdf':
    logger.warning(f"Invalid MIME type detected: {mime}")
    raise HTTPException(status_code=400, detail="Invalid file type")
```

This defense-in-depth approach protects against:
- Malicious executables disguised as PDFs
- Script injection attacks
- File type confusion vulnerabilities

### Temporary File Management

The resume upload endpoint uses `tempfile.NamedTemporaryFile` for PDF storage and ensures cleanup in a `finally` block. This pattern should be maintained for any file handling.

## UI/UX Implementation Details

### Custom Fonts
Located in `/frontend/font/`:
- `GC-Matrix-BF68a58803088a3.ttf`: Logo/title font (67KB)
- `RedditSansFudge-Regular-BF651644efef8fa.ttf`: Interface font (146KB)

Fonts are loaded via `@font-face` in `popup.css` and tracked in git.

### Loading Experience
Multi-step progress indicators with descriptive messages:
- **Resume Upload**: "Step 1 of 1: Uploading Resume" → "Analyzing your resume with AI..."
- **Job Extraction**: "Step 1 of 3: Extracting Job Posting" → "Reading job requirements from the page..."
- **Job Analysis**: "Step 2 of 3: Analyzing Job Requirements" → "Understanding role expectations and required skills..."
- **Document Generation**: "Step 3 of 3: Generating Documents" → "Creating tailored resume and cover letter using AI..."

### Button Layout
- Grouped related actions with `.button-group` class using flexbox
- 12px gap between buttons for visual rhythm
- Primary actions use dark gradient buttons with enhanced hover effects
- Secondary actions use light gray gradient buttons

### Accessibility
- WCAG AAA contrast ratios (16.1:1) for dark buttons on white
- Clear success (green) and error (red) messaging maintained
- Smooth animations with cubic-bezier easing
- Touch-friendly button sizes (44px+ minimum)

## Git Ignore

The following files/folders are excluded from version control:
- `resume.json`: User's parsed resume data
- `JobAgentWorkspace/`: User-generated workspace with job-specific data
- `.env`: Environment variables with API keys
- `.venv`, `venv/`: Python virtual environments
- `__pycache__/`, `*.pyc`: Python cache files

## Development Best Practices

### When Adding Features
1. Maintain the dark/monochrome design system
2. Use Reddit Sans for all UI text except the logo
3. Follow the 12-16px border-radius pattern for consistency
4. Add descriptive loading messages for long-running operations
5. Use Material Design shadow guidelines for depth
6. Ensure WCAG AA minimum contrast ratios

### When Modifying Security
- Never use `<all_urls>` or overly broad permissions
- Inject content scripts dynamically only when needed
- Use `activeTab` for temporary access patterns
- Validate all user inputs on both frontend and backend
- **ALWAYS use MIME type checking for file uploads** - Never rely solely on file extensions
- Use defense-in-depth: combine file extension, size, and MIME type validation
- Log security warnings when suspicious files are detected
- Keep dependencies updated to avoid known vulnerabilities (especially FastAPI, python-magic)

### When Updating Branding
- GC-Matrix font is reserved for "JobAgent0" logo only
- Maintain dark (#1A1A1A, #2C3E50) as primary brand colors
- Keep green (#4CAF50) for success states
- Keep red (#C62828) for error states
- Test font loading in browser DevTools Network tab

## Future Enhancements

**Potential improvements** (not currently planned):
- Dark mode support for entire interface
- Docker container setup for easier deployment
- Automated testing suite (pytest for backend, Jest for frontend)
- Custom LaTeX templates via UI
- Batch processing for multiple job applications
- Analytics dashboard for application tracking
- Cross-browser support (Firefox, Edge)

When implementing future features, maintain the workspace-based data organization pattern and modern design system.
- Always update @CLAUDE.md after any filechanges.