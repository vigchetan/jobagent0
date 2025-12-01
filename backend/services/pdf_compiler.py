"""Service for compiling LaTeX documents to PDF"""
import subprocess
from pathlib import Path
import logging
import shutil

logger = logging.getLogger(__name__)


class PDFCompilerService:
    """Service for compiling LaTeX files to PDF using pdflatex"""

    @staticmethod
    def check_latex_installed() -> bool:
        """
        Check if pdflatex is installed on the system.

        Returns:
            bool: True if pdflatex is available, False otherwise
        """
        return shutil.which("pdflatex") is not None

    @staticmethod
    def compile_latex_to_pdf(tex_file_path: Path) -> Path:
        """
        Compile a LaTeX file to PDF using pdflatex.

        Args:
            tex_file_path: Path to the .tex file

        Returns:
            Path: Path to the generated PDF file

        Raises:
            ValueError: If compilation fails or pdflatex is not installed
        """
        if not PDFCompilerService.check_latex_installed():
            raise ValueError(
                "pdflatex is not installed. Please install TeX Live or MiKTeX to compile LaTeX documents."
            )

        if not tex_file_path.exists():
            raise ValueError(f"LaTeX file not found: {tex_file_path}")

        try:
            logger.info(f"Compiling LaTeX file: {tex_file_path}")

            # Get the directory containing the .tex file
            work_dir = tex_file_path.parent

            # Run pdflatex twice to resolve references
            # First pass
            result = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",  # Don't stop on errors
                    "-output-directory", str(work_dir),
                    str(tex_file_path.name)
                ],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )

            if result.returncode != 0:
                logger.error(f"pdflatex first pass failed: {result.stderr}")
                # Don't raise immediately, as pdflatex might still produce a PDF

            # Second pass to resolve references
            result = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-output-directory", str(work_dir),
                    str(tex_file_path.name)
                ],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Check if PDF was generated
            pdf_path = tex_file_path.with_suffix(".pdf")
            if not pdf_path.exists():
                logger.error(f"PDF generation failed. pdflatex output: {result.stderr}")
                raise ValueError(
                    f"PDF compilation failed. pdflatex did not produce a PDF file. "
                    f"This might be due to LaTeX syntax errors in the generated document."
                )

            # Clean up auxiliary files
            PDFCompilerService._cleanup_aux_files(tex_file_path)

            logger.info(f"Successfully compiled PDF: {pdf_path}")
            return pdf_path

        except subprocess.TimeoutExpired:
            logger.error("pdflatex compilation timed out")
            raise ValueError("PDF compilation timed out after 60 seconds")

        except Exception as e:
            logger.error(f"Error compiling LaTeX to PDF: {str(e)}")
            raise ValueError(f"Failed to compile PDF: {str(e)}")

    @staticmethod
    def _cleanup_aux_files(tex_file_path: Path) -> None:
        """
        Clean up auxiliary files created by pdflatex.

        Args:
            tex_file_path: Path to the .tex file
        """
        # List of extensions to remove
        aux_extensions = [".aux", ".log", ".out", ".toc", ".lof", ".lot"]

        base_path = tex_file_path.with_suffix("")
        for ext in aux_extensions:
            aux_file = base_path.with_suffix(ext)
            if aux_file.exists():
                try:
                    aux_file.unlink()
                    logger.debug(f"Removed auxiliary file: {aux_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove auxiliary file {aux_file}: {e}")
