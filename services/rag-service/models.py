from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentUpload(BaseModel):
    """Modelo para upload de documento"""
    collection_name: str = Field(default="default", description="Nome da coleção")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Metadados do documento")

class SearchQuery(BaseModel):
    """Modelo para consulta de busca"""
    query: str = Field(..., description="Texto da consulta")
    collection_name: str = Field(default="default", description="Nome da coleção")
    limit: int = Field(default=10, ge=1, le=100, description="Número máximo de resultados")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Threshold de similaridade")

class SearchResult(BaseModel):
    """Modelo para resultado de busca"""
    document_id: str = Field(..., description="ID do documento")
    chunk_id: str = Field(..., description="ID do chunk")
    content: str = Field(..., description="Conteúdo do chunk")
    metadata: Dict[str, Any] = Field(..., description="Metadados do documento")
    score: float = Field(..., description="Score de similaridade")
    chunk_index: int = Field(..., description="Índice do chunk no documento")

class DocumentInfo(BaseModel):
    """Modelo para informações do documento"""
    document_id: str = Field(..., description="ID do documento")
    filename: str = Field(..., description="Nome do arquivo")
    upload_time: datetime = Field(..., description="Data/hora do upload")
    file_size: int = Field(..., description="Tamanho do arquivo")
    content_type: str = Field(..., description="Tipo de conteúdo")
    chunks_count: int = Field(..., description="Número de chunks")
    metadata: Dict[str, Any] = Field(..., description="Metadados adicionais")

class CollectionInfo(BaseModel):
    """Modelo para informações da coleção"""
    name: str = Field(..., description="Nome da coleção")
    vectors_count: int = Field(..., description="Número de vetores")
    points_count: int = Field(..., description="Número de pontos")
    segments_count: int = Field(..., description="Número de segmentos")
    config: Dict[str, Any] = Field(..., description="Configuração da coleção")
    status: str = Field(..., description="Status da coleção")

class ProcessingResult(BaseModel):
    """Modelo para resultado do processamento"""
    document_id: str = Field(..., description="ID do documento")
    chunks: int = Field(..., description="Número de chunks criados")
    processing_time: float = Field(..., description="Tempo de processamento em segundos")
    status: str = Field(..., description="Status do processamento")
    error: Optional[str] = Field(None, description="Erro se houver") 