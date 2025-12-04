import sys 
import os
from dotenv import load_dotenv
from app.db_manager import VectorDBFactory, ConnectionParams, CustomEmbedder, VectorDBType

load_dotenv()
if len(sys.argv) >2:
    embedder = CustomEmbedder(os.getenv("EMBEDDING_MODEL_NAME"))
    embeddings = embedder.get_embeddings([sys.argv[2]])
    db_manager = VectorDBFactory.create_manager(
            db_type=VectorDBType.QDRANT,
            embedder=embedder
        )

    # Connect to database
    params = ConnectionParams(host=os.getenv("QDRANT_HOST"), port=os.getenv("QDRANT_PORT"))
    if db_manager.connect(params):
        res = db_manager.search(collection_name=sys.argv[1],query_embedding=embeddings[0])
        print(res)


        search_params = {
            # "level": {
            #     "must": True,
            #     "values": ["SENIOR", "MIDDLE"]
            # },
            "languages": {
                "must": True, 
                "values": ["german b1"]
            }
        }
        
        results = db_manager.filtered_search(
        collection_name=sys.argv[1],
        query="software engineer",
        filters=search_params,
        limit=3
    )
        for res in results:
            print(f"\n{res}\n")
    else:
        print("no connection")
    