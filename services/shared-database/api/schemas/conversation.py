#!/usr/bin/env python3
"""
Schemas Pydantic para o sistema de contexto conversacional
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ========= SESSÕES =========

class SessionBase(BaseModel):
    session_key: str = Field(..., description="Chave única da sessão")
    whatsapp_number: str = Field(..., description="Número do WhatsApp (E.164)")
    session_id: str = Field(..., description="ID da sessão")
    config_id: Optional[int] = Field(None, description="ID da configuração aplicada")

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    is_active: Optional[bool] = None
    rolling_summary: Optional[str] = None
    current_turn_count: Optional[int] = None
    total_tokens_used: Optional[int] = None
    config_id: Optional[int] = None

class SessionResponse(SessionBase):
    id: int
    is_active: bool
    created_at: datetime
    last_activity: datetime
    rolling_summary: Optional[str] = None
    current_turn_count: int
    total_tokens_used: int
    
    class Config:
        from_attributes = True

# ========= TURNOS =========

class TurnBase(BaseModel):
    session_key: str = Field(..., description="Chave da sessão")
    turn_number: int = Field(..., description="Número do turno na sessão")
    role: str = Field(..., description="'user' ou 'assistant'")
    content: str = Field(..., description="Conteúdo da mensagem")
    correlation_id: Optional[str] = Field(None, description="ID de correlação")

class TurnCreate(TurnBase):
    tokens_used: Optional[int] = None
    rag_citations: Optional[List[Dict[str, Any]]] = None
    rag_collection: Optional[str] = None
    rag_query: Optional[str] = None
    latency_ms: Optional[int] = None

class TurnResponse(TurnBase):
    id: int
    tokens_used: Optional[int] = None
    rag_citations: Optional[List[Dict[str, Any]]] = None
    rag_collection: Optional[str] = None
    rag_query: Optional[str] = None
    correlation_id: Optional[str] = None
    latency_ms: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========= MEMÓRIAS =========

class MemoryBase(BaseModel):
    whatsapp_number: str = Field(..., description="Número do WhatsApp")
    memory_type: str = Field(..., description="Tipo de memória")
    memory_value: str = Field(..., description="Valor da memória")
    confidence: Optional[float] = Field(None, description="Confiança da extração (0-1)")

class MemoryCreate(MemoryBase):
    source_turn_id: Optional[int] = None
    opt_in_status: bool = True
    expires_at: Optional[datetime] = None

class MemoryResponse(MemoryBase):
    id: int
    source_turn_id: Optional[int] = None
    opt_in_status: bool
    created_at: datetime
    last_updated: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ========= AUDITORIA =========

class AuditBase(BaseModel):
    session_key: str = Field(..., description="Chave da sessão")
    correlation_id: str = Field(..., description="ID de correlação")
    action: str = Field(..., description="Ação realizada")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes da ação")

class AuditCreate(AuditBase):
    total_tokens: Optional[int] = None
    rag_score_average: Optional[float] = None
    latency_ms: Optional[int] = None

class AuditResponse(AuditBase):
    id: int
    total_tokens: Optional[int] = None
    rag_score_average: Optional[float] = None
    latency_ms: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========= CONTEXTO COMPLETO =========

class ConversationContext(BaseModel):
    session: SessionResponse
    recent_turns: List[TurnResponse]
    user_memories: List[MemoryResponse]
    rolling_summary: Optional[str] = None 