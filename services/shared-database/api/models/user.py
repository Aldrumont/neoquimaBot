from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON, Text
from sqlalchemy.sql import func
from .base import Base, TimestampMixin

class User(Base, TimestampMixin):
    """Modelo de usuário para o schema WhatsApp"""
    __tablename__ = "users"
    __table_args__ = {"schema": "whatsapp"}
    
    # Campos obrigatórios
    number = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    
    # Campos opcionais
    company = Column(String(100), nullable=True)
    note = Column(Text, nullable=True)
    role = Column(String(50), default="user")
    active = Column(Boolean, default=True)
    
    # Campos de expiração
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Campos de interação
    last_interact = Column(DateTime(timezone=True), nullable=True)
    interact_count = Column(Integer, default=0)
    
    # Campos de status
    status_reason = Column(Text, nullable=True)
    
    # Tags e metadados
    tags = Column(JSON, default=list)
    
    def __repr__(self):
        return f"<User(id={self.id}, number='{self.number}', name='{self.name}')>"
    
    def to_dict(self):
        """Converte o modelo para dicionário"""
        return {
            "id": self.id,
            "number": self.number,
            "name": self.name,
            "company": self.company,
            "note": self.note,
            "role": self.role,
            "active": self.active,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_interact": self.last_interact.isoformat() if self.last_interact else None,
            "interact_count": self.interact_count,
            "status_reason": self.status_reason,
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 