from pydantic import BaseModel, Field
from typing import Optional


class JobPostingRequest(BaseModel):
    """Request model for job posting submission."""
    raw_text: str = Field(..., description="Full text content of the job posting")
    url: str = Field(..., description="URL of the job posting page")


class JobData(BaseModel):
    """Structured job data extracted from job posting."""
    job_title: str = Field(..., description="Title of the job position")
    company: str = Field(..., description="Company name")
    application_id: Optional[str] = Field(None, description="Application/requisition ID if available")
    job_description: str = Field(..., description="Full job description text")
    location: Optional[str] = Field(None, description="Job location")
    url: str = Field(..., description="URL of the job posting")
    raw_text: str = Field(..., description="Original raw text from the job posting")


class JobCaptureResponse(BaseModel):
    """Response model for job capture endpoint."""
    success: bool
    job_slug: Optional[str] = None
    error: Optional[str] = None
