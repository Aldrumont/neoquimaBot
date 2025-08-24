from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .base import PaginatedResponse

class ApiInfo(BaseModel):
    """Informações da API"""
    message: str
    version: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthCheck(BaseModel):
    """Status de saúde da API"""
    status: str = Field(..., description="Status: healthy, unhealthy, degraded")
    service: str
    database: str = Field(..., description="Status do banco: connected, disconnected, error")
    timestamp: datetime = Field(default_factory=datetime.now)
    uptime: Optional[float] = Field(None, description="Tempo de funcionamento em segundos")

class SchemaInfo(BaseModel):
    """Informações de um schema"""
    name: str
    description: str
    tables: List[str]
    record_count: Optional[int] = None

class SchemaList(BaseModel):
    """Lista de schemas disponíveis"""
    schemas: List[SchemaInfo] 