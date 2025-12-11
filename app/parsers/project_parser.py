"""
Parser for extracting project information from CV tables.
"""

from typing import List
from app.parsers.text_normalizer import TextNormalizer
from app.parsers.models import Project


class InnoProjectParser:
    """Parser for project information from CV tables."""
    
    @staticmethod
    def parse_project_row(cells: List, cv_id: str = "", candidate_name: str = "") -> Project:
        """
        Parses a table row containing project information.
        Expected cv_id from personal data parsed before.
        
        Args:
            cells: List of table cells from a DOCX table row
            
        Returns:
            Project object with extracted information
            
        Raises:
            ValueError: If row doesn't have enough cells
        """
        if len(cells) < 2:
            raise ValueError(f"Project row must have at least 2 cells, got {len(cells)}")
        
        description = cells[1].text
        project_name_parts = cells[0].text.split('\n')
        
        if len(project_name_parts) < 2:
            project_name = project_name_parts[0]
            summary = ""
        else:
            project_name = project_name_parts[0]
            summary = project_name_parts[1]
        
        # Extract roles from description
        description_lines = description.split('\n')
        roles_line = TextNormalizer.extract_between_markers(
            description_lines, "Project roles", "Period"
        )
        
        roles = roles_line[0].split('/') if roles_line else []
        description = f"{summary} {description}" if summary else description
        
        return Project(
            project_name=TextNormalizer.normalize(project_name),
            candidate_name=candidate_name,
            description=TextNormalizer.normalize(description),
            roles=[TextNormalizer.normalize(role) for role in roles],
            cv_id=cv_id  
        )