"""
Testing of parsing CVs, chunking text, and upserting data in vector database.
"""
from typing import Any
import os
import json
from dotenv import load_dotenv
from app.parsers import CVCollection
from app.chunker.chunker import SimpleChunker
from app.chunker.chunker import Chunk
from app.vector_db  import VectorDBFactory, ConnectionParams, CustomEmbedder

load_dotenv()
settings_file = os.getenv("CHUNKING_TEST_SETTINGS")
with open(settings_file,"r") as f:
    testing_params = json.load(f)
    
def parsing_test(verbose = False):

    passed = False
    host = os.getenv("QDRANT_HOST")
    port = os.getenv("QDRANT_PORT")
    params = ConnectionParams(host=host, port=port)
    embedding_model = os.getenv("EMBEDDING_MODEL_NAME")
    cv_collection_name = os.getenv("TEST_PERSONAL_DATA_COLLECTION_NAME")
    project_collection_name = os.getenv("TEST_PROJECT_DATA_COLLECTION_NAME")
    chunking_method = testing_params["chunking_method"]
    collection = CVCollection(chunk_size=testing_params["chunk_size"], chunk_overlap=testing_params["chunk_overlap"])
    embedder = CustomEmbedder(embedding_model)
    db_manager = VectorDBFactory.create_manager(
            db_type="qdrant",
            embedder=embedder
    )
    collection_metadata = {
        "about":"test cv collection"
    }
    try:
        # Add CVs from files
        #Checking files
        data_path = os.path.dirname(__file__) + "/" + testing_params["test_data_folder"]
        cv_files = [data_path + file for file in testing_params["cv_s"]]
        if verbose:
            print(f"Looking for {''.join(cv_files)} files in {data_path}")
            
        successful_parses = 0
        for cv_file in cv_files:
            # Check if file exists in current directory
            if not os.path.exists(cv_file):
                print(f"  ✗ {cv_file}: File not found")
                continue
            try:
                if verbose:
                    print(f"Reading {cv_file} ...")
                cv_id = collection.add_cv_from_file(cv_file) 
                cv_name = collection.cvs[-1].personal_info.candidate_name
                if verbose:
                    print(f"{cv_file} has been read successfully\nCandidat's name: {cv_name} with id: {cv_id}.")
                if cv_name in testing_params["expected_names_from_cv_s"]:
                    successful_parses += 1
            except Exception as e:
                print(f"File {cv_file} couldn't be read: Error - {e}")
        if successful_parses == 0:
            print("\nNo CVs were successfully parsed. Exiting.")
            return
        if successful_parses == len( testing_params["cv_s"]):
            if verbose:
                print("All files has been read and parsed.")
            passed = True
        if verbose:
            print(f"Chunking ...")
        passed = collection.generate_chunks(chunking_method)
        if passed:
            print(f"Chunks has been generated with chunking size {chunking_method}")
            if verbose:
                print(f"Personal data chunks: {len(collection.cv_chunks)}\nProject data chunks: {len(collection.project_chunks)}")
        vector_db_data_cv, vector_db_data_pr = collection.prepare_chunks_qdrant()
        
        if db_manager.connect(params):
            if not db_manager.check_collection(cv_collection_name):
                db_manager.create_collection(cv_collection_name, collection_metadata)
            cv_inserted = db_manager.insert_documents(
                collection_name=cv_collection_name,
                documents=vector_db_data_cv["texts"],
                metadatas=vector_db_data_cv["metadatas"],
                ids=vector_db_data_cv["ids"]
            )
            if not db_manager.check_collection(project_collection_name):
                db_manager.create_collection(project_collection_name, collection_metadata)
            pr_inserted = db_manager.insert_documents(
                collection_name=project_collection_name,
                documents=vector_db_data_pr["texts"],
                metadatas=vector_db_data_pr["metadatas"],
                ids=vector_db_data_pr["ids"]
            )
        if cv_inserted:
            print(f"Personal datat chunks has been inserted")
        if pr_inserted:
            print(f"Project data chunks has been inserted")
            


    except Exception as e:
        print(f"\nError during testting: {e}")
    return passed
if __name__ == "__main__":

    if (parsing_test(True)):
        print("Chunking test has been PASSED!")
    else:
        print("Chunking test has been FAILED!")