from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from enum import Enum

class VectorDBType(Enum):
    """Supported vector database types"""
    CHROMA = "chroma"
    QDRANT = "qdrant"

@dataclass
class ConnectionParams:
    """Connection parameters for vector databases"""
    host: str
    port: int = 8000
    api_key: str | None = None
    https: bool = False
    
    # Qdrant specific
    prefer_grpc: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert parameters to dictionary"""
        return {
            "host": self.host,
            "port": self.port,
            "api_key": self.api_key,
            "https": self.https,
            "prefer_grpc": self.prefer_grpc
        }
    
@dataclass
class SearchResult:
    """Search result from vector database"""
    id: str
    document: str
    metadata: dict[str, Any]
    score: float
    distance: float | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert search result to dictionary"""
        return {
            "id": self.id,
            "document": self.document,
            "metadata": self.metadata,
            "score": self.score,
            "distance": self.distance
        }

@dataclass
class CollectionInfo:
    """Collection information and statistics"""
    name: str
    count: int
    metadata: dict[str, Any]
    dimensions: int | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert collection info to dictionary"""
        return {
            "name": self.name,
            "count": self.count,
            "metadata": self.metadata,
            "dimensions": self.dimensions
        }

# ============ EMBEDDER ABSTRACTION ============

class BaseEmbedder(ABC):
    """Base class for text embedders"""
    
    @abstractmethod
    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts"""
        pass
    
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Dimensionality of embeddings"""
        pass

class CustomEmbedder(BaseEmbedder):
    """Adapter for custom embedder implementation"""
    
    def __init__(self, embedder_path: str):
        from embedding.model_embedder import Embedder
        self._embedder = Embedder(embedder_path)
    
    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using custom embedder"""
        return self._embedder.get_embeddings(texts)
    
    @property
    def dimensions(self) -> int:
        """Get embedding dimensions from first test embedding"""
        if not hasattr(self, '_dimensions'):
            test_embedding = self.get_embeddings(["test"])[0]
            self._dimensions = len(test_embedding)
        return self._dimensions

# ============ ABSTRACT MANAGER ============

class VectorDBManager(ABC):
    """Abstract vector database manager"""
    
    def __init__(self, embedder: BaseEmbedder | None = None):
        self.embedder = embedder
        self._is_connected = False
    
    @abstractmethod
    def connect(self, params: ConnectionParams) -> bool:
        """Connect to database"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from database"""
        pass
    
    @abstractmethod
    def list_collections(self) -> list[str]:
        """List all collections"""
        pass
    
    @abstractmethod
    def get_collection_info(self, name: str) -> CollectionInfo:
        """Get collection information"""
        pass
    
    @abstractmethod
    def create_collection(self, name: str, metadata: dict | None = None) -> bool:
        """Create new collection"""
        pass
    
    @abstractmethod
    def delete_collection(self, name: str) -> bool:
        """Delete collection"""
        pass
    
    @abstractmethod
    def insert_documents(
        self,
        collection_name: str,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str]
    ) -> bool:
        """Insert documents into collection"""
        pass
    
    @abstractmethod
    def search(
        self,
        collection_name: str,
        query_text: str | None = None,
        query_embedding: list[float] | None = None,
        limit: int = 10
    ) -> list[SearchResult]:
        """Search by text or embedding"""
        pass
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to database"""
        return self._is_connected
    
    @property
    def db_type(self) -> VectorDBType:
        """Get database type"""
        pass
    
    def search_by_text(self, collection_name: str, query: str, limit: int = 10) -> list[SearchResult]:
        """Convenience method for text-based search"""
        if self.embedder:
            embedding = self.embedder.get_embeddings([query])[0]
            return self.search(collection_name, query_embedding=embedding, limit=limit)
        else:
            return self.search(collection_name, query_text=query, limit=limit)


if __name__ == "__main__":
    pass