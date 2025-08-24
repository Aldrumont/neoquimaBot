from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import time
from ..core.database import get_db
from ..schemas.system import ApiInfo, HealthCheck, SchemaInfo, SchemaList
from ..models.user import User

router = APIRouter(prefix="/api/v1", tags=["System"])

# Variável global para tracking de uptime
start_time = time.time()

@router.get("/", response_model=ApiInfo)
async def get_api_info():
    """Informações da API"""
    return ApiInfo(
        message="Neoquima Shared Database API",
        version="1.0.0",
        status="running"
    )

@router.get("/health", response_model=HealthCheck)
async def health_check(db: Session = Depends(get_db)):
    """Verifica o status de saúde da API e banco"""
    try:
        # Testar conexão com banco
        db.execute("SELECT 1")
        db_status = "connected"
        api_status = "healthy"
    except Exception as e:
        db_status = "error"
        api_status = "unhealthy"
    
    uptime = time.time() - start_time
    
    return HealthCheck(
        status=api_status,
        service="shared-database-api",
        database=db_status,
        uptime=uptime
    )

@router.get("/schemas", response_model=SchemaList)
async def list_schemas(db: Session = Depends(get_db)):
    """Lista todos os schemas disponíveis"""
    schemas = [
        SchemaInfo(
            name="whatsapp",
            description="Usuários, mensagens e webhooks do WhatsApp",
            tables=["users", "messages", "webhooks"],
            record_count=db.query(User).count() if db else 0
        ),
        SchemaInfo(
            name="llm",
            description="Conversas, contexto e histórico do LLM",
            tables=["conversations", "context", "history"],
            record_count=0  # TODO: Implementar quando criar os modelos
        ),
        SchemaInfo(
            name="analytics",
            description="Métricas, logs e relatórios",
            tables=["metrics", "logs", "reports"],
            record_count=0  # TODO: Implementar quando criar os modelos
        ),
        SchemaInfo(
            name="auth",
            description="Autenticação e permissões",
            tables=["users", "permissions", "tokens"],
            record_count=0  # TODO: Implementar quando criar os modelos
        ),
        SchemaInfo(
            name="public",
            description="Tabelas compartilhadas entre módulos",
            tables=["schema_init_log", "system_config"],
            record_count=0  # TODO: Implementar quando criar os modelos
        )
    ]
    
    return SchemaList(schemas=schemas) 