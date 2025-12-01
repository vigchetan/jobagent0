# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JobApp MVP is a Chrome extension that uses AI to automate job application document generation. The system parses uploaded resumes into structured JSON and will eventually generate tailored cover letters and resumes for specific job postings.

Current Status: Phase 1 (Resume Upload & Parsing) - Complete

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
2. **PDF Parsing** (`backend/services/pdf_parser.py`): PyMuPDF4LLMLoader extracts text while preserving layout
3. **AI Parsing** (`backend/services/gemini_service.py`): Gemini 2.0 Flash converts text to structured JSON
4. **Data Storage**: Saves to `~/JobAgentWorkspace/resume.json`

### Key Architectural Patterns

**Structured Output with LangChain**: The system uses LangChain's `with_structured_output()` method with Gemini's JSON mode to enforce Pydantic schema compliance. This is critical for maintaining data integrity.

```python
structured_llm = self.llm.with_structured_output(
    schema=ResumeData, method="json_mode"
)
resume_data: ResumeData = structured_llm.invoke(prompt)
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

**Manifest V3** extension with:
- `popup.js`: Handles file upload, communicates with backend at `http://localhost:8000/api`
- `background.js`: Service worker (minimal use currently)
- Chrome Storage API: Persists `resumeUploaded` state

Extension expects backend running locally. No remote deployment in Phase 1.

## Important Implementation Notes

### Package Management

This project uses `uv` for package management because it's an externally managed Python environment. Never use `pip install` - always use `uv sync` or `uv add <package>`.

### Gemini API Usage

Model: `gemini-2.0-flash-exp` with temperature=0 for deterministic extraction. The prompt in `_build_parsing_prompt()` emphasizes preservation of ALL information - do not summarize or omit content.

### Error Handling

- PDF parsing errors raise `ValueError` in `PDFParserService`
- API routes catch `ValueError` and return HTTP 400
- Generic exceptions in routes return `ResumeUploadResponse` with `success=false` and `error` message

### Temporary File Management

The resume upload endpoint uses `tempfile.NamedTemporaryFile` for PDF storage and ensures cleanup in a `finally` block. This pattern should be maintained for any file handling.

## Future Phases (Not Yet Implemented)

- Phase 2: Job posting capture via content scripts
- Phase 3: LaTeX-based document generation
- Phase 4: PDF compilation and download
- Phase 5: Template customization

When implementing these phases, maintain the workspace-based data organization pattern.
