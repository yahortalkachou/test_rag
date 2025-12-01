from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import chromadb
from embedding.model_embedder import Embedder
from chunker import PersonalInfo

class VectorDBManager(ABC):
    """Abstract base class for vector database managers."""
    
    @abstractmethod
    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """Establish connection to the vector database."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Close connection to the vector database."""
        pass
    
    @abstractmethod
    def create_collection(self, collection_name: str, metadata: Dict[str, Any]) -> bool:
        """Create a new collection with specified metadata."""
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """Delete existing collection."""
        pass
    
    @abstractmethod
    def insert_documents(
        self, 
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> bool:
        """Insert documents with metadata into collection."""
        pass
    
    @abstractmethod
    def search(
        self,
        collection_name: str,
        query_embeddings: List[float],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search similar documents with optional metadata filtering."""
        pass
    
    @abstractmethod
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection statistics and metadata."""
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active."""
        pass
    
class ChromaHttpDBManager(VectorDBManager):
    """ChromaDB HTTP client implementation of VectorDBManager."""
    
    def __init__(self):
        self.client = None
        self._is_connected = False
        self.embedder = None
        
    
    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """Establish HTTP connection to ChromaDB server."""
        try:
            self.client = chromadb.HttpClient(
                host=connection_params['host'],
                port=connection_params.get('port', 8000),
                ssl=connection_params.get('ssl', False),
                headers=connection_params.get('headers', {})
            )
            
            self.client.heartbeat()
            self._is_connected = True
            return True
            
        except Exception as e:
            print(f"HTTP connection error: {e}")
            self._is_connected = False
            return False
    
    def set_embedder(self, embedder_path: str):
        '''Set custom embedder'''
        self.embedder = Embedder(embedder_path)
    
    def disconnect(self) -> bool:
        """Close HTTP connection."""
        try:
            self.client = None
            self._is_connected = False
            return True
        except Exception as e:
            print(f"Disconnection error: {e}")
            return False
        
    def list_collections (self):
        '''Get list of all collections'''
        if (self._is_connected):
            collections = self.client.list_collections()
            print (f"Collections:")
            for coll in collections:
                print (coll.name)
            return collections
        else:
            print ("No connection")
    
    def create_collection(self, collection_name: str, metadata: Dict[str, Any]) -> bool:
        """Create a new collection on ChromaDB server."""
        if not self._is_connected:
            return False
        
        try:
            self.client.create_collection(
                name=collection_name,
                metadata=metadata
            )
            return True
        except Exception as e:
            print(f"Collection creation error: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete collection from ChromaDB server."""
        if not self._is_connected:
            return False
        
        try:
            self.client.delete_collection(name=collection_name)
            print(f"{collection_name} has been deleted")
            return True
        except Exception as e:
            print(f"Collection deletion error: {e}")
            return False
    
    def insert_documents(
        self, 
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> bool:
        """Insert documents into remote ChromaDB collection."""
        if not self._is_connected:
            return False
        
        try:
            if not self.embedder:
                print("With chroma embedder")
                collection = self.client.get_collection(collection_name)
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                return True
            else:
                print ("With custom embedder")
                collection = self.client.get_collection(collection_name)
                #print(f"docs:{metadatas}")
                embeddings = self.embedder.get_embeddings(documents)
                print("2")
                collection.add(
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents,
                    ids=ids
                )
                for e in embeddings:
                    print (f"e:{e[:3]}\n")
        except Exception as e:
            print(f"Insertion error: {e}")
            return False
    
    def search(
        self,
        collection_name: str,
        query_embeddings: List[float],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search in remote ChromaDB collection."""
        if not self._is_connected:
            return []
        
        try:
            collection = self.client.get_collection(collection_name)
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=limit,
                where=filters
            )
            
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information from remote server."""
        if not self._is_connected:
            return {}
        
        try:
            collection = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "count": collection.count(),
                "metadata": collection.metadata
            }
        except Exception as e:
            print(f"Collection info error: {e}")
            return {}
        
    def add_personal_data(self, data: PersonalInfo, collection_name: str):
        self.client.get_collection(collection_name)
            
    
    @property
    def is_connected(self) -> bool:
        """Check if HTTP connection is active."""
        return self._is_connected
    
    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format ChromaDB results to standard format."""
        formatted = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                formatted.append({
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'id': results['ids'][0][i],
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
        return formatted
    
    def get_server_version(self) -> str:
        """Get ChromaDB server version (HTTP client specific)."""
        if not self._is_connected:
            return "Not connected"
        
        try:
            return self.client.get_version()
        except Exception as e:
            return f"Error: {e}"


# Usage example
if __name__ == "__main__":
    # Initialize HTTP ChromaDB manager
    http_manager = ChromaHttpDBManager()
    
    # Connection parameters for remote server
    connection_params = {
        'mode': 'http',
        'host': 'localhost',  # or remote server IP
        'port': 8000,
        'ssl': False,
        'headers': {
            'X-Client-Name': 'CVSearchApp',
            # 'Authorization': 'Bearer your-token'  # if auth enabled
        }
    }
    
    # Connect to remote ChromaDB server
    if http_manager.connect(connection_params):
        print("Successfully connected to ChromaDB HTTP server")
        print(f"Server version: {http_manager.get_server_version()}")
        
        # Create collection
        collection_metadata = {
            "description": "CV personal collection",
            "owner": "E"
        }
        http_manager.delete_collection("cv_chunks")
        http_manager.create_collection("cv_personal_data", collection_metadata)
        
        
    else:
        print("Failed to connect to ChromaDB HTTP server")