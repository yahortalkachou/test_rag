"""
Data models for CV parsing system.
Defines the structure of parsed CV data.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class Project:
    """Project model extracted from CV."""
    
    name: str
    description: str
    roles: List[str]
    cv_id: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
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
    level: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    education: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
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
    projects: List[Project]
    cv_id: str
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Metadata for vector database."""
        return {
            "CV_id": self.cv_id,
            **self.personal_info.to_dict()
        }
    
    @property
    def text(self) -> str:
        """Text content for vector database."""
        return self.personal_info.description