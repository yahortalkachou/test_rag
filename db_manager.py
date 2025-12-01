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
    

class ChromaDBManager(VectorDBManager):
    """ChromaDB implementation of VectorDBManager."""
    
    def __init__(self):
        self.client = None
        self._is_connected = False
    
    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """Establish connection to ChromaDB."""
        try:
            if connection_params.get('mode') == 'persistent':
                self.client = chromadb.PersistentClient(
                    path=connection_params['path'],
                    settings=Settings(anonymized_telemetry=False)
                )
            else:
                self.client = chromadb.EphemeralClient()
            
            self._is_connected = True
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            self._is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """Close connection to ChromaDB."""
        try:
            self.client = None
            self._is_connected = False
            return True
        except Exception as e:
            print(f"Disconnection error: {e}")
            return False
    
    def create_collection(self, collection_name: str, metadata: Dict[str, Any]) -> bool:
        """Create a new collection in ChromaDB."""
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
        """Delete collection from ChromaDB."""
        if not self._is_connected:
            return False
        
        try:
            self.client.delete_collection(name=collection_name)
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
        """Insert documents into ChromaDB collection."""
        if not self._is_connected:
            return False
        
        try:
            collection = self.client.get_collection(collection_name)
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return True
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
        """Search in ChromaDB collection."""
        if not self._is_connected:
            return []
        
        try:
            collection = self.client.get_collection(collection_name)
            results = collection.query(
                query_embeddings=[query_embeddings],
                n_results=limit,
                where=filters
            )
            
            return self._format_results(results)
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get ChromaDB collection information."""
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
    
    @property
    def is_connected(self) -> bool:
        """Check if ChromaDB connection is active."""
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
            
            # Test connection by getting version
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
                collection = self.client.get_collection(collection_name)
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                return True
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
        
    #     # Get collection info
    #     info = http_manager.get_collection_info("cv_chunks")
    #     print(f"Collection info: {info}")
        
    #     # Example: Insert test data
    #     test_documents = ["Middle with no experience"]
    #     test_metadatas = [{
    #         "cv_id": "test_002",
    #         "chunk_number": 1,
    #         "name": "Petr",
    #         "level": "middle",
    #         "specialisation": "Machine Learning"
    #     }]
    #     test_ids = ["doc#1"]
    #     http_manager.insert_documents(
    #     collection_name="cv_chunks",
    #     documents=test_documents[0],
    #     metadatas=test_metadatas,
    #     ids=test_ids
    # )
    #     test_documents = ["Senior with a vast experience"]
    #     test_metadatas = [{
    #         "cv_id": "test_003",
    #         "chunk_number": 1,
    #         "name": "Kate",
    #         "level": "senior",
    #         "specialisation": "Machine Learning"
    #     }]
        
    #     test_ids = ["doc#2"]
    #     http_manager.insert_documents(
    #     collection_name="cv_chunks",
    #     documents=test_documents[0],
    #     metadatas=test_metadatas,
    #     ids=test_ids
    # )
    #     test_ids = ["doc_001"]
    #     http_manager.set_embedder("embedding/models/all-MiniLM-L12-v2")
    #     embeddings = http_manager.embedder.get_embeddings(["Strong developer"])
    #     info = http_manager.get_collection_info("cv_chunks")
    #     print(f"Collection info: {info}")
    #     print(f"embeddings: {embeddings[0][:10]}")
    #     print ("res",http_manager.search("cv_chunks",embeddings))
    #     # http_manager.insert_documents(
    #     #     collection_name="cv_chunks",
    #     #     documents=test_documents,
    #     #     metadatas=test_metadatas,
    #     #     ids=test_ids
    #     # )
    #     # print("Test data inserted successfully")
        
    else:
        print("Failed to connect to ChromaDB HTTP server")