from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .user import UserResponse

class LoginRequest(BaseModel):
    """Request para login"""
    username: str = Field(..., description="Nome de usuário ou email")
    password: str = Field(..., description="Senha do usuário")

class LoginResponse(BaseModel):
    """Resposta do login"""
    access_token: str = Field(..., description="Token JWT para autenticação")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(..., description="Tempo de expiração em segundos")
    user: UserResponse 