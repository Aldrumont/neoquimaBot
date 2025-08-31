from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import requests
import json
import time
import os
from datetime import datetime
from typing import Optional, Dict, Any
import logging

# Importar o novo sistema de providers
from providers.factory import LLMProviderFactory
from providers.base import LLMResponse

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Neoquima LLM Service", version="1.0.0")

# Configurações
SHARED_DB_URL = os.getenv("SHARED_DATABASE_URL", "http://shared-database-api:8000")

# Templates e arquivos estáticos
templates = Jinja2Templates(directory="templates")

# ========= Modelos Pydantic =========
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class ChatResponse(BaseModel):
    response: str
    model: str
    provider: str
    processing_time: float
    tokens_used: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None

class LLMConfig(BaseModel):
    provider: str = "ollama"
    model: str = "llama2:3b"
    temperature: float = 0.7
    max_tokens: int = 1000
    context_window: int = 4096
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    additional_config: Optional[Dict[str, Any]] = None

class ProviderInfo(BaseModel):
    name: str
    description: str
    requires_api_key: bool
    supports_local: bool
    config_fields: Dict[str, Any]

# ========= Funções auxiliares =========
def get_ollama_models() -> list:
    """Obtém lista de modelos disponíveis no Ollama"""
    try:
        ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        if response.status_code == 200:
            models_data = response.json()
            return [model["name"] for model in models_data.get("models", [])]
        else:
            logger.warning(f"Erro ao buscar modelos Ollama: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Erro ao conectar com Ollama: {e}")
        return []

