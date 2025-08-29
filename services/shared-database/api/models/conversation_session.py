from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float
from sqlalchemy.sql import func
from .base import Base


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_key = Column(String(100), unique=True, nullable=False, comment="Chave única da sessão")
    whatsapp_number = Column(String(20), nullable=False, comment="Número do WhatsApp (E.164)")
    session_id = Column(String(50), nullable=False, comment="ID da sessão")
    
    # Estado da sessão
    is_active = Column(Boolean, default=True, comment="Sessão ativa")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Contexto da conversa
    rolling_summary = Column(Text, comment="Resumo acumulado da sessão")
    current_turn_count = Column(Integer, default=0, comment="Número atual de turnos")
    total_tokens_used = Column(Integer, default=0, comment="Total de tokens usados")
    
    # Configurações aplicadas
    config_id = Column(Integer, comment="ID da configuração aplicada")
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_key": self.session_key,
            "whatsapp_number": self.whatsapp_number,
            "session_id": self.session_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "rolling_summary": self.rolling_summary,
            "current_turn_count": self.current_turn_count,
            "total_tokens_used": self.total_tokens_used,
            "config_id": self.config_id
        }


class ConversationTurn(Base):
    __tablename__ = "conversation_turns"
    
    id = Column(Integer, primary_key=True, index=True)
    session_key = Column(String(100), nullable=False, comment="Chave da sessão")
    turn_number = Column(Integer, nullable=False, comment="Número do turno na sessão")
    
    # Conteúdo do turno
    role = Column(String(10), nullable=False, comment="'user' ou 'assistant'")
    content = Column(Text, nullable=False, comment="Conteúdo da mensagem")
    tokens_used = Column(Integer, comment="Tokens utilizados")
    
    # Contexto RAG
    rag_citations = Column(JSON, comment="Citações do RAG (document_id, chunk_id, score)")
    rag_collection = Column(String(100), comment="Coleção RAG utilizada")
    rag_query = Column(Text, comment="Query RAG original")
    
    # Auditoria
    correlation_id = Column(String(100), comment="ID de correlação para rastreamento")
    latency_ms = Column(Integer, comment="Latência em milissegundos")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_key": self.session_key,
            "turn_number": self.turn_number,
            "role": self.role,
            "content": self.content,
            "tokens_used": self.tokens_used,
            "rag_citations": self.rag_citations,
            "rag_collection": self.rag_collection,
            "rag_query": self.rag_query,
            "correlation_id": self.correlation_id,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class UserMemory(Base):
    __tablename__ = "user_memories"
    
    id = Column(Integer, primary_key=True, index=True)
    whatsapp_number = Column(String(20), nullable=False, comment="Número do WhatsApp")
    memory_type = Column(String(50), nullable=False, comment="Tipo de memória")
    memory_value = Column(Text, nullable=False, comment="Valor da memória")
    
    # Metadados
    confidence = Column(Float, comment="Confiança da extração (0-1)")
    source_turn_id = Column(Integer, comment="ID do turno que originou a memória")
    opt_in_status = Column(Boolean, default=False, comment="Usuário deu opt-in")
    
    # Controle de tempo
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), comment="Data de expiração")
    
    def to_dict(self):
        return {
            "id": self.id,
            "whatsapp_number": self.whatsapp_number,
            "memory_type": self.memory_type,
            "memory_value": self.memory_value,
            "confidence": self.confidence,
            "source_turn_id": self.source_turn_id,
            "opt_in_status": self.opt_in_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


class ConversationAuditLog(Base):
    __tablename__ = "conversation_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_key = Column(String(100), nullable=False, comment="Chave da sessão")
    correlation_id = Column(String(100), nullable=False, comment="ID de correlação")
    
    # Dados da auditoria
    action = Column(String(50), nullable=False, comment="Ação realizada")
    details = Column(JSON, comment="Detalhes da ação")
    
    # Métricas
    total_tokens = Column(Integer, comment="Total de tokens utilizados")
    rag_score_average = Column(Float, comment="Score médio do RAG")
    latency_ms = Column(Integer, comment="Latência total em ms")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_key": self.session_key,
            "correlation_id": self.correlation_id,
            "action": self.action,
            "details": self.details,
            "total_tokens": self.total_tokens,
            "rag_score_average": self.rag_score_average,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        } 