import re
from typing import List, Callable
from abc import ABC, abstractmethod

class CVData (ABC):
    @abstractmethod
    def get_description (self):
        pass
    
    @abstractmethod
    def set_embeddings (self, embeddings):
        pass
    
    @abstractmethod
    def get_metadatas (self):
        pass
    
    @abstractmethod
    def get_embeddings (self):
        pass
    
class PersonalInfo (CVData):
    def __init__(self, docs: List[dict]):
        self.metadatas, self.texts = [{
                "name": data["name"],
                "level": data["level"],
                "roles": data["roles"],
                "education": data["education"],
                "languages": data["languages"],
                "domains": data["domains"]
            } for data in docs ]
        
        self.texts = [data["description"] for data in docs]
        self.embeddings = None
    
    def __repr__(self):
        return 

    def get_descriptions(self):
        return self.texts
    
    def set_embeddings(self, embeddings):
        self.embeddings = embeddings
    
    def get_metadatas(self):
        if self.metadata:
            return self.metadata
    
    def get_embeddings(self):
        if self.embeddings:
            return self.embeddings
        

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
        """Разделение текста на чанки по количеству слов"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), words_per_chunk - self.overlap//5):
            chunk = " ".join(words[i:i + words_per_chunk])
            chunks.append(chunk)
            
        return chunks
    
    def chunk_by_fixed_size(self, text: str) -> List[str]:
        """Разделение текста на чанки фиксированного размера символов"""
        chunks = []
        
        for i in range(0, len(text), self.chunk_size - self.overlap):
            chunk = text[i:i + self.chunk_size]
            chunks.append(chunk)
            
        return chunks
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """Разбивает слишком длинное предложение"""
        words = sentence.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size//10):
            chunk = " ".join(words[i:i + self.chunk_size//10])
            chunks.append(chunk)
            
        return chunks

# Пример использования
if __name__ == "__main__":
    # Пример текста для тестирования
    sample_text = """
    Это пример текста для тестирования чанкера. Здесь содержится несколько предложений.
    Каждое предложение должно быть обработано отдельно. Чанкер разбивает длинные тексты
    на более мелкие части для последующей обработки. Это полезно для работы с языковыми
    моделями, которые имеют ограничения на длину входного текста.
    """
    
    chunker = SimpleChunker(chunk_size=100, overlap=20)
    
    print("Разделение по предложениям:")
    sentence_chunks = chunker.chunk_by_sentences(sample_text)
    for i, chunk in enumerate(sentence_chunks):
        print(f"Чанк {i+1}: {chunk[:50]}...")
    
    print("\nРазделение по словам:")
    word_chunks = chunker.chunk_by_words(sample_text, words_per_chunk=20)
    for i, chunk in enumerate(word_chunks):
        print(f"Чанк {i+1}: {chunk[:50]}...")
    
    print("\nРазделение по фиксированному размеру:")
    fixed_chunks = chunker.chunk_by_fixed_size(sample_text)
    for i, chunk in enumerate(fixed_chunks):
        print(f"Чанк {i+1}: {chunk[:50]}...")