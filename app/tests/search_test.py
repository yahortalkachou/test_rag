"""
Testing of semantic search and filtering in vector database.
"""
import os
import json
from dotenv import load_dotenv
from app.vector_db import VectorDBType, VectorDBFactory, ConnectionParams, CustomEmbedder

load_dotenv()

def check_results(res: list = [], expected: str = "", verbose: bool = True) -> bool:
        passed = False
        for r in res:
            if verbose:
                print(f"Candidat's name: {r.metadata['candidate_name']} score: {r.score}")
            if r.metadata["candidate_name"] == expected and not passed:
                passed = True
                if not verbose:
                    return passed
        return passed
    
def search_test (storage: str = "PERSONAL_DATA", verbose: bool = False) -> bool:
    """Search testing. Use for testing personal and project data storage.
    The data suppose to be upserted before.  

    Args:
        mode (str, optional): Use "PERSONAL_DATA" or 
    "PROJECT_DATA" mode to test correspomding storage. Defaults to "PERSONAL_DATA".
        verbose (bool, optional): Additional outputs. Defaults to False.

    Returns:
        bool: True in case of success for both searching mods. 
        Otherwise -- False.
    """
    semantic_search_passed = False
    filtered_search_passed = False
    settings_file = os.getenv(f"{storage}_TEST_SETTINGS")
    collection_name = os.getenv(f"TEST_{storage}_COLLECTION_NAME") 
    if not settings_file:
        print(f"Incorrect storage arg. Use 'PERSONAL_DATA' or 'PROJECT_DATA'")
        return False    


    with open(settings_file,"r") as f:
        testing_params = json.load(f)
    semantic_search_query = testing_params["semantic_search_query"]
    search_filters = testing_params["search_filters"] 
    filterd_search_query = testing_params["filterd_search_query"] 
    semantic_search_expected_result = testing_params["expected_semantic_search_name"]
    filterd_search_expected_result = testing_params["expected_filtered_search_name"]
    host = os.getenv("QDRANT_HOST")
    port = os.getenv("QDRANT_PORT")
    
    if verbose:
        print(f"Searching {semantic_search_query} in {collection_name}")
        
    params = ConnectionParams(host=host, port=port)
    embedder = CustomEmbedder(os.getenv("EMBEDDING_MODEL_NAME"))
    embeddings = embedder.get_embeddings([semantic_search_query])[0]
    db_manager = VectorDBFactory.create_manager(
            db_type=VectorDBType.QDRANT,
            embedder=embedder
        )
    
    if db_manager.connect(params):
        if collection_name not in db_manager.list_collections():
            print(f'''Test collection was not found. Run "db_test.py" and "parser_test.py" to create and fill
                test collection and insert testing data. ''')
            return False
        res = db_manager.search(collection_name=collection_name, query_embedding=embeddings,limit=15)
        semantic_search_passed = check_results(res=res, expected=semantic_search_expected_result, verbose=verbose)
        
        print(f"Searching {filterd_search_query} with following filters:")
        for (f,v) in search_filters.items():
            print(f"{f} : {v}")
        res = db_manager.filtered_search(
            collection_name=collection_name,
            query=filterd_search_query,
            filters=search_filters,
            limit=3
        )
        filtered_search_passed = check_results(res=res, expected=filterd_search_expected_result, verbose=verbose)
    else:
        print("no connection")

    if verbose:
        if semantic_search_passed:
            print("Semantic search test has been PASSED!")
        else:
            print("Semantic search test has been FAILED!")
        if filtered_search_passed:
            print("Filtered search test has been PASSED!")
        else:
            print("Filtered search test has been FAILED!")  
            
    return semantic_search_passed and filtered_search_passed
              

            

if __name__ == "__main__":
    if search_test(storage="PROJECT_DATA", verbose=True):
        print("Search test has been PASSED")
    else:
        print("Search test has been FAILED")
    