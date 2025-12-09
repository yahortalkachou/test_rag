from typing import Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.vector_db.manager import VectorDBManager, VectorDBType, BaseEmbedder, ConnectionParams,\
    CollectionInfo, SearchResult

class QdrantManager(VectorDBManager):
    """Qdrant vector database manager"""
    
    def __init__(self, embedder: BaseEmbedder | None = None):
        super().__init__(embedder)
        if embedder is None:
            raise ValueError("Qdrant requires an embedder for vector operations")
        self.client: QdrantClient | None = None
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
    
    def list_collections(self) -> list[str]:
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
    
    def create_collection(self, name: str, metadata: dict | None = None) -> bool:
        """Create new collection in Qdrant"""
        if not self._is_connected:
            return False
        try:
            vectors_config = models.VectorParams(
                size=self._dimensions,
                distance=models.Distance.COSINE
            )
            
            self.client.create_collection(
                collection_name=name,
                vectors_config=vectors_config,
                metadata=metadata,
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
            print (f"Collection {name}  has been deleted")
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
        query_text: str | None = None,
        query_embedding: list[float] | None = None,
        limit: int = 10
    ) -> list[SearchResult]:
        """Search in Qdrant collection"""
        if not self._is_connected:
            return []
        try:
            if query_embedding is None and query_text is not None:
                query_embedding = self.embedder.get_embeddings([query_text])[0]
            elif query_embedding is None:
                return []
            search_result = self.client.query_points(
                collection_name=collection_name,
                query=query_embedding,
                limit=limit
            )
            return self._format_results( search_result)
        except Exception as e:
            print(f"Error searching in Qdrant: {e}")
            import traceback
            traceback.print_exc()  # Add error details
            return []
    
    def filtered_search(
        self,
        collection_name: str,
        query: str,
        filters: dict[str, dict[str, Any]],
        limit: int = 10
    ) -> list[SearchResult]:
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
            return self._format_results(search_result) 
        except Exception as e:
            print(f"Error in filtered_search: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _build_filter_from_format(self, filters: dict[str, dict[str, Any]]) -> Any:
        """
        Converts dict to Qdrant filters        
        Input data format:
        {
            "field_name": {
                "must": bool,           # True = must, False = should
                "values": list[Any]     # list of values
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

    def check_collection(self, collection: str) -> bool:
        """Check the collection with such name"""
        if not self._is_connected:
            return False
        if collection in self.list_collections():
            return True
        return False
    
    def recreate_collection (self, collection: str, meatadata: dict | None = None):
        if not meatadata:
            meatadata = {
                "about": "new collection"
            }
        if not self.check_collection(collection):
            self.create_collection(collection, meatadata)
 
        else:
            print(f"{collection} has been found.{collection} will be deleted and created again")
            self.delete_collection(collection)
            self.create_collection(collection, meatadata)
        
        
    
    
    def _format_results(self, results: list[models.ScoredPoint]) -> list[SearchResult]:
        """Format Qdrant results to standard format"""
        formatted = []
        for result in results:
            formatted.append(SearchResult(
                id=str(result[1][0].payload.get("text_id")),
                document=result[1][0].payload.get("document"),
                metadata=result[1][0].payload.get("metadata"),
                score=result[1][0].score,
                distance=1.0 - result[1][0].score  # Convert similarity to distance
            ))
        
        return formatted