"""
Testing of semantic search and filtering in vector database.
"""
import os
import json
from dotenv import load_dotenv
from app.vector_db import VectorDBType, VectorDBFactory, ConnectionParams, CustomEmbedder

load_dotenv()
with open("app/tests/test_queries.json","r") as f:
    testing_params = json.load(f)
def search_test (search_in_projects: bool = False):
    passed = False
    collection_name = os.getenv("TEST_COLLECTION_NAME") if not search_in_projects else os.getenv("TEST_COLLECTION_NAME")+"_projects"
    print(collection_name)
    semantic_search_query = testing_params["cv_semantic_search_query"]
    search_filters = testing_params["cv_search_filters"]
    cv_filterd_search_query = testing_params["cv_filterd_search_query"]
    embedder = CustomEmbedder(os.getenv("EMBEDDING_MODEL_NAME"))
    embeddings = embedder.get_embeddings([semantic_search_query])[0]
    db_manager = VectorDBFactory.create_manager(
            db_type=VectorDBType.QDRANT,
            embedder=embedder
        )
    params = ConnectionParams(host=os.getenv("QDRANT_HOST"), port=os.getenv("QDRANT_PORT"))
    if db_manager.connect(params):
        if collection_name not in db_manager.list_collections():
            print(f'''Test collection was not found. Run "pesonal_info_parser_test.py" to create
                test collection and insert testing data. ''')
            return passed
        res = db_manager.search(collection_name=collection_name, query_embedding=embeddings)
        if (res[0].metadata["name"]) == testing_params["expected_cv_semantic_search_name"]:
            print("Semantic search test PASSED!")
        else:
            print("Semantic search test FAILED!")
            return passed
        res = db_manager.filtered_search(
            collection_name=collection_name,
            query=cv_filterd_search_query,
            filters=search_filters,
            limit=3
        )
        if (res[0].metadata["name"]) == testing_params["expected_cv_filtered_search_name"]:
            print("Search tests PASSED!")
            passed = True
            return passed
    else:
        print("no connection")
if __name__ == "__main__":
    search_test(True)