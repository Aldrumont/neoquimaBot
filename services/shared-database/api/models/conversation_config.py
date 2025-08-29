from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from .base import Base


class ConversationConfig(Base):
    __tablename__ = "conversation_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, comment="Nome da configuração")
    description = Column(Text, comment="Descrição da configuração")
    
    # Limites de tokens
    max_total_tokens = Column(Integer, default=1500, comment="Total máximo de tokens")
    summary_tokens = Column(Integer, default=200, comment="Tokens para resumo")
    conversation_window_tokens = Column(Integer, default=800, comment="Tokens para janela de conversa")
    rag_context_tokens = Column(Integer, default=500, comment="Tokens para contexto RAG")
    
    # Configurações de sessão
    session_ttl_minutes = Column(Integer, default=30, comment="TTL da sessão em minutos")
    max_conversation_turns = Column(Integer, default=6, comment="Máximo de turnos na janela")
    
    # Configurações de privacidade
    enable_user_memories = Column(Boolean, default=True, comment="Habilitar memórias do usuário")
    memory_retention_days = Column(Integer, default=90, comment="Dias para reter memórias")
    require_opt_in = Column(Boolean, default=True, comment="Requer opt-in para memórias")
    
    # Configurações de auditoria
    enable_audit_log = Column(Boolean, default=True, comment="Habilitar log de auditoria")
    log_citations = Column(Boolean, default=True, comment="Logar citações RAG")
    log_latency = Column(Boolean, default=True, comment="Logar latência")
    
    # Configurações de fallback
    enable_fallback = Column(Boolean, default=True, comment="Habilitar fallback automático")
    fallback_strategy = Column(String(50), default="truncate_oldest", comment="Estratégia de fallback")
    
    # Status
    is_active = Column(Boolean, default=True, comment="Configuração ativa")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "max_total_tokens": self.max_total_tokens,
            "summary_tokens": self.summary_tokens,
            "conversation_window_tokens": self.conversation_window_tokens,
            "rag_context_tokens": self.rag_context_tokens,
            "session_ttl_minutes": self.session_ttl_minutes,
            "max_conversation_turns": self.max_conversation_turns,
            "enable_user_memories": self.enable_user_memories,
            "memory_retention_days": self.memory_retention_days,
            "require_opt_in": self.require_opt_in,
            "enable_audit_log": self.enable_audit_log,
            "log_citations": self.log_citations,
            "log_latency": self.log_latency,
            "enable_fallback": self.enable_fallback,
            "fallback_strategy": self.fallback_strategy,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 