"""
Template Manager Service

Manages LaTeX template discovery, loading, and selection for resume generation.
Provides centralized access to template files and their associated document classes.
"""

import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TemplateInfo(BaseModel):
    """Information about a LaTeX template."""
    name: str  # Template name (e.g., "resume_coding_bootcamp")
    path: Path  # Absolute path to .tex template file
    cls_files: list[Path]  # List of .cls files required by this template
    document_class: str  # Document class used (e.g., "resume")


class TemplateManager:
    """
    Manages LaTeX templates for document generation.

    Discovers available templates in backend/template/ directory,
    provides template selection logic, and handles template file loading.
    """

    def __init__(self):
        """Initialize the template manager."""
        self.template_dir = self.get_template_dir()
        self.templates = self.discover_templates()
        logger.info(f"Initialized TemplateManager with {len(self.templates)} template(s)")

    @staticmethod
    def get_template_dir() -> Path:
        """
        Get the absolute path to the template directory.

        Returns:
            Path: Absolute path to backend/template/
        """
        # Navigate from this file to backend/template/
        current_file = Path(__file__).resolve()
        backend_dir = current_file.parent.parent  # backend/services -> backend
        template_dir = backend_dir / "template"

        if not template_dir.exists():
            logger.warning(f"Template directory not found: {template_dir}")
            template_dir.mkdir(parents=True, exist_ok=True)

        return template_dir

    def discover_templates(self) -> dict[str, TemplateInfo]:
        """
        Discover all .tex template files in the template directory.

        Returns:
            dict[str, TemplateInfo]: Mapping of template names to TemplateInfo objects
        """
        templates = {}

        # Find all .tex files in template directory
        tex_files = list(self.template_dir.glob("*.tex"))

        for tex_file in tex_files:
            template_name = tex_file.stem  # Filename without extension

            # Read template to determine document class
            try:
                with open(tex_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract document class from \documentclass{...}
                doc_class = self._extract_document_class(content)

                # Find associated .cls files
                cls_files = self.get_template_cls_files(doc_class)

                template_info = TemplateInfo(
                    name=template_name,
                    path=tex_file,
                    cls_files=cls_files,
                    document_class=doc_class
                )

                templates[template_name] = template_info
                logger.info(f"Discovered template: {template_name} (class: {doc_class})")

            except Exception as e:
                logger.error(f"Error processing template {tex_file}: {e}")
                continue

        return templates

    def _extract_document_class(self, content: str) -> str:
        """
        Extract document class from LaTeX content.

        Args:
            content: LaTeX file content

        Returns:
            str: Document class name (e.g., "resume", "article")
        """
        import re

        # Match \documentclass{classname} or \documentclass[options]{classname}
        match = re.search(r'\\documentclass(?:\[.*?\])?\{([^}]+)\}', content)

        if match:
            return match.group(1)

        logger.warning("No document class found in template, defaulting to 'article'")
        return "article"

    def get_template_cls_files(self, document_class: str) -> list[Path]:
        """
        Get list of .cls files needed for a document class.

        Args:
            document_class: Name of the document class (e.g., "resume")

        Returns:
            list[Path]: List of absolute paths to .cls files
        """
        cls_files = []

        # Standard LaTeX classes don't need .cls files
        standard_classes = ["article", "report", "book", "letter", "beamer", "memoir"]

        if document_class in standard_classes:
            return cls_files

        # Look for custom .cls file in template directory
        cls_file = self.template_dir / f"{document_class}.cls"

        if cls_file.exists():
            cls_files.append(cls_file)
            logger.debug(f"Found .cls file: {cls_file}")
        else:
            logger.warning(f"Custom document class '{document_class}' requires {document_class}.cls, but file not found")

        return cls_files

    def load_template(self, template_name: str) -> str:
        """
        Load template file content.

        Args:
            template_name: Name of the template to load

        Returns:
            str: Template file content

        Raises:
            ValueError: If template not found
        """
        if template_name not in self.templates:
            raise ValueError(
                f"Template '{template_name}' not found. "
                f"Available templates: {list(self.templates.keys())}"
            )

        template_info = self.templates[template_name]

        with open(template_info.path, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.debug(f"Loaded template: {template_name} ({len(content)} characters)")

        return content

    def select_resume_template(
        self,
        resume_data: dict,
        job_data: dict
    ) -> Optional[str]:
        """
        Select appropriate resume template based on resume and job data.

        Args:
            resume_data: Parsed resume data
            job_data: Parsed job posting data

        Returns:
            Optional[str]: Template name, or None if no suitable template found
        """
        # Phase 1: Simple selection - use resume_coding_bootcamp if available
        # Future: Add logic to select based on job type, industry, experience level

        if "resume_coding_bootcamp" in self.templates:
            logger.info("Selected template: resume_coding_bootcamp")
            return "resume_coding_bootcamp"

        # Fallback: Return first available template
        if self.templates:
            template_name = next(iter(self.templates.keys()))
            logger.info(f"Selected fallback template: {template_name}")
            return template_name

        logger.warning("No templates available")
        return None

    def get_template_info(self, template_name: str) -> Optional[TemplateInfo]:
        """
        Get TemplateInfo for a specific template.

        Args:
            template_name: Name of the template

        Returns:
            Optional[TemplateInfo]: Template information, or None if not found
        """
        return self.templates.get(template_name)
