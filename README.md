## 🚀 Setup & Installation

This project uses **Docker Compose** for orchestration and **uv** for Python package management.

### 1. Prerequisites
Ensure you have the following installed on your host machine:
* **Docker & Docker Compose**
* **uv** (Fast Python package manager) — [Installation Guide](https://docs.astral-sh/uv/getting-started/installation/)

### 2. Environment Configuration
Create a `.env` file in the root directory. This file is used by Docker Compose to configure the containers.

```bash
# General
LOG_LEVEL=INFO

# Qdrant Configuration
QDRANT_HOST=qdrant
QDRANT_PORT=6333
VECTOR_DB=qdrant

# Model Settings
EMBEDDING_MODEL_NAME=embedding/models/all-MiniLM-L12-v2

# Collection Names
TEST_PERSONAL_DATA_COLLECTION_NAME=retriever_test_collection
TEST_PROJECT_DATA_COLLECTION_NAME=retriever_test_collection_projects

# Test Paths
CHUNKING_TEST_SETTINGS=app/tests/chunking_test_settings.json
PERSONAL_DATA_TEST_SETTINGS=app/tests/personal_data_search_settings.json
PROJECT_DATA_TEST_SETTINGS=app/tests/project_data_search_settings.json
```

### 3. Local Development Setup
If you want to run the application locally (outside of Docker) for faster UI development while keeping Qdrant in a container:

```bash
# 1. Install dependencies and create virtual environment
uv sync

# 2. Start only the Qdrant database
docker compose up -d qdrant

# 3. Run the application
uv run python app/main.py
```

### 4. Full Docker Deployment
To run the entire stack (Database + API + UI) inside Docker:

```bash
# Build and start the containers
docker compose up -d --build --remove-orphans

# Watch the logs for the retriever service
docker compose logs -f rag-retriever
```

### 5. Accessing the System
Once the containers are healthy, you can access the following interfaces:
Run all tests (or DB test and parsing test) to init test database before using.
* **Web Interface (NiceGUI):** [http://localhost:8000](http://localhost:8000)
* **API Documentation (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Qdrant Dashboard:** [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

---

### 🛠️ Development Workflow
To automatically sync code changes to the running Docker container without rebuilding:
```bash
docker compose up --watch
```

