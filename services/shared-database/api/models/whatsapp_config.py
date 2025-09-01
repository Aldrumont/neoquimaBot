from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from .base import Base

class WhatsAppConfig(Base):
    """Modelo para configuração do WhatsApp Business API"""
    
    __tablename__ = "whatsapp_config"
    __table_args__ = {"schema": "public"}
    
    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(Text, nullable=False, comment="Token de acesso do WhatsApp Business API")
    phone_number_id = Column(String(50), nullable=False, comment="ID do número de telefone")
    business_account_id = Column(String(50), nullable=False, comment="ID da conta empresarial")
    verify_token = Column(String(100), nullable=False, comment="Token para verificação do webhook")
    webhook_url = Column(Text, nullable=True, comment="URL do webhook configurada")
    is_active = Column(Boolean, default=True, comment="Se a configuração está ativa")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Data de atualização")
    created_by = Column(String(100), default="admin", comment="Quem criou a configuração")
    
    def __repr__(self):
        return f"<WhatsAppConfig(id={self.id}, phone_number_id='{self.phone_number_id}', is_active={self.is_active})>" 