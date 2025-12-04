from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import chromadb
from qdrant_client import QdrantClient
from qdrant_client.http import models
import numpy as np

# ============ DATA MODELS ============

class VectorDBType(Enum):
    """Supported vector database types"""
    CHROMA = "chroma"
    QDRANT = "qdrant"

@dataclass
class ConnectionParams:
    """Connection parameters for vector databases"""
    host: str
    port: int = 8000
    api_key: Optional[str] = None
    https: bool = False
    
    # Qdrant specific
    prefer_grpc: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        return {
            "host": self.host,
            "port": self.port,
            "api_key": self.api_key,
            "https": self.https,
            "prefer_grpc": self.prefer_grpc
        }
# @dataclass
# class SearchParams:
#     """Search params for filtering"""
#     params = {
#         "field": {
#             "must":True,
#             "values": [val1, val2, val3]
#         },
#         "param2":{
#             "must":False,
#             "values": [val4, val5, val6]
#         }
#     }
    

@dataclass
class SearchResult:
    """Search result from vector database"""
    id: str
    document: str
    metadata: Dict[str, Any]
    score: float
    distance: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
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
    metadata: Dict[str, Any]
    dimensions: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
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
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
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
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
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
    
    def __init__(self, embedder: Optional[BaseEmbedder] = None):
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
    def list_collections(self) -> List[str]:
        """List all collections"""
        pass
    
    @abstractmethod
    def get_collection_info(self, name: str) -> CollectionInfo:
        """Get collection information"""
        pass
    
    @abstractmethod
    def create_collection(self, name: str, metadata: Optional[Dict] = None) -> bool:
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
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> bool:
        """Insert documents into collection"""
        pass
    
    @abstractmethod
    def search(
        self,
        collection_name: str,
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        limit: int = 10
    ) -> List[SearchResult]:
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
    
    def search_by_text(self, collection_name: str, query: str, limit: int = 10) -> List[SearchResult]:
        """Convenience method for text-based search"""
        if self.embedder:
            embedding = self.embedder.get_embeddings([query])[0]
            return self.search(collection_name, query_embedding=embedding, limit=limit)
        else:
            return self.search(collection_name, query_text=query, limit=limit)

# ============ CHROMA IMPLEMENTATION ============

