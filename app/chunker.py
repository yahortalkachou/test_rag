import re
from typing import List, Callable
from abc import ABC, abstractmethod


class SimpleChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
        
    def chunk_by_sentences(self, text: str) -> List[str]:
        """Sentence Parse simple"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Если добавление предложения превысит размер чанка
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    # Сохраняем перекрытие
                    overlap_sentences = current_chunk.split()[-self.overlap//10:]
                    current_chunk = " ".join(overlap_sentences) + " "
                else:
                    # Если одно предложение больше чанка, разбиваем его
                    chunks.extend(self._split_long_sentence(sentence))
                    continue
                    
            current_chunk += sentence + ". "
            
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
    
    def chunk_by_words(self, text: str, words_per_chunk: int = 200) -> List[str]:
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), words_per_chunk - self.overlap//5):
            chunk = " ".join(words[i:i + words_per_chunk])
            chunks.append(chunk)
            
        return chunks
    
    def chunk_by_fixed_size(self, text: str) -> List[str]:
        chunks = []
        
        for i in range(0, len(text), self.chunk_size - self.overlap):
            chunk = text[i:i + self.chunk_size]
            chunks.append(chunk)
            
        return chunks
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        words = sentence.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size//10):
            chunk = " ".join(words[i:i + self.chunk_size//10])
            chunks.append(chunk)
            
        return chunks