def get_available_api_models() -> dict:
    """Retorna lista de modelos disponíveis para cada provider de API"""
    return {
        "openai": [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ],
        "anthropic": [
            "claude-3.5-sonnet",
            "claude-3.5-haiku",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku"
        ],
        "google": [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
            "gemini-1.0-pro-vision"
        ],
        "azure_openai": [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
    }

def get_llm_config() -> LLMConfig:
    """Obtém configurações do LLM do banco compartilhado"""
    try:
        response = requests.get(f"{SHARED_DB_URL}/llm/config")
        if response.status_code == 200:
            config_data = response.json()
            # Mapear campos do banco para o modelo local
            return LLMConfig(
                provider=config_data.get("provider", "ollama"),
                model=config_data.get("model", "qwen2.5:3b-instruct-q4_K_M"),
                temperature=config_data.get("temperature", 0.7) / 100.0,  # Converter de centésimos
                max_tokens=config_data.get("max_tokens", 1000),
                context_window=config_data.get("context_window", 4096),
                api_key=config_data.get("api_key"),
                base_url=config_data.get("base_url")
            )
        else:
            logger.warning(f"Erro ao buscar config LLM: {response.status_code}")
            # Retornar configuração padrão baseada no que está no banco
            return LLMConfig(
                provider="ollama",
                model="qwen2.5:3b-instruct-q4_K_M",
                temperature=0.7,
                max_tokens=1000,
                context_window=4096
            )
    except Exception as e:
        logger.error(f"Erro ao conectar com shared-db: {e}")
        # Retornar configuração padrão baseada no que está no banco
        return LLMConfig(
            provider="ollama",
            model="qwen2.5:3b-instruct-q4_K_M",
            temperature=0.7,
            max_tokens=1000,
            context_window=4096
        )

async def generate_llm_response(message: str, config: LLMConfig) -> LLMResponse:
    """Gera resposta usando o provider configurado"""
    try:
        # Converter configuração para dict
        config_dict = config.model_dump()
        
        # Criar provider usando factory
        provider = LLMProviderFactory.create_provider(config_dict)
        
        # Gerar resposta
        response = await provider.generate_response(message)
        return response
        
    except Exception as e:
        logger.error(f"Erro ao gerar resposta LLM: {e}")
        # Retornar resposta de erro padronizada
        return LLMResponse(
            success=False,
            response="",
            model=config.model,
            provider=config.provider,
            processing_time=0.0,
            error=str(e)
        )

# ========= Endpoints da API =========
@app.get("/health")
async def health_check():
    """Health check do serviço"""
    try:
        # Verificar shared-db
        shared_db_status = "connected"
        try:
            requests.get(f"{SHARED_DB_URL}/health", timeout=5)
        except:
            shared_db_status = "disconnected"
        
        # Verificar provider ativo
        try:
            config = get_llm_config()
            provider = LLMProviderFactory.create_provider(config.model_dump())
            provider_health = await provider.health_check()
        except Exception as e:
            provider_health = {
                "status": "unhealthy",
                "provider": config.provider if 'config' in locals() else "unknown",
                "error": str(e)
            }
        
        return {
            "status": "healthy",
            "service": "llm-service",
            "shared_db_status": shared_db_status,
            "provider_health": provider_health,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Processa mensagem via LLM"""
    try:
        config = get_llm_config()
        
        # Sobrescrever configurações se fornecidas na request
        if request.temperature is not None:
            config.temperature = request.temperature
        if request.max_tokens is not None:
            config.max_tokens = request.max_tokens
        
        # Gerar resposta usando provider configurado
        llm_response = await generate_llm_response(request.message, config)
        
        if llm_response.success:
            return ChatResponse(
                response=llm_response.response,
                model=llm_response.model,
                provider=llm_response.provider,
                processing_time=llm_response.processing_time,
                tokens_used=llm_response.tokens_used,
                metadata=llm_response.metadata
            )
        else:
            raise HTTPException(status_code=500, detail=llm_response.error)
            
    except Exception as e:
        logger.error(f"Erro no chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/providers")
async def list_providers():
    """Lista todos os providers suportados"""
    try:
        providers = LLMProviderFactory.get_supported_providers()
        return {
            "providers": providers,
            "total": len(providers),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao listar providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/providers/{provider_name}")
async def get_provider_info(provider_name: str):
    """Informações detalhadas sobre um provider específico"""
    try:
        providers = LLMProviderFactory.get_supported_providers()
        if provider_name not in providers:
            raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' não encontrado")
        
        return {
            "provider": providers[provider_name],
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter info do provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/providers/validate")
async def validate_provider_config(config: LLMConfig):
    """Valida configuração de um provider"""
    try:
        validation_result = LLMProviderFactory.validate_config(config.model_dump())
        return {
            "validation": validation_result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao validar config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config():
    """Obtém configurações atuais do LLM"""
    try:
        config = get_llm_config()
        return config.model_dump()
    except Exception as e:
        logger.error(f"Erro ao obter config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/local")
async def get_local_models():
    """Lista modelos disponíveis localmente no Ollama"""
    try:
        models = get_ollama_models()
        return {
            "provider": "ollama",
            "models": models,
            "total": len(models),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao listar modelos locais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/api/{provider}")
async def get_api_models(provider: str):
    """Lista modelos disponíveis para um provider de API específico"""
    try:
        api_models = get_available_api_models()
        if provider not in api_models:
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' não suportado")
        
        models = api_models[provider]
        return {
            "provider": provider,
            "models": models,
            "total": len(models),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar modelos da API {provider}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/all")
async def get_all_models():
    """Lista todos os modelos disponíveis (locais e APIs)"""
    try:
        local_models = get_ollama_models()
        api_models = get_available_api_models()
        
        return {
            "local": {
                "provider": "ollama",
                "models": local_models,
                "total": len(local_models)
            },
            "api": api_models,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao listar todos os modelos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========= Interface Web =========
@app.get("/", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """Interface web do chat"""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_interface(request: Request):
    """Interface administrativa"""
    return templates.TemplateResponse("admin.html", {"request": request})

# ========= Inicialização =========
@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação"""
    try:
        logger.info("🚀 LLM Service iniciando...")
        
        # Verificar configuração inicial
        config = get_llm_config()
        logger.info(f"✅ Configuração carregada: {config.provider} - {config.model}")
        
        # Validar provider
        validation = LLMProviderFactory.validate_config(config.model_dump())
        if validation["valid"]:
            logger.info(f"✅ Provider '{config.provider}' configurado corretamente")
        else:
            logger.warning(f"⚠️ Provider '{config.provider}' com problemas: {validation['errors']}")
        
        logger.info("🚀 LLM Service iniciado com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("LLM_SERVICE_PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port) 