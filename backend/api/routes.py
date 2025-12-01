"""API routes for resume upload and processing"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.models.resume import ResumeUploadResponse
from backend.models.job import JobPostingRequest, JobCaptureResponse
from backend.models.generation import GenerateRequest, GenerateResponse
from backend.services.pdf_parser import PDFParserService
from backend.services.gemini_service import GeminiResumeParser
from backend.services.latex_generator import LaTeXGeneratorService
from backend.services.pdf_compiler import PDFCompilerService
from backend.utils.workspace import ensure_workspace_exists, get_resume_path, create_job_folder, get_jobs_dir
from pathlib import Path
import tempfile
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and parse resume PDF.

    Steps:
    1. Validate file is PDF
    2. Save to temporary location
    3. Parse PDF using PyMuPDF4LLMLoader
    4. Extract structured data using Gemini
    5. Save to workspace/resume.json
    6. Return success response

    Args:
        file: The uploaded PDF file

    Returns:
        ResumeUploadResponse with success status and resume path

    Raises:
        HTTPException: If validation fails or processing errors occur
    """
    try:
        # Validate file type
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        logger.info(f"Received resume upload: {file.filename}")

        # Validate file size (max 10MB)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400, detail="File size must be less than 10MB"
            )

        # Ensure workspace exists
        ensure_workspace_exists()

        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)

        try:
            # Parse PDF using PyMuPDF4LLMLoader
            logger.info("Parsing PDF...")
            resume_text = PDFParserService.load_pdf(tmp_path)

            # Parse with Gemini
            logger.info("Extracting structured data with Gemini...")
            gemini_parser = GeminiResumeParser()
            output_path = get_resume_path()
            resume_data = gemini_parser.parse_resume(resume_text, output_path)

            logger.info("Resume processing completed successfully")

            return ResumeUploadResponse(
                success=True,
                message="Resume uploaded and parsed successfully",
                resume_path=str(output_path),
            )

        finally:
            # Clean up temporary file
            tmp_path.unlink(missing_ok=True)

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return ResumeUploadResponse(
            success=False, message="Failed to process resume", error=str(e)
        )


