from chunker import SimpleChunker
from inno_parser import InnoStandardPraser
from chunker import PersonalInfo
from db_manager import ChromaHttpDBManager

parser = InnoStandardPraser()
chunker = SimpleChunker(chunk_size=300,overlap=30)
parser.parse_inniwise_std(file_path="cv_lev.docx")
gd = parser.get_personal_data()
pd = parser.get_projects_data()


for project in pd:
    print(f"name: {project['roles']}\n")

test = PersonalInfo(gd)
print(test)
db_manager = ChromaHttpDBManager()
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
db_manager.connect(connection_params)
if db_manager.connect(connection_params):
    print("Successfully connected to ChromaDB HTTP server")
    print(f"Server version: {db_manager.get_server_version()}")
    print(db_manager.get_collection_info("cv_personal_data"))
    db_manager.disconnect()