"""PDF parsing service using PyMuPDF4LLMLoader"""
from langchain_pymupdf4llm import PyMuPDF4LLMLoader, PyMuPDF4LLMParser
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PDFParserService:
    """Service for parsing PDF resumes using PyMuPDF4LLMLoader"""

    @staticmethod
    def load_pdf(pdf_path: Path) -> str:
        """
        Loads PDF using PyMuPDF4LLMLoader which preserves document layout
        and context for LLM processing.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text with preserved layout/context

        Raises:
            ValueError: If PDF cannot be parsed
        """
        try:
            logger.info(f"Loading PDF from: {pdf_path}")

            # PyMuPDF4LLMLoader preserves layout, images context
            loader = PyMuPDF4LLMLoader(str(pdf_path))
            documents = loader.load()

            # Combine all pages
            full_text = "\n\n".join([doc.page_content for doc in documents])

            logger.info(f"Successfully loaded PDF with {len(documents)} pages")
            logger.debug(f"Extracted text length: {len(full_text)} characters")

            return full_text

        except Exception as e:
            logger.error(f"Error loading PDF: {str(e)}")
            raise ValueError(f"Failed to parse PDF: {str(e)}")
