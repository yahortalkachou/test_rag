"""
Data models for CV parsing system.
Defines the structure of parsed CV data.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Project:
    """Project model extracted from CV."""
    
    name: str
    description: str
    roles: list[str]
    cv_id: str
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Project':
        """Creates Project instance from dictionary."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            roles=data.get("roles", []),
            cv_id=data.get("cv_id", "")
        )


@dataclass
class PersonalInfo:
    """Personal information extracted from CV."""
    
    name: str
    level: str | None = None
    roles: list[str] = field(default_factory=list)
    education: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    description: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        """Converts PersonalInfo to dictionary."""
        return {
            "name": self.name,
            "level": self.level,
            "roles": self.roles,
            "education": self.education,
            "languages": self.languages,
            "domains": self.domains,
            "description": self.description
        }


@dataclass
class CV:
    """Complete CV with personal information and projects."""
    
    personal_info: PersonalInfo
    projects: list[Project]
    cv_id: str
    
    @property
    def metadata(self) -> dict[str, Any]:
        """Metadata for vector database."""
        return {
            "CV_id": self.cv_id,
            **self.personal_info.to_dict()
        }
    
    @property
    def text(self) -> str:
        """Text content for vector database."""
        return self.personal_info.description