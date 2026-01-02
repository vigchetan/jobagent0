"""Service for generating LaTeX documents using Gemini"""
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config import settings
from backend.config.prompts import (
    COVER_LETTER_SYSTEM_PROMPT,
    RESUME_SYSTEM_PROMPT,
    build_cover_letter_prompt,
    build_resume_prompt,
    build_template_resume_prompt,
    JINJA2_TEMPLATE_RESUME_SYSTEM_PROMPT,
    build_jinja2_resume_prompt
)
from backend.services.template_manager import TemplateManager
from backend.models.template_data import ResumeTemplateData
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)


class LaTeXGeneratorService:
    """Service for generating LaTeX documents (cover letters and resumes) using Gemini"""

    def __init__(self):
        """Initialize Gemini model for LaTeX generation and template manager"""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=settings.google_api_key,
            temperature=0.7,  # Slightly higher temperature for creative writing
        )
        self.template_manager = TemplateManager()
        self._cls_files = None  # Store cls files for compilation

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

        Priority order:
        1. Try Jinja2 template (.j2.tex) → JSON generation + template rendering
        2. Fallback to regular template (.tex) → AI-generated full LaTeX
        3. Fallback to scratch generation → No template

        Args:
            resume_data: The parsed resume data as dictionary
            job_data: The job posting data as dictionary
            output_path: Path where resume.tex should be saved

        Returns:
            str: The generated LaTeX code

        Raises:
            ValueError: If all generation methods fail
        """
        # Select template
        template_name = self.template_manager.select_resume_template(
            resume_data, job_data
        )

        if not template_name:
            logger.info("No templates available, generating from scratch...")
            return self._generate_resume_from_scratch(
                resume_data, job_data, output_path
            )

        # Check if Jinja2 template exists (highest priority)
        jinja2_path = self.template_manager.template_dir / f"{template_name}.j2.tex"

        if jinja2_path.exists():
            try:
                logger.info("Attempting Jinja2 template-based generation...")
                latex_code = self._generate_resume_with_jinja2_template(
                    resume_data, job_data, output_path, template_name
                )
                logger.info("✅ Jinja2 template generation successful")
                return latex_code

            except Exception as e:
                logger.warning(
                    f"Jinja2 generation failed: {e}. "
                    "Falling back to regular template generation."
                )
                # Reset cls_files since Jinja2 generation failed
                self._cls_files = None

        # Try regular template generation
        try:
            logger.info("Attempting regular template-based generation...")
            latex_code = self._generate_resume_with_template(
                resume_data, job_data, output_path
            )
            logger.info("Template-based generation successful")
            return latex_code

        except Exception as e:
            logger.warning(
                f"Template-based generation failed: {e}. "
                "Falling back to scratch generation."
            )
            # Reset cls_files since template generation failed
            self._cls_files = None

            # Final fallback to scratch generation
            logger.info("Falling back to scratch generation...")
            return self._generate_resume_from_scratch(
                resume_data, job_data, output_path
            )

    def _generate_resume_with_template(
        self,
        resume_data: dict,
        job_data: dict,
        output_path: Path
    ) -> str:
        """
        Generate resume using template-based approach.

        Args:
            resume_data: The parsed resume data as dictionary
            job_data: The job posting data as dictionary
            output_path: Path where resume.tex should be saved

        Returns:
            str: The generated LaTeX code

        Raises:
            ValueError: If template generation fails
        """
        # Select appropriate template
        template_name = self.template_manager.select_resume_template(
            resume_data, job_data
        )

        if not template_name:
            raise ValueError("No suitable template found")

        # Load template
        template_content = self.template_manager.load_template(template_name)
        template_info = self.template_manager.get_template_info(template_name)

        # Store cls_files for later use by PDF compiler
        self._cls_files = template_info.cls_files
        logger.info(f"Using template: {template_name} with {len(self._cls_files)} .cls file(s)")

        # Build prompt for AI to generate content following template structure
        user_prompt = build_template_resume_prompt(
            resume_data, job_data, template_content
        )

        # Create messages
        from backend.config.prompts import TEMPLATE_RESUME_SYSTEM_PROMPT
        messages = [
            {"role": "system", "content": TEMPLATE_RESUME_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        # Call Gemini
        logger.info("Calling Gemini API for template-based resume generation...")
        response = self.llm.invoke(messages)

        # Extract LaTeX code
        latex_code = self._extract_latex_code(response.content)

        # Save to file
        self._save_latex_file(latex_code, output_path)

        logger.info(f"Template-based resume LaTeX saved to: {output_path}")
        return latex_code

    def _generate_resume_from_scratch(
        self,
        resume_data: dict,
        job_data: dict,
        output_path: Path
    ) -> str:
        """
        Generate resume from scratch (original method).

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
            logger.info("Generating tailored resume from scratch with Gemini...")

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

    def _generate_resume_with_jinja2_template(
        self,
        resume_data: dict,
        job_data: dict,
        output_path: Path,
        template_name: str
    ) -> str:
        """
        Generate resume using Jinja2 template with structured JSON data.

        This method uses AI to generate structured JSON data (not full LaTeX),
        then renders a Jinja2 template with that data for guaranteed consistency.

        Args:
            resume_data: The parsed resume data as dictionary
            job_data: The job posting data as dictionary
            output_path: Path where resume.tex should be saved
            template_name: Name of the template (without .j2.tex extension)

        Returns:
            str: The generated LaTeX code

        Raises:
            ValueError: If generation or rendering fails
        """
        try:
            # Check if Jinja2 template exists
            template_file = f"{template_name}.j2.tex"
            template_path = self.template_manager.template_dir / template_file

            if not template_path.exists():
                raise ValueError(f"Jinja2 template not found: {template_file}")

            logger.info(f"Using Jinja2 template: {template_file}")

            # Build prompt for AI to generate JSON data
            user_prompt = build_jinja2_resume_prompt(
                resume_data, job_data, template_name
            )

            # Create messages
            messages = [
                {"role": "system", "content": JINJA2_TEMPLATE_RESUME_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]

            # Use structured output for guaranteed JSON schema compliance
            logger.info("Calling Gemini API for structured JSON generation...")
            structured_llm = self.llm.with_structured_output(
                schema=ResumeTemplateData,
                method="json_mode"
            )

            # Generate structured data
            template_data: ResumeTemplateData = structured_llm.invoke(messages)

            logger.info("Successfully generated structured JSON data")
            logger.debug(f"Generated data: {template_data.model_dump_json(indent=2)}")

            # Configure Jinja2 environment for LaTeX
            jinja_env = Environment(
                loader=FileSystemLoader(self.template_manager.template_dir),
                autoescape=False,  # Don't escape LaTeX commands
                block_start_string='{%',
                block_end_string='%}',
                variable_start_string='{{',
                variable_end_string='}}',
                comment_start_string='{#',
                comment_end_string='#}',
                trim_blocks=True,  # Remove first newline after block
                lstrip_blocks=True  # Strip leading whitespace before blocks
            )

            # Load and render template
            template = jinja_env.get_template(template_file)
            latex_code = template.render(**template_data.model_dump())

            logger.info("Successfully rendered Jinja2 template")

            # Store cls_files for PDF compilation
            template_info = self.template_manager.get_template_info(template_name)
            if template_info:
                self._cls_files = template_info.cls_files
                logger.info(f"Stored {len(self._cls_files)} .cls file(s) for compilation")

            # Save to file
            self._save_latex_file(latex_code, output_path)

            logger.info(f"Jinja2-based resume LaTeX saved to: {output_path}")
            return latex_code

        except Exception as e:
            logger.error(f"Error generating resume with Jinja2: {str(e)}")
            raise ValueError(f"Failed to generate Jinja2 resume: {str(e)}")

    def _extract_json_from_response(self, response_content: str) -> dict:
        """
        Extract and parse JSON from LLM response.

        Handles markdown code blocks and validates JSON structure.
        Used as fallback when structured output is not available.

        Args:
            response_content: The raw response from the LLM

        Returns:
            dict: Parsed JSON data

        Raises:
            ValueError: If JSON parsing fails or required keys are missing
        """
        content = response_content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[len("```json"):].strip()
        elif content.startswith("```"):
            content = content[len("```"):].strip()

        if content.endswith("```"):
            content = content[:-len("```")].strip()

        try:
            data = json.loads(content)

            # Validate required keys
            required_keys = ["contact", "projects", "skills", "education"]
            missing_keys = [k for k in required_keys if k not in data]

            if missing_keys:
                raise ValueError(f"Missing required keys in JSON: {missing_keys}")

            logger.info("Successfully parsed and validated JSON response")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response content (first 500 chars): {content[:500]}...")
            raise ValueError(f"Invalid JSON response from LLM: {e}")

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
        # Check for \input{} or \include{} commands (security)
        if "\\input{" in latex_code or "\\include{" in latex_code:
            logger.warning(
                "Generated LaTeX contains \\input{} or \\include{} commands. "
                "This may cause compilation failures if referenced files don't exist."
            )
            raise ValueError(
                "Generated LaTeX uses external file references (\\input or \\include). "
                "The document must be self-contained for successful compilation."
            )

        # Note: Custom document class restriction removed.
        # The template system provides vetted custom classes with .cls files.
        # PDFCompilerService will copy necessary .cls files to the work directory.

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
