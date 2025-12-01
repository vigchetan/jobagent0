"""Workspace directory management utilities"""
from pathlib import Path
from backend.config import settings
import logging
import re

logger = logging.getLogger(__name__)


def ensure_workspace_exists() -> Path:
    """
    Ensures workspace directory exists and returns its path.
    Creates directory if it doesn't exist.

    Returns:
        Path: The workspace directory path

    Raises:
        OSError: If directory cannot be created
    """
    workspace = settings.workspace_path
    try:
        workspace.mkdir(parents=True, exist_ok=True)
        logger.info(f"Workspace directory: {workspace}")
        return workspace
    except OSError as e:
        logger.error(f"Failed to create workspace directory: {e}")
        raise


def get_resume_path() -> Path:
    """
    Returns path to resume.json file.

    Returns:
        Path: Path to resume.json in workspace directory
    """
    return ensure_workspace_exists() / "resume.json"


def get_jobs_dir() -> Path:
    """
    Returns path to jobs directory.
    Creates it if it doesn't exist.

    Returns:
        Path: Path to jobs directory in workspace
    """
    jobs_dir = ensure_workspace_exists() / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    return jobs_dir


def sanitize_slug(text: str) -> str:
    """
    Sanitizes text into a filesystem-safe slug.

    Args:
        text: Text to sanitize

    Returns:
        str: Sanitized slug suitable for directory names
    """
    # Remove or replace special characters
    slug = re.sub(r'[^\w\s-]', '', text)
    # Replace whitespace with hyphens
    slug = re.sub(r'[-\s]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Limit length to prevent filesystem issues
    return slug[:100]


def create_job_folder(job_title: str, company: str) -> tuple[Path, str]:
    """
    Creates a job-specific folder in the workspace.

    Args:
        job_title: Title of the job position
        company: Company name

    Returns:
        tuple[Path, str]: (Path to created job folder, job_slug)

    Raises:
        OSError: If directory cannot be created
    """
    # Create slug from job_title and company
    job_slug = f"{sanitize_slug(job_title)}-{sanitize_slug(company)}"

    # Handle potential duplicate slugs by appending counter
    jobs_dir = get_jobs_dir()
    job_folder = jobs_dir / job_slug

    counter = 1
    original_slug = job_slug
    while job_folder.exists():
        job_slug = f"{original_slug}-{counter}"
        job_folder = jobs_dir / job_slug
        counter += 1

    try:
        job_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created job folder: {job_folder}")
        return job_folder, job_slug
    except OSError as e:
        logger.error(f"Failed to create job folder: {e}")
        raise


def get_job_json_path(job_slug: str) -> Path:
    """
    Returns path to job.json file for a specific job.

    Args:
        job_slug: The job slug identifier

    Returns:
        Path: Path to job.json file
    """
    return get_jobs_dir() / job_slug / "job.json"