class ChromaManager(VectorDBManager):
    """ChromaDB manager implementation"""
    
    def __init__(self, embedder: Optional[BaseEmbedder] = None):
        super().__init__(embedder)
        self.client: Optional[chromadb.HttpClient] = None
    
    @property
    def db_type(self) -> VectorDBType:
        return VectorDBType.CHROMA
    
    def connect(self, params: ConnectionParams) -> bool:
        """Connect to ChromaDB server"""
        try:
            self.client = chromadb.HttpClient(
                host=params.host,
                port=params.port,
                ssl=params.https,
                headers={"Authorization": params.api_key} if params.api_key else {}
            )
            self.client.heartbeat()
            self._is_connected = True
            return True
        except Exception as e:
            print(f"Chroma connection error: {e}")
            self._is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from ChromaDB"""
        try:
            self.client = None
            self._is_connected = False
            return True
        except Exception:
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections in ChromaDB"""
        if not self._is_connected:
            return []
        
        try:
            collections = self.client.list_collections()
            return [coll.name for coll in collections]
        except Exception as e:
            print(f"Error listing collections: {e}")
            return []
    
    def get_collection_info(self, name: str) -> CollectionInfo:
        """Get information about specific collection"""
        if not self._is_connected:
            return CollectionInfo(name=name, count=0, metadata={})
        
        try:
            collection = self.client.get_collection(name)
            return CollectionInfo(
                name=name,
                count=collection.count(),
                metadata=collection.metadata or {}
            )
        except Exception:
            return CollectionInfo(name=name, count=0, metadata={})
    
    def create_collection(self, name: str, metadata: Optional[Dict] = None) -> bool:
        """Create new collection in ChromaDB"""
        if not self._is_connected:
            return False
        
        try:
            self.client.create_collection(
                name=name,
                metadata=metadata or {}
            )
            return True
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False
    
    def delete_collection(self, name: str) -> bool:
        """Delete collection from ChromaDB"""
        if not self._is_connected:
            return False
        
        try:
            self.client.delete_collection(name)
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False
    
    def insert_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> bool:
        """Insert documents into ChromaDB collection"""
        if not self._is_connected:
            return False
        
        try:
            collection = self.client.get_collection(collection_name)
            
            if self.embedder:
                embeddings = self.embedder.get_embeddings(documents)
                collection.add(
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            else:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            return True
        except Exception as e:
            print(f"Error inserting documents: {e}")
            return False
    
    def search(
        self,
        collection_name: str,
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """Search in ChromaDB collection"""
        if not self._is_connected:
            return []
        
        try:
            collection = self.client.get_collection(collection_name)
            
            if query_embedding is not None:
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit
                )
            elif query_text is not None:
                results = collection.query(
                    query_texts=[query_text],
                    n_results=limit
                )
            else:
                return []
            
            return self._format_results(results)
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def _format_results(self, results: Dict) -> List[SearchResult]:
        """Format ChromaDB results to standard format"""
        formatted = []
        
        if results.get('documents') and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted.append(SearchResult(
                    id=results['ids'][0][i],
                    document=results['documents'][0][i],
                    metadata=results['metadatas'][0][i] if results['metadatas'] else {},
                    score=results['distances'][0][i] if results['distances'] else 0.0,
                    distance=results['distances'][0][i] if results['distances'] else None
                ))
        
        return formatted

# ============ QDRANT IMPLEMENTATION ============

class QdrantManager(VectorDBManager):
    """Qdrant vector database manager"""
    
    def __init__(self, embedder: Optional[BaseEmbedder] = None):
        super().__init__(embedder)
        if embedder is None:
            raise ValueError("Qdrant requires an embedder for vector operations")
        self.client: Optional[QdrantClient] = None
        self._dimensions = embedder.dimensions
    
    @property
    def db_type(self) -> VectorDBType:
        return VectorDBType.QDRANT
    
    def connect(self, params: ConnectionParams) -> bool:
        """Connect to Qdrant server"""
        try:
            url = f"{'https' if params.https else 'http'}://{params.host}:{params.port}"
            
            self.client = QdrantClient(
                url=url,
                api_key=params.api_key,
                prefer_grpc=params.prefer_grpc
            )
            
            # Verify connection
            self.client.get_collections()
            self._is_connected = True
            return True
        except Exception as e:
            print(f"Qdrant connection error: {e}")
            self._is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from Qdrant"""
        try:
            self.client = None
            self._is_connected = False
            return True
        except Exception:
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections in Qdrant"""
        if not self._is_connected:
            return []
        
        try:
            collections = self.client.get_collections()
            return [coll.name for coll in collections.collections]
        except Exception as e:
            print(f"Error listing collections: {e}")
            return []
    
    def get_collection_info(self, name: str) -> CollectionInfo:
        """Get information about Qdrant collection"""
        if not self._is_connected:
            return CollectionInfo(name=name, count=0, metadata={})
        
        try:
            collection = self.client.get_collection(name)
            
            # Get point count
            count_result = self.client.count(
                collection_name=name,
                exact=True
            )
            
            return CollectionInfo(
                name=name,
                count=count_result.count,
                metadata=collection.config.params or {},
                dimensions=self._dimensions
            )
        except Exception:
            return CollectionInfo(name=name, count=0, metadata={})
    
    def create_collection(self, name: str, metadata: Optional[Dict] = None) -> bool:
        """Create new collection in Qdrant"""
        if not self._is_connected:
            return False
        
        try:
            vectors_config = models.VectorParams(
                size=self._dimensions,
                distance=models.Distance.COSINE
            )
            
            # Qdrant has different API for collection creation
            # Metadata is handled differently than in Chroma
            
            self.client.create_collection(
                collection_name=name,
                vectors_config=vectors_config,
                metadata=metadata,
                # replication_factor=1,  # Optional parameter
                # shard_number=1,       # Optional parameter
            )
            
            print(f"Collection '{name}' created successfully in Qdrant")
            return True
            
        except Exception as e:
            print(f"Error creating collection in Qdrant: {e}")
            return False
    
    def delete_collection(self, name: str) -> bool:
        """Delete collection from Qdrant"""
        if not self._is_connected:
            return False
        
        try:
            self.client.delete_collection(name)
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False
    
    def insert_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> bool:
        """Insert documents into Qdrant collection"""
        if not self._is_connected:
            return False
        
        try:
            # Generate embeddings
            embeddings = self.embedder.get_embeddings(documents)
            
            # Prepare points for insertion
            points = []
            for i, (doc_id, embedding, document, metadata) in enumerate(
                zip(ids, embeddings, documents, metadatas)
            ):
                point = models.PointStruct(
                    id=i,  # Qdrant requires numeric IDs
                    vector=embedding,
                    payload={
                        "document": document,
                        "metadata": metadata,
                        "text_id": doc_id  # Preserve original text ID
                    }
                )
                points.append(point)
            
            # Insert points
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            return True
        except Exception as e:
            print(f"Error inserting documents: {e}")
            return False
    
    def search(
        self,
        collection_name: str,
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """Search in Qdrant collection"""
        if not self._is_connected:
            return []
        
        try:
            if query_embedding is None and query_text is not None:
                query_embedding = self.embedder.get_embeddings([query_text])[0]
            elif query_embedding is None:
                return []
            
            # FIX: Use query_points instead of search
            search_result = self.client.query_points(
                collection_name=collection_name,
                query=query_embedding,
                limit=limit
            )
            
            # return self._format_results(search_result)
            return search_result
        except Exception as e:
            print(f"Error searching in Qdrant: {e}")
            import traceback
            traceback.print_exc()  # Add error details
            return []
    
    def filtered_search(
        self,
        collection_name: str,
        query: str,
        filters: Dict[str, Dict[str, Any]],
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Filered search
        
        Args:
            collection_name: collection name
            query: querytext
            filters: :
                {
                    "level": {
                        "must": True,
                        "values": ["SENIOR", "MIDDLE"]
                    },
                    "languages": {
                        "must": True, 
                        "values": ["english", "german"]
                    },
                    "domains": {
                        "must": False,
                        "values": ["AI", "Machine Learning"]
                    }
                }
            limit: n-results
            
        Returns:
            list of results
        """
        if not self._is_connected:
            return []
        
        try:
            if not query or not isinstance(filters, dict):
                print("Error: Query and filters are required")
                return []
            
            embeddings = self.embedder.get_embeddings([query])
            
            query_embedding = embeddings[0]
            
            qdrant_filter = self._build_filter_from_format(filters)
            

            
            search_result = self.client.query_points(collection_name=collection_name,query_filter=qdrant_filter,query=query_embedding)
            
            return search_result
            
        except Exception as e:
            print(f"Error in filtered_search: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _build_filter_from_format(self, filters: Dict[str, Dict[str, Any]]) -> Any:
        """
        Converts dict to Qdrant filters        
        Input data format:
        {
            "field_name": {
                "must": bool,           # True = must, False = should
                "values": List[Any]     # list of values
            }
        }
        
        Returns:
            Qdrant Filter or None
        """
        from qdrant_client.http import models as qdrant_models
        
        must_conditions = []
        should_conditions = []
        
        for field_name, filter_config in filters.items():
            if not isinstance(filter_config, dict):
                print(f"Warning: Filter for '{field_name}' is not a dict, skipping")
                continue
            
            must = filter_config.get("must", True)
            values = filter_config.get("values", [])
            
            if not values:
                print(f"Warning: No values for filter '{field_name}', skipping")
                continue
            
            if not isinstance(values, list):
                values = [values]  

            field_path = f"metadata.{field_name}"
            
            field_condition = {
                "key": field_path,
                "match": {"any": values}  
            }
            
            if must:
                for value in values:
                    value_condition = {
                        "key": field_path,
                        "match": {"value": value}
                    }
                    must_conditions.append(value_condition)
            else:
                should_conditions.append(field_condition)
        
        filter_dict = {}
        
        if must_conditions:
            filter_dict["must"] = must_conditions
        
        if should_conditions:
            filter_dict["should"] = should_conditions
        
        if not filter_dict:
            return None
        
        return qdrant_models.Filter(**filter_dict)
    
    
    def _format_results(self, results: List[models.ScoredPoint]) -> List[SearchResult]:
        """Format Qdrant results to standard format"""
        formatted = []
        
        for result in results:
            formatted.append(SearchResult(
                id=str(result.payload.get("text_id", result.id)),
                document=result.payload.get("document", ""),
                metadata=result.payload.get("metadata", {}),
                score=result.score,
                distance=1.0 - result.score  # Convert similarity to distance
            ))
        
        return formatted

# ============ MANAGER FACTORY ============

class VectorDBFactory:
    """Factory for creating database managers"""
    
    @staticmethod
    def create_manager(
        db_type: Union[VectorDBType, str],
        embedder: Optional[BaseEmbedder] = None
    ) -> VectorDBManager:
        """Create manager for specified database type"""
        
        if isinstance(db_type, str):
            db_type = VectorDBType(db_type.lower())
        
        if db_type == VectorDBType.CHROMA:
            return ChromaManager(embedder)
        elif db_type == VectorDBType.QDRANT:
            return QdrantManager(embedder)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")



# ============ USAGE EXAMPLE ============

if __name__ == "__main__":
    pass