@router.post("/job", response_model=JobCaptureResponse)
async def capture_job(job_request: JobPostingRequest):
    """
    Capture and parse job posting.

    Steps:
    1. Extract structured data from job posting text using Gemini
    2. Create job-specific folder with sanitized slug
    3. Save to workspace/jobs/<slug>/job.json
    4. Return success response with job_slug

    Args:
        job_request: JobPostingRequest containing raw_text and url

    Returns:
        JobCaptureResponse with success status and job_slug

    Raises:
        HTTPException: If processing errors occur
    """
    try:
        logger.info(f"Received job posting from URL: {job_request.url}")

        # Validate input
        if not job_request.raw_text.strip():
            raise HTTPException(status_code=400, detail="Job posting text cannot be empty")

        if not job_request.url.strip():
            raise HTTPException(status_code=400, detail="Job URL cannot be empty")

        # Ensure workspace exists
        ensure_workspace_exists()

        # Parse job posting with Gemini (without saving yet)
        logger.info("Extracting structured job data with Gemini...")
        gemini_parser = GeminiResumeParser()

        # We need to parse first to get job_title and company for folder creation
        # So we'll create a temporary path, parse, then move to final location
        from backend.models.job import JobData
        structured_llm = gemini_parser.llm.with_structured_output(
            schema=JobData, method="json_mode"
        )
        prompt = gemini_parser._build_job_parsing_prompt(job_request.raw_text, job_request.url)
        job_data: JobData = structured_llm.invoke(prompt)

        # Ensure raw_text and url are set
        job_data.raw_text = job_request.raw_text
        job_data.url = job_request.url

        # Create job folder using extracted job_title and company
        logger.info(f"Creating job folder for: {job_data.job_title} at {job_data.company}")
        job_folder, job_slug = create_job_folder(job_data.job_title, job_data.company)

        # Save job.json to the created folder
        job_json_path = job_folder / "job.json"
        gemini_parser._save_job_json(job_data, job_json_path)

        logger.info(f"Job posting captured successfully: {job_slug}")

        return JobCaptureResponse(
            success=True,
            job_slug=job_slug
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return JobCaptureResponse(
            success=False,
            error=str(e)
        )


@router.post("/generate", response_model=GenerateResponse)
async def generate_documents(request: GenerateRequest):
    """
    Generate tailored resume and cover letter for a specific job.

    Steps:
    1. Load resume.json and job.json
    2. Generate cover letter LaTeX using Gemini
    3. Generate tailored resume LaTeX using Gemini
    4. Compile both to PDFs using pdflatex
    5. Return paths to generated PDFs

    Args:
        request: GenerateRequest containing job_slug

    Returns:
        GenerateResponse with paths to generated PDFs

    Raises:
        HTTPException: If generation or compilation fails
    """
    try:
        logger.info(f"Starting document generation for job: {request.job_slug}")

        # Validate job folder exists
        job_folder = get_jobs_dir() / request.job_slug
        if not job_folder.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Job folder not found: {request.job_slug}"
            )

        # Load resume.json
        resume_path = get_resume_path()
        if not resume_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Resume not found. Please upload your resume first."
            )

        with open(resume_path, "r", encoding="utf-8") as f:
            resume_data = json.load(f)

        # Load job.json
        job_json_path = job_folder / "job.json"
        if not job_json_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Job data not found for: {request.job_slug}"
            )

        with open(job_json_path, "r", encoding="utf-8") as f:
            job_data = json.load(f)

        # Initialize services
        latex_generator = LaTeXGeneratorService()

        # Generate cover letter LaTeX
        logger.info("Generating cover letter...")
        cover_letter_tex_path = job_folder / "cover_letter.tex"
        latex_generator.generate_cover_letter(
            resume_data, job_data, cover_letter_tex_path
        )

        # Generate resume LaTeX
        logger.info("Generating tailored resume...")
        resume_tex_path = job_folder / "resume.tex"
        latex_generator.generate_resume(
            resume_data, job_data, resume_tex_path
        )

        # Check if pdflatex is installed
        if not PDFCompilerService.check_latex_installed():
            logger.warning("pdflatex not installed - returning LaTeX files only")
            return GenerateResponse(
                success=True,
                status="latex_only",
                cover_letter_pdf=None,
                resume_pdf=None,
                error="pdflatex not installed. LaTeX files generated but PDFs could not be compiled."
            )

        # Compile cover letter to PDF
        logger.info("Compiling cover letter to PDF...")
        cover_letter_pdf_path = PDFCompilerService.compile_latex_to_pdf(
            cover_letter_tex_path
        )

        # Compile resume to PDF
        logger.info("Compiling resume to PDF...")
        resume_pdf_path = PDFCompilerService.compile_latex_to_pdf(
            resume_tex_path
        )

        # Build relative paths for response
        cover_letter_pdf_rel = f"jobs/{request.job_slug}/cover_letter.pdf"
        resume_pdf_rel = f"jobs/{request.job_slug}/resume.pdf"

        logger.info("Document generation completed successfully")

        return GenerateResponse(
            success=True,
            status="success",
            cover_letter_pdf=cover_letter_pdf_rel,
            resume_pdf=resume_pdf_rel
        )

    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise

    except ValueError as e:
        logger.error(f"Generation error: {str(e)}")
        return GenerateResponse(
            success=False,
            status="error",
            error=str(e)
        )

    except Exception as e:
        logger.error(f"Unexpected error during generation: {str(e)}", exc_info=True)
        return GenerateResponse(
            success=False,
            status="error",
            error=f"Document generation failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Service status information
    """
    return {"status": "healthy", "service": "resume-parser"}
