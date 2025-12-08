"""
CV Parsers package.
"""

from app.parsers.models import Project, PersonalInfo, CV
from app.parsers.text_normalizer import TextNormalizer
from app.parsers.base_parser import BaseDocxParser
from app.parsers.project_parser import InnoProjectParser
from app.parsers.inno_parser import InnoStandardParser
from app.parsers.collection import CVCollection

__all__ = [
    'Project',
    'PersonalInfo', 
    'CV',
    'TextNormalizer',
    'BaseDocxParser',
    'InnoProjectParser',
    'InnoStandardParser',
    'CVCollection'
]