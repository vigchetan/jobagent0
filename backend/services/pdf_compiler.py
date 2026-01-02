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
    def compile_latex_to_pdf(tex_file_path: Path, cls_files: list[Path] = None) -> Path:
        """
        Compile a LaTeX file to PDF using pdflatex.

        Args:
            tex_file_path: Path to the .tex file
            cls_files: Optional list of .cls files to copy to work directory

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

        # Track copied .cls files for cleanup
        copied_cls_files = []

        try:
            logger.info(f"Compiling LaTeX file: {tex_file_path}")

            # Get the directory containing the .tex file
            work_dir = tex_file_path.parent

            # Copy .cls files to work directory if provided
            if cls_files:
                for cls_file in cls_files:
                    if cls_file.exists():
                        dest = work_dir / cls_file.name
                        shutil.copy(cls_file, dest)
                        copied_cls_files.append(dest)
                        logger.info(f"Copied template class file: {cls_file.name}")
                    else:
                        logger.warning(f"Class file not found: {cls_file}")

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

            # Clean up copied .cls files
            for cls_file in copied_cls_files:
                try:
                    cls_file.unlink(missing_ok=True)
                    logger.debug(f"Removed copied class file: {cls_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to remove copied class file {cls_file}: {e}")

            logger.info(f"Successfully compiled PDF: {pdf_path}")
            return pdf_path

        except subprocess.TimeoutExpired:
            # Clean up copied .cls files on error
            for cls_file in copied_cls_files:
                cls_file.unlink(missing_ok=True)
            logger.error("pdflatex compilation timed out")
            raise ValueError("PDF compilation timed out after 60 seconds")

        except Exception as e:
            # Clean up copied .cls files on error
            for cls_file in copied_cls_files:
                cls_file.unlink(missing_ok=True)
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
