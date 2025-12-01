"""Gemini service for parsing resume and job posting text into structured JSON"""
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.models.resume import ResumeData
from backend.models.job import JobData
from backend.config import settings
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class GeminiResumeParser:
    """Service for parsing resume text into structured JSON using Gemini"""

    def __init__(self):
        """Initialize Gemini Flash 2.0 with structured output support"""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=settings.google_api_key,
            temperature=0,  # Deterministic output for data extraction
        )

    def parse_resume(self, resume_text: str, output_path: Path) -> ResumeData:
        """
        Parse resume text into structured JSON using Gemini's structured output.

        Uses response_schema to enforce ResumeData structure.

        Args:
            resume_text: Extracted text from PDF
            output_path: Path where resume.json should be saved

        Returns:
            ResumeData object

        Raises:
            ValueError: If parsing fails
        """
        try:
            logger.info("Starting Gemini resume parsing...")

            # Create structured output LLM using response_schema
            structured_llm = self.llm.with_structured_output(
                schema=ResumeData, method="json_mode"  # Use Gemini's JSON mode
            )

            # Construct prompt that emphasizes preservation of ALL information
            prompt = self._build_parsing_prompt(resume_text)

            # Invoke Gemini with structured output
            logger.info("Calling Gemini API...")
            resume_data: ResumeData = structured_llm.invoke(prompt)

            # Add raw text to the data
            resume_data.raw_text = resume_text

            # Save to JSON file
            self._save_resume_json(resume_data, output_path)

            logger.info(f"Successfully parsed resume and saved to {output_path}")
            return resume_data

        except Exception as e:
            logger.error(f"Error parsing resume with Gemini: {str(e)}")
            raise ValueError(f"Failed to parse resume: {str(e)}")

    def _build_parsing_prompt(self, resume_text: str) -> str:
        """
        Builds comprehensive prompt for Gemini to extract ALL resume information.

        Args:
            resume_text: The text extracted from the resume PDF

        Returns:
            str: The complete prompt for Gemini
        """
        prompt = f"""You are an expert resume parser. Extract ALL information from the following resume text into a structured JSON format.

CRITICAL REQUIREMENTS:
1. Preserve ALL information - do not summarize or omit anything
2. Extract every detail including dates, locations, descriptions, bullet points
3. Capture all contact information (email, phone, LinkedIn, GitHub, websites)
4. Extract all work experiences with complete job descriptions and achievements
5. Include all education details with GPA, honors, coursework if present
6. List all skills, organized by category if possible
7. Extract all projects with their full descriptions and technologies
8. Include certifications, publications, awards, languages, volunteer work
9. Preserve any additional sections not covered by standard categories
10. Maintain chronological order for experiences and education

RESUME TEXT:
{resume_text}

Extract this resume into the structured format, ensuring NO information is lost.
"""
        return prompt

    def _save_resume_json(self, resume_data: ResumeData, output_path: Path) -> None:
        """
        Saves ResumeData to JSON file with proper formatting.

        Args:
            resume_data: The parsed resume data
            output_path: Path where JSON should be saved

        Raises:
            Exception: If file cannot be written
        """
        try:
            # Convert to dict and save with indentation
            resume_dict = resume_data.model_dump(mode="json")

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(resume_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Resume JSON saved to: {output_path}")

        except Exception as e:
            logger.error(f"Error saving resume JSON: {str(e)}")
            raise

    def parse_job_posting(self, job_text: str, url: str, output_path: Path) -> JobData:
        """
        Parse job posting text into structured JSON using Gemini's structured output.

        Args:
            job_text: Extracted text from job posting page
            url: URL of the job posting
            output_path: Path where job.json should be saved

        Returns:
            JobData object

        Raises:
            ValueError: If parsing fails
        """
        try:
            logger.info("Starting Gemini job posting parsing...")

            # Create structured output LLM using response_schema
            structured_llm = self.llm.with_structured_output(
                schema=JobData, method="json_mode"
            )

            # Construct prompt for job extraction
            prompt = self._build_job_parsing_prompt(job_text, url)

            # Invoke Gemini with structured output
            logger.info("Calling Gemini API for job extraction...")
            job_data: JobData = structured_llm.invoke(prompt)

            # Ensure raw_text and url are set
            job_data.raw_text = job_text
            job_data.url = url

            # Save to JSON file
            self._save_job_json(job_data, output_path)

            logger.info(f"Successfully parsed job posting and saved to {output_path}")
            return job_data

        except Exception as e:
            logger.error(f"Error parsing job posting with Gemini: {str(e)}")
            raise ValueError(f"Failed to parse job posting: {str(e)}")

    def _build_job_parsing_prompt(self, job_text: str, url: str) -> str:
        """
        Builds prompt for Gemini to extract structured job information.

        Args:
            job_text: The text extracted from the job posting page
            url: URL of the job posting

        Returns:
            str: The complete prompt for Gemini
        """
        prompt = f"""You are an expert job posting analyzer. Extract key information from the following job posting text into a structured JSON format.

EXTRACTION REQUIREMENTS:
1. job_title: Extract the exact job title (e.g., "Senior Backend Engineer", "Product Manager")
2. company: Extract the company name
3. application_id: Look for any requisition/application ID (e.g., "REQ-12345", "Job ID: 98765"). Set to null if not found.
4. job_description: Preserve the COMPLETE job description including all sections (responsibilities, requirements, benefits, etc.)
5. location: Extract the job location (city, state, country, or "Remote"). Set to null if not specified.

CRITICAL: For job_description, include ALL details - responsibilities, requirements, qualifications, benefits, company info, etc. Do not summarize.

JOB POSTING URL: {url}

JOB POSTING TEXT:
{job_text}

Extract this job posting into the structured format, ensuring the full job description is captured.
"""
        return prompt

    def _save_job_json(self, job_data: JobData, output_path: Path) -> None:
        """
        Saves JobData to JSON file with proper formatting.

        Args:
            job_data: The parsed job data
            output_path: Path where JSON should be saved

        Raises:
            Exception: If file cannot be written
        """
        try:
            # Convert to dict and save with indentation
            job_dict = job_data.model_dump(mode="json")

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(job_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Job JSON saved to: {output_path}")

        except Exception as e:
            logger.error(f"Error saving job JSON: {str(e)}")
            raise
