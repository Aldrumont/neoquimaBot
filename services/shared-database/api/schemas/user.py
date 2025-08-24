from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import re
from .base import PaginatedResponse

class UserBase(BaseModel):
    """Schema base para usuários"""
    number: str = Field(..., pattern=r'^\+[1-9]\d{1,14}$', description="Número de telefone internacional")
    name: str = Field(..., min_length=2, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    note: Optional[str] = Field(None, max_length=500)
    role: str = Field(default="user", description="Papel: user, admin, moderator")
    active: bool = Field(default=True)
    expires_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)

    @validator('number')
    def validate_phone_number(cls, v):
        if not re.match(r'^\+[1-9]\d{1,14}$', v):
            raise ValueError('Número deve estar no formato internacional (+5511999998888)')
        return v

    @validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'admin', 'moderator']:
            raise ValueError('Role deve ser: user, admin ou moderator')
        return v

class UserCreate(UserBase):
    """Schema para criação de usuário"""
    pass

class UserUpdate(BaseModel):
    """Schema para atualização de usuário"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    note: Optional[str] = Field(None, max_length=500)
    role: Optional[str] = Field(None, description="Papel: user, admin, moderator")
    active: Optional[bool] = None
    expires_at: Optional[datetime] = None
    tags: Optional[List[str]] = None

    @validator('role')
    def validate_role(cls, v):
        if v is not None and v not in ['user', 'admin', 'moderator']:
            raise ValueError('Role deve ser: user, admin ou moderator')
        return v

class UserResponse(UserBase):
    """Schema para resposta de usuário"""
    id: int
    created_at: datetime
    last_interact: Optional[datetime] = None
    interact_count: int = Field(default=0)
    
    class Config:
        from_attributes = True

class UserList(PaginatedResponse):
    """Lista paginada de usuários"""
    users: List[UserResponse] 