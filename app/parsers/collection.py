"""
Manager for collections of parsed CVs.
"""
import json
from typing import Any
from app.parsers.models import CV
from app.parsers.inno_parser import InnoStandardParser
from app.chunker.chunker import SimpleChunker



class CVCollection:
    """Manager for collections of parsed CVs."""
    
    def __init__(self, chunk_size: int, chunk_overlap: int) :

        self.cvs: list[CV] = []
        self.parser = InnoStandardParser()
        self.chunker = SimpleChunker(chunk_size, chunk_overlap)
        self.cv_chunks = []
        self.project_chunks = []
    
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
    
    def get_cv(self, cv_id: str) -> CV | None:
        """Retrieves a CV by its ID."""
        for cv in self.cvs:
            if cv.cv_id == cv_id:
                return cv
        return None
    
    def get_all_metadata(self) -> list[dict[str, Any]]:
        """Returns all metadata for vector database."""
        return [cv.metadata for cv in self.cvs]
    
    def get_all_texts(self) -> list[str]:
        """Returns all text content for vector database."""
        return [cv.text for cv in self.cvs]
    
    def get_personal_data(self, cv_id: str) -> dict[str, Any] | None:
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
    
    def generate_chunks(self, method: str) -> bool:
        '''Chunk presonal and project data chunking'''
        try:
            for cv in self.cvs:
                cv_chunks = self.chunker.chunk_by_sentences(cv.text,cv.metadata)
                self.cv_chunks += cv_chunks
                for project in cv.projects:
                    project_chunks = self.chunker.chunk_by_sentences(project.description, project.metadata)
                    self.project_chunks += project_chunks
            return True
        except Exception as e:
            print(f"\nError during chunking: {e}")
            return False
    
    def prepare_chunks_qdrant (self):
        '''Prepare for qdrant insertion generated chunks of
        presonal and project data chunking. Chunks suppose to be generated before
        '''
        vector_db_data_cv = {
            "texts":[],
            "metadatas":[],
            "ids":[]
        }
        vector_db_data_project = {
            "texts":[],
            "metadatas":[],
            "ids":[]
        }
        for chunk in self.cv_chunks:
            #print(f"id: {chunk.id}")
            vector_db_data_cv["ids"].append(chunk.id)
            vector_db_data_cv["texts"].append(chunk.text)
            vector_db_data_cv["metadatas"].append(chunk.metadata)
        for (project_number,chunk) in enumerate(self.project_chunks):
            vector_db_data_project["ids"].append(f"pr#{project_number}_{chunk.id}")
            vector_db_data_project["texts"].append(chunk.text)
            vector_db_data_project["metadatas"].append(chunk.metadata)
        return vector_db_data_cv, vector_db_data_project