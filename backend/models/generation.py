"""Models for document generation requests and responses"""
from pydantic import BaseModel, Field
from typing import Optional


class GenerateRequest(BaseModel):
    """Request model for document generation."""
    job_slug: str = Field(..., description="The job slug identifier")


class GenerateResponse(BaseModel):
    """Response model for document generation."""
    success: bool
    status: str = "success"
    cover_letter_pdf: Optional[str] = None
    resume_pdf: Optional[str] = None
    error: Optional[str] = None
