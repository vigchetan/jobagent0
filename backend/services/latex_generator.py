"""Service for generating LaTeX documents using Gemini"""
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config import settings
from backend.config.prompts import (
    COVER_LETTER_SYSTEM_PROMPT,
    RESUME_SYSTEM_PROMPT,
    build_cover_letter_prompt,
    build_resume_prompt
)
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)


class LaTeXGeneratorService:
    """Service for generating LaTeX documents (cover letters and resumes) using Gemini"""

    def __init__(self):
        """Initialize Gemini model for LaTeX generation"""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=settings.google_api_key,
            temperature=0.7,  # Slightly higher temperature for creative writing
        )

    def generate_cover_letter(
        self,
        resume_data: dict,
        job_data: dict,
        output_path: Path
    ) -> str:
        """
        Generate a cover letter in LaTeX format.

        Args:
            resume_data: The parsed resume data as dictionary
            job_data: The job posting data as dictionary
            output_path: Path where cover_letter.tex should be saved

        Returns:
            str: The generated LaTeX code

        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info("Generating cover letter with Gemini...")

            # Build the complete prompt
            user_prompt = build_cover_letter_prompt(resume_data, job_data)

            # Create messages with system prompt and user prompt
            messages = [
                {"role": "system", "content": COVER_LETTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]

            # Call Gemini
            logger.info("Calling Gemini API for cover letter generation...")
            response = self.llm.invoke(messages)

            # Extract LaTeX code from response
            latex_code = self._extract_latex_code(response.content)

            # Save to file
            self._save_latex_file(latex_code, output_path)

            logger.info(f"Cover letter LaTeX saved to: {output_path}")
            return latex_code

        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            raise ValueError(f"Failed to generate cover letter: {str(e)}")

    def generate_resume(
        self,
        resume_data: dict,
        job_data: dict,
        output_path: Path
    ) -> str:
        """
        Generate a tailored resume in LaTeX format.

        Args:
            resume_data: The parsed resume data as dictionary
            job_data: The job posting data as dictionary
            output_path: Path where resume.tex should be saved

        Returns:
            str: The generated LaTeX code

        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info("Generating tailored resume with Gemini...")

            # Build the complete prompt
            user_prompt = build_resume_prompt(resume_data, job_data)

            # Create messages with system prompt and user prompt
            messages = [
                {"role": "system", "content": RESUME_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]

            # Call Gemini
            logger.info("Calling Gemini API for resume generation...")
            response = self.llm.invoke(messages)

            # Extract LaTeX code from response
            latex_code = self._extract_latex_code(response.content)

            # Save to file
            self._save_latex_file(latex_code, output_path)

            logger.info(f"Resume LaTeX saved to: {output_path}")
            return latex_code

        except Exception as e:
            logger.error(f"Error generating resume: {str(e)}")
            raise ValueError(f"Failed to generate resume: {str(e)}")

    def _extract_latex_code(self, response_content: str) -> str:
        """
        Extracts LaTeX code from LLM response.
        Handles cases where the response might include markdown code blocks.

        Args:
            response_content: The raw response from the LLM

        Returns:
            str: The extracted LaTeX code
        """
        content = response_content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```latex"):
            content = content[len("```latex"):].strip()
        elif content.startswith("```"):
            content = content[len("```"):].strip()

        if content.endswith("```"):
            content = content[:-len("```")].strip()

        # Validate the LaTeX code
        self._validate_latex_code(content)

        return content

    def _validate_latex_code(self, latex_code: str) -> None:
        """
        Validates LaTeX code for common issues that would prevent compilation.
        Logs warnings for problematic patterns.

        Args:
            latex_code: The LaTeX code to validate

        Raises:
            ValueError: If critical issues are detected that would prevent compilation
        """
        # Check for \input{} or \include{} commands
        if "\\input{" in latex_code or "\\include{" in latex_code:
            logger.warning(
                "Generated LaTeX contains \\input{} or \\include{} commands. "
                "This may cause compilation failures if referenced files don't exist."
            )
            raise ValueError(
                "Generated LaTeX uses external file references (\\input or \\include). "
                "The document must be self-contained for successful compilation."
            )

        # Check for custom document classes (non-standard)
        import re
        doc_class_match = re.search(r'\\documentclass(?:\[.*?\])?\{([^}]+)\}', latex_code)
        if doc_class_match:
            doc_class = doc_class_match.group(1)
            standard_classes = ['article', 'report', 'book', 'letter', 'beamer', 'memoir']
            if doc_class not in standard_classes:
                logger.warning(
                    f"Generated LaTeX uses non-standard document class: {doc_class}. "
                    f"This may require external .cls files and cause compilation failures."
                )
                raise ValueError(
                    f"Generated LaTeX uses non-standard document class '{doc_class}'. "
                    f"Only standard classes ({', '.join(standard_classes)}) are allowed."
                )

    def _save_latex_file(self, latex_code: str, output_path: Path) -> None:
        """
        Saves LaTeX code to file.

        Args:
            latex_code: The LaTeX code to save
            output_path: Path where the .tex file should be saved

        Raises:
            Exception: If file cannot be written
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(latex_code)

            logger.info(f"LaTeX file saved to: {output_path}")

        except Exception as e:
            logger.error(f"Error saving LaTeX file: {str(e)}")
            raise
