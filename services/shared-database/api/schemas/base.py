from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class ErrorResponse(BaseModel):
    """Resposta padrão para erros"""
    error: str
    code: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class PaginationParams(BaseModel):
    """Parâmetros de paginação"""
    skip: int = Field(default=0, ge=0, description="Registros para pular")
    limit: int = Field(default=100, ge=1, le=1000, description="Limite de registros")

class PaginatedResponse(BaseModel):
    """Resposta paginada padrão"""
    total: int
    skip: int
    limit: int
    has_more: bool 