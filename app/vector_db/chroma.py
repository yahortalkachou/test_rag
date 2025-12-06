from typing import Any
import chromadb
from .manager import VectorDBManager, VectorDBType, BaseEmbedder, ConnectionParams,\
    CollectionInfo, SearchResult

class ChromaManager(VectorDBManager):
    """ChromaDB manager implementation"""
    
    def __init__(self, embedder: BaseEmbedder | None = None):
        super().__init__(embedder)
        self.client: chromadb.HttpClient | None = None
    
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
    
    def list_collections(self) -> list[str]:
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
    
    def create_collection(self, name: str, metadata: dict | None = None) -> bool:
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
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str]
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
        query_text: str | None = None,
        query_embedding: list[float] | None = None,
        limit: int = 10
    ) -> list[SearchResult]:
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
    
    def _format_results(self, results: dict) -> list[SearchResult]:
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