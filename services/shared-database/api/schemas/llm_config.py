from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class LLMConfigBase(BaseModel):
    """Schema base para configurações do LLM"""
    provider: str = Field(default="ollama", description="Provedor do LLM")
    model: str = Field(default="llama2:3b", description="Nome do modelo")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperatura da geração (0.0-2.0)")
    max_tokens: int = Field(default=1000, ge=100, le=4000, description="Máximo de tokens")
    context_window: int = Field(default=4096, ge=1024, le=8192, description="Janela de contexto")
    rag_enabled: bool = Field(default=True, description="Se o RAG está habilitado")
    default_rag_collection: Optional[str] = Field(default=None, description="Coleção RAG padrão")
    system_prompt: Optional[str] = Field(default=None, description="Prompt do sistema")

class LLMConfigCreate(LLMConfigBase):
    """Schema para criar configuração do LLM"""
    api_key: Optional[str] = Field(default=None, description="Chave da API (opcional)")
    base_url: Optional[str] = Field(default=None, description="URL base da API")
    created_by: Optional[str] = Field(default=None, description="Usuário que criou")
    additional_config: Optional[Dict[str, Any]] = Field(default=None, description="Configurações adicionais")

class LLMConfigUpdate(LLMConfigBase):
    """Schema para atualizar configuração do LLM"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    additional_config: Optional[Dict[str, Any]] = None

class LLMConfigResponse(LLMConfigBase):
    """Schema para resposta de configuração do LLM"""
    id: Optional[int] = None
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    additional_config: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class LLMConfigList(BaseModel):
    """Schema para lista de configurações"""
    configs: list[LLMConfigResponse]
    total: int
    active_id: Optional[int] = None 