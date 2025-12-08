import os
import sys
from dotenv import load_dotenv
from app.vector_db import VectorDBFactory, ConnectionParams, CustomEmbedder


# Initialize vector DB manager
load_dotenv()
host = os.getenv("QDRANT_HOST")
port = os.getenv("QDRANT_PORT")
embedding_model = os.getenv("EMBEDDING_MODEL_NAME")
collection_name = os.getenv("TEST_COLLECTION_NAME")
collection_metadata = {
    "about":"test collection"
}

embedder = CustomEmbedder(embedding_model)
db_manager = VectorDBFactory.create_manager(
    db_type="qdrant",
    embedder=embedder
)

# Connect to database
params = ConnectionParams(host="localhost", port=6333)
try:
    if db_manager.connect(params):
        # Create or get collection
        if collection_name not in db_manager.list_collections():
            db_manager.create_collection(collection_name,collection_metadata)
            print(f"Test collections has been crated as {collection_name}")
        else:
            print(f"Test collections has been found.{collection_name} will be deleted and created again")
            db_manager.delete_collection(collection_name)
            print (f"{collection_name} collections has been deleted")
            db_manager.create_collection(collection_name, collection_metadata)
            print(f"Test collections has been crated as {collection_name}")
except Exception as e:
    print(f"\nError during initialisation: {e}")
    import traceback
    traceback.print_exc()