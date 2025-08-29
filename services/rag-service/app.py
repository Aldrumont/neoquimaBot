from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from typing import List, Optional
import json
from datetime import datetime

from rag_service import RAGService
from models import DocumentUpload, SearchQuery, SearchResult

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Neoquima RAG Service",
    description="Serviço de RAG para processamento e busca de documentos",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instância do serviço RAG
rag_service = RAGService()

@app.on_event("startup")
async def startup_event():
    """Inicialização do serviço"""
    try:
        await rag_service.initialize()
        logger.info("RAG Service inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar RAG Service: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check do serviço"""
    try:
        qdrant_status = await rag_service.check_qdrant_health()
        return {
            "status": "healthy",
            "service": "rag-service",
            "qdrant_status": qdrant_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "rag-service",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/collections")
async def list_collections():
    """Lista todas as coleções disponíveis"""
    try:
        collections = await rag_service.list_collections()
        return {"collections": collections}
    except Exception as e:
        logger.error(f"Erro ao listar coleções: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/collections")
async def create_collection(collection_name: str = Form(...)):
    """Cria uma nova coleção"""
    try:
        await rag_service.create_collection(collection_name)
        return {"message": f"Coleção '{collection_name}' criada com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao criar coleção: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """Deleta uma coleção"""
    try:
        await rag_service.delete_collection(collection_name)
        return {"message": f"Coleção '{collection_name}' deletada com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao deletar coleção: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = Form("default"),
    metadata: Optional[str] = Form("{}")
):
    """Upload e vetorização de documento"""
    try:
        # Validar arquivo
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nome do arquivo é obrigatório")
        
        # Processar metadados
        try:
            metadata_dict = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Metadados inválidos")
        
        # Adicionar metadados padrão
        metadata_dict.update({
            "filename": file.filename,
            "upload_time": datetime.now().isoformat(),
            "file_size": file.size,
            "content_type": file.content_type
        })
        
        # Processar documento
        result = await rag_service.process_document(
            file=file,
            collection_name=collection_name,
            metadata=metadata_dict
        )
        
        return {
            "message": "Documento processado com sucesso",
            "document_id": result["document_id"],
            "collection": collection_name,
            "chunks": result["chunks"],
            "metadata": metadata_dict
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_documents(query: SearchQuery):
    """Busca semântica em documentos"""
    try:
        results = await rag_service.search_documents(
            query=query.query,
            collection_name=query.collection_name,
            limit=query.limit,
            threshold=query.threshold
        )
        
        return {
            "query": query.query,
            "collection": query.collection_name,
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections/{collection_name}/info")
async def get_collection_info(collection_name: str):
    """Informações sobre uma coleção específica"""
    try:
        info = await rag_service.get_collection_info(collection_name)
        return info
    except Exception as e:
        logger.error(f"Erro ao obter informações da coleção: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections/{collection_name}/documents")
async def list_documents(collection_name: str, limit: int = 100):
    """Lista documentos de uma coleção"""
    try:
        documents = await rag_service.list_documents(collection_name, limit)
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Erro ao listar documentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 