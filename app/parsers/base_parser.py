"""
Base parser class for DOCX documents.
Provides common functionality for all DOCX parsers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

# Check if python-docx is available
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: python-docx not installed. DOCX support disabled.")


class BaseDocxParser(ABC):
    """Base class for all DOCX parsers."""
    
    def __init__(self):
        self._check_docx_available()
    
    @staticmethod
    def _check_docx_available():
        """Verifies python-docx is installed."""
        if not DOCX_AVAILABLE:
            raise ImportError(
                "python-docx is not installed. Install it with: pip install python-docx"
            )
    
    @staticmethod
    def _check_file_exists(file_path: str):
        """Validates that the file exists and is a DOCX file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"DOCX file not found: {file_path}")
        if path.suffix.lower() != '.docx':
            raise ValueError(f"File must be a .docx file: {file_path}")
    
    @abstractmethod
    def parse(self, file_path: str) -> Any:
        """Parses a DOCX file."""
        pass