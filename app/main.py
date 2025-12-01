from fastapi import FastAPI, HTTPException
import chromadb
import os

app = FastAPI(title="RAG Retriever MVP")

# Глобальные клиенты
chroma_client = None
collections = {}

@app.on_event("startup")
async def startup_event():
    """Инициализация клиентов при запуске"""
    global chroma_client, collections
    
    try:
        # Инициализация ChromaDB клиента
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = os.getenv("CHROMA_PORT", "8000")
        
        chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        
        # Получаем или создаем коллекции
        collections = {
            "resume_skills": chroma_client.get_or_create_collection("resume_skills"),
            "resume_experience": chroma_client.get_or_create_collection("resume_experience"),
            "resume_facts": chroma_client.get_or_create_collection("resume_facts")
        }
        
        print("✅ ChromaDB client and collections initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize ChromaDB: {e}")
        raise

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "RAG Retriever MVP",
        "chroma_connected": chroma_client is not None
    }

@app.get("/chroma_check")
async def chroma_check():
    """Проверка соединения и доступности коллекций ChromaDB"""
    if chroma_client is None:
        raise HTTPException(status_code=503, detail="ChromaDB client not initialized")
    
    try:
        chroma_client.heartbeat()
        
        collection_status = {}
        for name, collection in collections.items():
            try:
                collection.count()
                collection_status[name] = {
                    "status": "available",
                    "count": collection.count()
                }
            except Exception as e:
                collection_status[name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "status": "success",
            "chroma_connection": "healthy",
            "collections": collection_status
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"ChromaDB connection failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)