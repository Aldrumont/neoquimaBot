from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func
from .base import Base

class LLMConfig(Base):
    """Modelo para configurações do LLM"""
    __tablename__ = "llm_configs"
    __table_args__ = {"schema": "llm"}

    id = Column(Integer, primary_key=True, index=True)
    
    # Configurações básicas
    provider = Column(String(50), nullable=False, default="openai")
    model = Column(String(100), nullable=False, default="gpt-3.5-turbo")
    api_key = Column(Text, nullable=True)  # Criptografado em produção
    
    # URLs e endpoints
    base_url = Column(String(500), nullable=True)
    
    # Parâmetros de geração
    temperature = Column(Integer, nullable=False, default=70)  # 0-200 (0.0-2.0)
    max_tokens = Column(Integer, nullable=False, default=1000)
    context_window = Column(Integer, nullable=False, default=8000)
    
    # Configurações RAG
    rag_enabled = Column(Boolean, nullable=False, default=True)
    default_rag_collection = Column(String(100), nullable=True)
    
    # Prompt do sistema
    system_prompt = Column(Text, nullable=True)
    
    # Metadados
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Configurações adicionais (flexível)
    additional_config = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<LLMConfig(id={self.id}, provider='{self.provider}', model='{self.model}')>"
    
    def to_dict(self):
        """Converte o modelo para dicionário"""
        return {
            "id": self.id,
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature / 100.0 if self.temperature is not None else 0.7,  # Converte para float
            "max_tokens": self.max_tokens,
            "context_window": self.context_window,
            "rag_enabled": self.rag_enabled,
            "default_rag_collection": self.default_rag_collection,
            "system_prompt": self.system_prompt,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "additional_config": self.additional_config
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Cria instância a partir de dicionário"""
        # Converte temperatura de float para int (0-200)
        if "temperature" in data and isinstance(data["temperature"], float):
            data["temperature"] = int(data["temperature"] * 100)
        
        return cls(**data) 