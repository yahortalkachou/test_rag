"""
Text normalization utilities for CV parsing.
Handles text cleaning, language level extraction, and position level parsing.
"""

import re
from typing import List, Tuple, Optional


class TextNormalizer:
    """Utilities for text normalization and extraction."""
    
    @staticmethod
    def normalize(text: str) -> str:
        """Normalizes text to lowercase and removes extra spaces."""
        if not text:
            return ""
        return ' '.join(text.lower().split())
    
    @staticmethod
    def extract_between_markers(
        lines: List[str], 
        start_marker: str, 
        end_marker: str
    ) -> List[str]:
        """Extracts lines between start and end markers."""
        try:
            start_idx = lines.index(start_marker) + 1
        except ValueError:
            return []
        
        try:
            end_idx = lines.index(end_marker)
            items = lines[start_idx:end_idx]
        except ValueError:
            items = lines[start_idx:]
        
        return [TextNormalizer.normalize(item) for item in items]
    
    @staticmethod
    def clean_language_entry(text: str) -> Tuple[str, Optional[str]]:
        """
        Cleans language entry and extracts proficiency level.
        
        Args:
            text: Language entry string (e.g., "English (B2)", "German A1")
            
        Returns:
            Tuple of (cleaned_text, level) where level may be None
        """
        # Pattern for language levels A1-C2
        level_pattern = r'([ABCabc])[\-\s]*(\d{1,2})\b'
        match = re.search(level_pattern, text, re.IGNORECASE)
        
        if match:
            level_letter = match.group(1)
            level_digit = match.group(2)
            level_full = f"{level_letter}{level_digit}"
            
            # Text before the level
            level_start = match.start(1)
            text_before = text[:level_start].strip()
            
            # Clean non-alphanumeric characters
            text_before_cleaned = re.sub(r'[^\w\s]', ' ', text_before)
            text_before_cleaned = re.sub(r'\s+', ' ', text_before_cleaned).strip()
            
            result = f"{text_before_cleaned} {level_full}"
            return result, level_full
        
        # Fallback: look for digits only
        fallback_pattern = r'([^\d]*?)(\d{1,2})\b'
        fallback_match = re.search(fallback_pattern, text)
        
        if fallback_match:
            text_before = fallback_match.group(1).strip()
            level_digit = fallback_match.group(2)
            
            text_before = re.sub(r'[^\w\s]+$', '', text_before)
            text_before = re.sub(r'[\-\s]+$', '', text_before).strip()
            
            if text_before:
                return f"{text_before} {level_digit}", level_digit
        
        return TextNormalizer.normalize(text), None
    
    @staticmethod
    def extract_position_level(text: str) -> Tuple[Optional[str], str]:
        """
        Extracts position level (Senior, Middle, etc.) from text.
        
        Args:
            text: Position text (e.g., "SENIOR AI ENGINEER")
            
        Returns:
            Tuple of (level, cleaned_text)
        """
        LEVEL_PATTERNS = [
            r'\b(SENIOR)\b',
            r'\b(JUNIOR)\b', 
            r'\b(MIDDLE)\b',
            r'\b(LEAD)\b',
            r'\b(INTERN|INTERNSHIP)\b',
            r'\b(ENTRY[- ]LEVEL)\b',
            r'\b(PRINCIPAL)\b',
            r'\b(STAFF)\b',
            r'\b(SR\.)\b',
            r'\b(JR\.)\b'
        ]
        
        upper_text = text.upper()
        found_level = None
        
        for pattern in LEVEL_PATTERNS:
            match = re.search(pattern, upper_text, re.IGNORECASE)
            if match:
                found_level = match.group(1).upper()
                # Remove level from text
                clean_pattern = re.compile(re.escape(match.group(1)), re.IGNORECASE)
                text = clean_pattern.sub('', text, 1)
                break
        
        if found_level:
            # Clean up separators
            text = re.sub(r'\s+/\s*/\s*', '/', text)
            text = re.sub(r'^\s*[/\s]+|[/\s]+\s*$', '', text)
            text = ' '.join(text.split()).strip()
        
        return found_level, TextNormalizer.normalize(text)