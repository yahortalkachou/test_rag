"""
Testing of vector database connection.
"""
import os
from dotenv import load_dotenv
from app.vector_db import VectorDBFactory, ConnectionParams, CustomEmbedder


load_dotenv()
    
def db_test():
    host = os.getenv("QDRANT_HOST")
    port = os.getenv("QDRANT_PORT")
    embedding_model = os.getenv("EMBEDDING_MODEL_NAME")
    cv_collection_name = os.getenv("TEST_COLLECTION_NAME")
    project_collection_name = os.getenv("TEST_COLLECTION_NAME") + "_projects"
    passed = False
    embedder = CustomEmbedder(embedding_model)
    db_manager = VectorDBFactory.create_manager(
        db_type="qdrant",
        embedder=embedder
    )

    params = ConnectionParams(host=host, port=port)
    try:
        if db_manager.connect(params):
            db_manager.recreate_collection (cv_collection_name)
            db_manager.recreate_collection (project_collection_name)
            passed = True
            return passed
    except Exception as e:
        print(f"\nError during initialisation: {e}")
        import traceback
        traceback.print_exc()
if __name__ == "__main__":
    if db_test():
        print("DB test PASSED!")
    else:
        print("DB test FAILED!")