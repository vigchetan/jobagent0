"""Pydantic models for resume data structure"""
from pydantic import BaseModel, Field
from typing import List, Optional


class ContactInfo(BaseModel):
    """Contact information from resume"""

    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    other_links: List[str] = Field(default_factory=list)


class Education(BaseModel):
    """Education entry"""

    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None  # Flexible string format
    end_date: Optional[str] = None
    gpa: Optional[str] = None
    honors: List[str] = Field(default_factory=list)
    relevant_coursework: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class Experience(BaseModel):
    """Work experience entry"""

    company: str
    position: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    current: bool = False
    responsibilities: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class Project(BaseModel):
    """Project entry"""

    name: str
    description: str
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    link: Optional[str] = None


class Certification(BaseModel):
    """Certification entry"""

    name: str
    issuer: str
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


class Skill(BaseModel):
    """Skill category"""

    category: str  # e.g., "Programming Languages", "Frameworks", "Tools"
    items: List[str]


class Publication(BaseModel):
    """Publication/Research entry"""

    title: str
    authors: List[str] = Field(default_factory=list)
    venue: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None


class Award(BaseModel):
    """Award/Achievement entry"""

    title: str
    issuer: str
    date: Optional[str] = None
    description: Optional[str] = None


class Language(BaseModel):
    """Language proficiency"""

    language: str
    proficiency: str  # e.g., "Native", "Fluent", "Professional"


class ResumeData(BaseModel):
    """Complete resume data structure"""

    contact_info: ContactInfo
    summary: Optional[str] = None
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    publications: List[Publication] = Field(default_factory=list)
    awards: List[Award] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    volunteer_experience: List[Experience] = Field(default_factory=list)
    additional_sections: dict = Field(
        default_factory=dict
    )  # For any other sections
    raw_text: str = ""  # Preserve original text for reference


class ResumeUploadResponse(BaseModel):
    """API response for resume upload"""

    success: bool
    message: str
    resume_path: Optional[str] = None
    error: Optional[str] = None
