import re

from dataclasses import dataclass, field
from typing import Any
import uuid

@dataclass
class Chunk:
    """Project model extracted from CV."""
    
    text: str
    id: int
    metadata: dict
    
    
    @classmethod
    def from_dict(cls, data: dict[str, Any], meta: dict) -> 'Chunk':
        """Creates Project instance from dictionary."""
        return cls(
            text=data.get("text", ""),
            id=data.get("id", -1),
            metadata = {
                **meta,
                "chunk_number": data.get("chunk_number", -1),
                "chunks_overall": data.get("chunks_overall",-1)
            }
        )
    

    
    
class SimpleChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    
    def chunk_by_sentences(self, text: str, meta: dict) -> list[Chunk]:
        """Sentence Parse simple"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        texts = []
        chunks = []
        current_chunk = ""
        
        for (i,sentence) in enumerate(sentences):
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    texts.append(current_chunk)
                    overlap_sentences = current_chunk.split()[-self.overlap//10:]
                    current_chunk = " ".join(overlap_sentences) + " "
                else:
                    texts.extend(self._split_long_sentence(sentence))
                    continue
                    
            current_chunk += sentence + ". "
            
        if current_chunk:
            texts.append(current_chunk)
        i =0 

        for (i,text) in enumerate(texts):
            chunks.append(Chunk.from_dict(
                    {
                        "text": text,
                        "id": f"{meta.get('CV_id',uuid.uuid4())}_chunk#{i+1}", #temp id generation. Will be replaced
                        "chunk_number": i+1,
                        "chunks_overall": len(texts)
                    },
                    meta
                        )
                            )
        return chunks
    
    def chunk_by_words(self, text: str, words_per_chunk: int = 200) -> list[str]:
        words = text.split()
        texts = []
        
        for i in range(0, len(words), words_per_chunk - self.overlap//5):
            chunk = " ".join(words[i:i + words_per_chunk])
            texts.append(chunk)
            
        return {
            "texts": texts,
            "chunk_ids" : range(0,len(texts)),
            "texts_all": len(texts) 
        }
    
    def chunk_by_fixed_size(self, text: str) -> list[str]:
        texts = []
        
        for i in range(0, len(text), self.chunk_size - self.overlap):
            chunk = text[i:i + self.chunk_size]
            texts.append(chunk)
            
        return {
            "texts": texts,
            "chunk_ids" : range(0,len(texts)),
            "texts_all": len(texts) 
        }
    
    def _split_long_sentence(self, sentence: str) -> list[str]:
        words = sentence.split()
        texts = []
        
        for i in range(0, len(words), self.chunk_size//10):
            chunk = " ".join(words[i:i + self.chunk_size//10])
            texts.append(chunk)
            
        return texts

