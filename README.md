# JobAgent0

**AI-Powered Job Application Automation**

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Status](https://img.shields.io/badge/status-MVP%20Complete-success)

> Automate your job application workflow with AI-generated, tailored resumes and cover letters for every job posting.

---

## What is JobAgent0?

JobAgent0 is a Chrome extension powered by Google's Gemini AI that streamlines the job application process. Upload your resume once, and for each job posting you find, JobAgent0 automatically generates a tailored resume and cover letter optimized for that specific role.

Built with a FastAPI backend and modern Chrome Extension frontend, JobAgent0 processes everything **locally** for maximum privacy and security. Your resume data never leaves your machine.

**Tech Stack**: Python 3.12+ • FastAPI • Gemini AI • LangChain • Chrome Extension (Manifest V3) • LaTeX

---

## Features

✨ **AI-Powered Resume Parsing** - Extracts structured data from PDF resumes using Gemini 2.0 Flash
🎯 **Job Posting Capture** - Automatically extracts job requirements from any web page
📄 **Tailored Cover Letters** - Generates customized cover letters highlighting relevant experience
🔄 **Customized Resumes** - Creates job-specific resumes emphasizing matching skills
📑 **LaTeX Document Generation** - Professional PDF output using LaTeX compilation
🔒 **Privacy-First Design** - All processing happens locally on your machine

---

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Google Chrome browser
- Gemini API key ([Get one here](https://ai.google.dev/))
- `uv` package manager ([Install here](https://github.com/astral-sh/uv))

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd resume
   ```

2. **Install dependencies** (use `uv`, not `pip`)
   ```bash
   uv sync
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

4. **Run the backend server**
   ```bash
   uvicorn backend.main:app --reload --host localhost --port 8000
   ```

   The API will be available at `http://localhost:8000`

### Chrome Extension Setup

1. **Open Chrome Extensions page**
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top-right)

2. **Load the extension**
   - Click "Load unpacked"
   - Select the `/frontend` directory from this repository

3. **Start using JobAgent0**
   - Click the extension icon
   - Upload your resume (PDF format)
   - Navigate to any job posting
   - Click "Generate" to create tailored documents

---

## Usage

1. **Upload Your Resume** - Click the JobAgent0 extension and upload your PDF resume
2. **Find a Job Posting** - Navigate to any job posting on the web
3. **Generate Documents** - Click "Generate" to create a tailored resume and cover letter

Generated documents are saved to `~/JobAgentWorkspace/jobs/<job-slug>/` as PDF files.

---

## Project Structure

```
resume/
├── backend/              # FastAPI server
│   ├── api/             # API routes and endpoints
│   ├── models/          # Pydantic data models
│   ├── services/        # Business logic (PDF parsing, AI, LaTeX)
│   └── main.py          # Application entry point
│
├── frontend/            # Chrome Extension (Manifest V3)
│   ├── manifest.json    # Extension configuration
│   ├── popup.html       # Main UI
│   ├── popup.js         # Extension logic
│   └── content.js       # Job posting extraction
│
└── JobAgentWorkspace/   # Generated documents (created at runtime)
    ├── resume.json      # Parsed resume data
    └── jobs/            # Job-specific folders with PDFs
```

For detailed architecture and development guidelines, see [`CLAUDE.md`](CLAUDE.md).

---

## Development

### Running in Development Mode

**Backend with auto-reload:**
```bash
uvicorn backend.main:app --reload --host localhost --port 8000
```

**Testing the extension:**
- Make changes to files in `/frontend`
- Click "Reload" button on extension card in `chrome://extensions/`
- Test changes immediately

### Key Commands

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --all-extras

# Run tests (when available)
pytest
```

**Important**: This project uses `uv` for package management, not `pip`. Always use `uv sync` or `uv add <package>`.

---

## Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- Python 3.12+ - Latest Python features
- Gemini AI (2.0 Flash) - AI-powered document generation
- LangChain - LLM framework with structured output
- PyMuPDF - PDF parsing with layout preservation
- python-magic - MIME type validation for security

**Frontend:**
- Chrome Extension (Manifest V3) - Secure, modern extension architecture
- Vanilla JavaScript - No framework dependencies
- Custom fonts (GC-Matrix, Reddit Sans) - Professional branding

**Document Generation:**
- LaTeX - Professional document typesetting
- pdflatex - PDF compilation

**Package Manager:**
- uv - Fast, reliable Python package management

---

## Contributing

Contributions are welcome! This project is currently at **Phase 1 MVP** status with core functionality complete.

For development guidelines, architectural patterns, and implementation details, please refer to [`CLAUDE.md`](CLAUDE.md).

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Built with [Google Gemini AI](https://ai.google.dev/)
- Uses [LangChain](https://www.langchain.com/) for LLM integration
- Inspired by the need to streamline job applications

---

**Made with AI for job seekers everywhere** 🚀
