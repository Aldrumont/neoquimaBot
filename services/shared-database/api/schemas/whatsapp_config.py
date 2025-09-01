from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class WhatsAppConfigBase(BaseModel):
    """Schema base para configuração do WhatsApp"""
    access_token: str = Field(..., description="Token de acesso do WhatsApp Business API")
    phone_number_id: str = Field(..., description="ID do número de telefone")
    business_account_id: str = Field(..., description="ID da conta empresarial")
    verify_token: str = Field(..., description="Token para verificação do webhook")
    webhook_url: Optional[str] = Field(None, description="URL do webhook configurada")

class WhatsAppConfigCreate(WhatsAppConfigBase):
    """Schema para criação de configuração do WhatsApp"""
    pass

class WhatsAppConfigUpdate(WhatsAppConfigBase):
    """Schema para atualização de configuração do WhatsApp"""
    access_token: Optional[str] = Field(None, description="Token de acesso do WhatsApp Business API")
    phone_number_id: Optional[str] = Field(None, description="ID do número de telefone")
    business_account_id: Optional[str] = Field(None, description="ID da conta empresarial")
    verify_token: Optional[str] = Field(None, description="Token para verificação do webhook")
    webhook_url: Optional[str] = Field(None, description="URL do webhook configurada")

class WhatsAppConfigResponse(WhatsAppConfigBase):
    """Schema para resposta de configuração do WhatsApp"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: str
    
    class Config:
        from_attributes = True 