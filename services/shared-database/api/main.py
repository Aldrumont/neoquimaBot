from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from .routes import system_router, whatsapp_router, auth_router
from .core.database import init_db

# Configurações
app = FastAPI(
    title="Neoquima Shared Database API",
    description="API compartilhada para acesso ao banco de dados centralizado",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(system_router)
app.include_router(whatsapp_router)
app.include_router(auth_router)

@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação"""
    try:
        init_db()
        print("✅ Tabelas do banco criadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")

# Endpoints de compatibilidade (sem prefixo)
@app.get("/")
async def root():
    return {
        "message": "Neoquima Shared Database API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "shared-database-api",
        "database": "connected"
    }

@app.get("/schemas")
async def list_schemas():
    """Lista todos os schemas disponíveis"""
    schemas = [
        {
            "name": "whatsapp",
            "description": "Usuários, mensagens e webhooks do WhatsApp",
            "tables": ["users", "messages", "webhooks"]
        },
        {
            "name": "llm",
            "description": "Conversas, contexto e histórico do LLM",
            "tables": ["conversations", "context", "history"]
        },
        {
            "name": "analytics",
            "description": "Métricas, logs e relatórios",
            "tables": ["metrics", "logs", "reports"]
        },
        {
            "name": "auth",
            "description": "Autenticação e permissões",
            "tables": ["users", "permissions", "tokens"]
        },
        {
            "name": "public",
            "description": "Tabelas compartilhadas entre módulos",
            "tables": ["schema_init_log", "system_config"]
        }
    ]
    return {"schemas": schemas}

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 