"""
Pydantic models for Jinja2 template data.

These models define the structured JSON data that AI generates to populate
Jinja2 LaTeX templates. Using Pydantic ensures type safety and enables
LangChain's with_structured_output() for guaranteed schema compliance.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class ContactData(BaseModel):
    """Contact information for resume template."""
    name: str = Field(description="Full name of the candidate")
    phone: Optional[str] = Field(default=None, description="Phone number in format +1(XXX) XXX-XXXX")
    location: Optional[str] = Field(default=None, description="City, State")
    email: str = Field(description="Email address")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn URL (just linkedin.com/in/username part)")
    github: Optional[str] = Field(default=None, description="GitHub URL (just github.com/username part)")
    website: Optional[str] = Field(default=None, description="Personal website URL")


class ProjectData(BaseModel):
    """Project information for resume template."""
    name: str = Field(description="Project name")
    technologies: str = Field(
        description="Comma-separated list of technologies used (e.g., 'Python, React, PostgreSQL')"
    )
    bullets: List[str] = Field(
        min_length=2,
        max_length=6,
        description="List of 2-6 achievement bullet points with action verbs and metrics"
    )


class SkillsData(BaseModel):
    """Skills information for resume template."""
    languages: Optional[str] = Field(
        default=None,
        description="Comma-separated programming languages (e.g., 'JavaScript, Python, SQL')"
    )
    frameworks: Optional[str] = Field(
        default=None,
        description="Comma-separated frameworks and libraries (e.g., 'React, Django, Express')"
    )
    tools: Optional[str] = Field(
        default=None,
        description="Comma-separated tools and technologies (e.g., 'Git, Docker, AWS')"
    )
    soft_skills: Optional[str] = Field(
        default=None,
        description="Comma-separated soft skills (e.g., 'Leadership, Communication, Teamwork')"
    )


class EducationData(BaseModel):
    """Education entry for resume template."""
    degree: str = Field(description="Degree name (e.g., 'BS in Computer Science', 'Software Development Certificate')")
    institution: str = Field(description="Name of educational institution")
    field: Optional[str] = Field(
        default=None,
        description="Field of study if different from degree (can be null for certificates)"
    )
    date: str = Field(description="Graduation date in format 'Month Year' (e.g., 'May 2020', 'Jan 2023')")


class WorkExperienceData(BaseModel):
    """Work experience entry for resume template."""
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    date_range: str = Field(
        description="Date range in format 'Month Year - Month Year' or 'Month Year - Present'"
    )


class ResumeTemplateData(BaseModel):
    """
    Complete data structure for populating Jinja2 resume templates.

    This is the root model that AI generates when using with_structured_output().
    All resume content is structured in a way that can be directly passed to
    Jinja2 templates for rendering.
    """
    contact: ContactData = Field(description="Contact information")
    projects: List[ProjectData] = Field(
        min_length=1,
        max_length=5,
        description="List of 1-5 most relevant projects for the job"
    )
    skills: SkillsData = Field(description="Categorized skills")
    education: List[EducationData] = Field(
        min_length=1,
        description="List of education entries (at least one required)"
    )
    work_experience: List[WorkExperienceData] = Field(
        default_factory=list,
        description="List of work experience entries (can be empty)"
    )


class CoverLetterTemplateData(BaseModel):
    """
    Data structure for populating Jinja2 cover letter templates.

    Future enhancement for cover letter generation with Jinja2.
    """
    contact: ContactData = Field(description="Contact information")
    company: str = Field(description="Target company name")
    position: str = Field(description="Target position/job title")
    hiring_manager: Optional[str] = Field(
        default=None,
        description="Hiring manager name if known"
    )
    opening_paragraph: str = Field(
        description="Opening paragraph introducing candidate and expressing interest"
    )
    body_paragraphs: List[str] = Field(
        min_length=1,
        max_length=3,
        description="1-3 body paragraphs highlighting relevant experience"
    )
    closing_paragraph: str = Field(
        description="Closing paragraph with call to action"
    )
