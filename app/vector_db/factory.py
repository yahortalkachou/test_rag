from .manager import VectorDBType, BaseEmbedder, VectorDBManager
from .chroma import ChromaManager
from .qdrant import QdrantManager
class VectorDBFactory:
    """Factory for creating database managers"""
    
    @staticmethod
    def create_manager(
        db_type: VectorDBType| str,
        embedder: BaseEmbedder | None = None
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