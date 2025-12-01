from chunker import SimpleChunker
from inno_parser import InnoStandardPraser
from chunker import PersonalInfo
from db_manager import ChromaHttpDBManager

parser = InnoStandardPraser()
chunker = SimpleChunker(chunk_size=300,overlap=30)
parser.parse_inniwise_std(file_path="cv_lev.docx")
parser.parse_inniwise_std(file_path="cv_K.docx")
parser.parse_inniwise_std(file_path="cv.docx")
parser.parse_inniwise_std(file_path="cv_ivan.docx")
gd = parser.get_personal_data()
#pd = parser.get_projects_data()
print (f'meta:{gd["metadata"]}\ntext:{gd["text"]}')
print (f"\n\n\n{parser.get_metadatas}")
ids = []
for i in range(len(parser.get_metadatas)):
    ids.append(f"{i}")
print (f"ids:{ids}")
db_manager = ChromaHttpDBManager()
connection_params = {
    'mode': 'http',
    'host': 'localhost',  
    'port': 8000,
    'ssl': False,
    'headers': {
        'X-Client-Name': 'CVSearchApp',
        # 'Authorization': 'Bearer your-token'  # if auth enabled
    }
}

# db_manager.connect(connection_params)
# db_manager.set_embedder("embedding/models/all-MiniLM-L12-v2")
# if db_manager.connect(connection_params):
#     print("Successfully connected to ChromaDB HTTP server")
#     print(f"Server version: {db_manager.get_server_version()}")
#     print(db_manager.get_collection_info("cv_personal_data"))
#     db_manager.list_collections()
#     db_manager.insert_documents("cv_personal_data",metadatas=parser.get_metadatas, documents=parser.get_texts,ids=ids)
#     db_manager.disconnect()