from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    number: str
    name: Optional[str] = None
    company: Optional[str] = None
    note: Optional[str] = None
    expires_at: Optional[datetime] = None
    active: bool = True
    role: str = "user"
    status_reason: Optional[str] = None
    tags: List[str] = []

class UserCreate(UserBase):
    added_by: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    note: Optional[str] = None
    expires_at: Optional[datetime] = None
    active: Optional[bool] = None
    role: Optional[str] = None
    status_reason: Optional[str] = None
    tags: Optional[List[str]] = None

class UserResponse(UserBase):
    id: int
    added_by: Optional[str]
    created_at: datetime
    last_interact: Optional[datetime]
    interact_count: int
    
    model_config = {
        "from_attributes": True
    }

class UserList(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int

# ========= Contratos de API =========

class WhatsAppMessage(BaseModel):
    """Contrato para mensagem recebida do WhatsApp"""
    from_number: str
    message_body: str
    timestamp: datetime
    message_id: Optional[str] = None

class WhatsAppResponse(BaseModel):
    """Contrato para resposta enviada ao WhatsApp"""
    to_number: str
    message_body: str
    message_type: str = "text"
    success: bool
    error_message: Optional[str] = None

class WebhookRequest(BaseModel):
    """Contrato para payload do webhook do WhatsApp"""
    entry: List[dict]

class WebhookResponse(BaseModel):
    """Contrato para resposta do webhook"""
    status: str  # "accepted", "blocked", "test_mode"
    user_id: Optional[int] = None
    reason: Optional[str] = None
    message_sent: bool = False
    test_info: Optional[dict] = None

class LLMRequest(BaseModel):
    """Contrato para envio de mensagem para módulo LLM"""
    user_id: int
    user_number: str
    message: str
    context: Optional[dict] = None

class LLMResponse(BaseModel):
    """Contrato para resposta do módulo LLM"""
    response_text: str
    confidence: Optional[float] = None
    processing_time: Optional[float] = None 