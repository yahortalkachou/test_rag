"""
Manager for collections of parsed CVs.
"""

from typing import List, Dict, Optional, Any
from .models import CV
from .inno_parser import InnoStandardParser


class CVCollection:
    """Manager for collections of parsed CVs."""
    
    def __init__(self):
        self.cvs: List[CV] = []
        self.parser = InnoStandardParser()
    
    def add_cv_from_file(self, file_path: str) -> str:
        """
        Adds a CV from file to the collection.
        
        Args:
            file_path: Path to CV file
            
        Returns:
            ID of the added CV
        """
        cv = self.parser.parse(file_path)
        self.cvs.append(cv)
        return cv.cv_id
    
    def get_cv(self, cv_id: str) -> Optional[CV]:
        """Retrieves a CV by its ID."""
        for cv in self.cvs:
            if cv.cv_id == cv_id:
                return cv
        return None
    
    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """Returns all metadata for vector database."""
        return [cv.metadata for cv in self.cvs]
    
    def get_all_texts(self) -> List[str]:
        """Returns all text content for vector database."""
        return [cv.text for cv in self.cvs]
    
    def get_personal_data(self, cv_id: str) -> Optional[Dict[str, Any]]:
        """Returns personal data for a specific CV."""
        cv = self.get_cv(cv_id)
        if cv:
            return {
                'metadata': cv.personal_info.to_dict(),
                'text': cv.text
            }
        return None
    
    def clear(self):
        """Clears the collection."""
        self.cvs.clear()