import os
import logging
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, 
    CreateCollection
)
import requests
import PyPDF2
from docx import Document
import pandas as pd
import io

logger = logging.getLogger(__name__)

class RAGService:
    """Serviço principal para RAG (Retrieval-Augmented Generation)"""
    
    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        
        self.client: Optional[QdrantClient] = None
        
    async def initialize(self):
        """Inicializa o serviço RAG"""
        try:
            # Conectar ao Qdrant
            self.client = QdrantClient(self.qdrant_url)
            logger.info(f"Conectado ao Qdrant em {self.qdrant_url}")
            
            # Verificar se o modelo Ollama está disponível
            await self._ensure_ollama_model()
            logger.info(f"Modelo de embeddings Ollama configurado: {self.embedding_model_name}")
            
            # Criar coleção padrão se não existir
            await self._ensure_default_collection()
            
        except Exception as e:
            logger.error(f"Erro ao inicializar RAG Service: {e}")
            raise
    
    async def _ensure_ollama_model(self):
        """Garante que o modelo Ollama está disponível"""
        try:
            # Verificar se o modelo existe
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                if self.embedding_model_name not in model_names:
                    logger.info(f"Baixando modelo Ollama: {self.embedding_model_name}")
                    # Baixar o modelo
                    pull_response = requests.post(
                        f"{self.ollama_url}/api/pull",
                        json={"name": self.embedding_model_name}
                    )
                    if pull_response.status_code != 200:
                        raise Exception(f"Erro ao baixar modelo: {pull_response.text}")
                    logger.info(f"Modelo {self.embedding_model_name} baixado com sucesso")
                else:
                    logger.info(f"Modelo {self.embedding_model_name} já está disponível")
            else:
                raise Exception(f"Erro ao verificar modelos Ollama: {response.text}")
                
        except Exception as e:
            logger.error(f"Erro ao verificar modelo Ollama: {e}")
            raise
    
    async def _ensure_default_collection(self):
        """Garante que a coleção padrão existe"""
        try:
            collections = await self.list_collections()
            if "default" not in [col["name"] for col in collections]:
                await self.create_collection("default")
                logger.info("Coleção padrão criada")
        except Exception as e:
            logger.warning(f"Não foi possível criar coleção padrão: {e}")
    
    async def check_qdrant_health(self) -> str:
        """Verifica a saúde do Qdrant"""
        try:
            collections = await self.list_collections()
            return "connected"
        except Exception as e:
            logger.error(f"Erro ao conectar com Qdrant: {e}")
            return "disconnected"
    
    async def list_collections(self) -> List[Dict[str, Any]]:
        """Lista todas as coleções"""
        try:
            collections = self.client.get_collections()
            result = []
            
            for collection in collections.collections:
                info = await self.get_collection_info(collection.name)
                result.append(info)
            
            return result
        except Exception as e:
            logger.error(f"Erro ao listar coleções: {e}")
            raise
    
    async def create_collection(self, collection_name: str):
        """Cria uma nova coleção"""
        try:
            # nomic-embed-text tem dimensão fixa de 768
            vector_size = 768
            
            # Criar coleção
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"Coleção '{collection_name}' criada com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao criar coleção '{collection_name}': {e}")
            raise
    
    async def delete_collection(self, collection_name: str):
        """Deleta uma coleção"""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Coleção '{collection_name}' deletada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao deletar coleção '{collection_name}': {e}")
            raise
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Obtém informações sobre uma coleção"""
        try:
            info = self.client.get_collection(collection_name)
            
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "config": {
                    "vector_size": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance
                },
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Erro ao obter informações da coleção '{collection_name}': {e}")
            raise
    
    async def process_document(self, file, collection_name: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Processa um documento: extrai texto, divide em chunks e vetoriza"""
        start_time = time.time()
        
        try:
            # Extrair texto do arquivo
            text = await self._extract_text(file)
            
            # Dividir em chunks
            chunks = self._split_text(text)
            
            # Gerar embeddings e salvar no Qdrant
            document_id = str(uuid.uuid4())
            points = []
            
            for i, chunk in enumerate(chunks):
                # Gerar embedding via Ollama
                embedding = await self._generate_embedding(chunk)
                
                # Criar ponto
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "document_id": document_id,
                        "chunk_index": i,
                        "content": chunk,
                        "metadata": metadata,
                        "chunk_id": str(uuid.uuid4())
                    }
                )
                points.append(point)
            
            # Salvar no Qdrant
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            processing_time = time.time() - start_time
            
            logger.info(f"Documento processado: {len(chunks)} chunks em {processing_time:.2f}s")
            
            return {
                "document_id": document_id,
                "chunks": len(chunks),
                "processing_time": processing_time,
                "status": "success"
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Erro ao processar documento: {e}")
            
            return {
                "document_id": str(uuid.uuid4()),
                "chunks": 0,
                "processing_time": processing_time,
                "status": "error",
                "error": str(e)
            }
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Gera embedding via Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.embedding_model_name,
                    "prompt": text
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["embedding"]
            else:
                raise Exception(f"Erro ao gerar embedding: {response.text}")
                
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            raise
    
    async def _extract_text(self, file) -> str:
        """Extrai texto de diferentes tipos de arquivo"""
        try:
            content = await file.read()
            
            if file.content_type == "application/pdf":
                return self._extract_pdf_text(content)
            elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return self._extract_docx_text(content)
            elif file.content_type in ["text/plain", "text/csv"]:
                return content.decode("utf-8")
            elif file.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                return self._extract_excel_text(content)
            else:
                # Tentar como texto
                try:
                    return content.decode("utf-8")
                except:
                    raise ValueError(f"Tipo de arquivo não suportado: {file.content_type}")
                    
        except Exception as e:
            logger.error(f"Erro ao extrair texto: {e}")
            raise
    
    def _extract_pdf_text(self, content: bytes) -> str:
        """Extrai texto de PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF: {e}")
            raise
    
    def _extract_docx_text(self, content: bytes) -> str:
        """Extrai texto de DOCX"""
        try:
            doc = Document(io.BytesIO(content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto do DOCX: {e}")
            raise
    
    def _extract_excel_text(self, content: bytes) -> str:
        """Extrai texto de Excel"""
        try:
            df = pd.read_excel(io.BytesIO(content))
            return df.to_string()
        except Exception as e:
            logger.error(f"Erro ao extrair texto do Excel: {e}")
            raise
    
    def _split_text(self, text: str) -> List[str]:
        """Divide o texto em chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Se não é o último chunk, tenta quebrar em uma palavra
            if end < len(text):
                # Procurar por quebra de linha ou espaço próximo ao final
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in ['\n', ' ', '.', '!', '?']:
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    async def search_documents(self, query: str, collection_name: str = "default", 
                             limit: int = 10, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Busca semântica em documentos"""
        try:
            # Gerar embedding da query via Ollama
            query_embedding = await self._generate_embedding(query)
            
            # Buscar no Qdrant
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=threshold
            )
            
            # Formatar resultados
            results = []
            for point in search_result:
                results.append({
                    "document_id": point.payload["document_id"],
                    "chunk_id": point.payload["chunk_id"],
                    "content": point.payload["content"],
                    "metadata": point.payload["metadata"],
                    "score": point.score,
                    "chunk_index": point.payload["chunk_index"]
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            raise
    
    async def list_documents(self, collection_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Lista documentos de uma coleção"""
        try:
            # Buscar todos os pontos
            points = self.client.scroll(
                collection_name=collection_name,
                limit=limit,
                with_payload=True
            )[0]
            
            # Agrupar por documento
            documents = {}
            for point in points:
                doc_id = point.payload["document_id"]
                if doc_id not in documents:
                    documents[doc_id] = {
                        "document_id": doc_id,
                        "filename": point.payload["metadata"].get("filename", "Unknown"),
                        "upload_time": point.payload["metadata"].get("upload_time", ""),
                        "file_size": point.payload["metadata"].get("file_size", 0),
                        "content_type": point.payload["metadata"].get("content_type", ""),
                        "chunks_count": 0,
                        "metadata": point.payload["metadata"]
                    }
                documents[doc_id]["chunks_count"] += 1
            
            return list(documents.values())
            
        except Exception as e:
            logger.error(f"Erro ao listar documentos: {e}")
            raise 