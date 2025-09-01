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

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Neoquima LLM Service", version="1.0.0")

# Configurações
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
SHARED_DB_URL = os.getenv("SHARED_DATABASE_URL", "http://shared-database-api:8000")
DEFAULT_MODEL = "qwen2.5:3b-instruct-q4_K_M"

# Templates e arquivos estáticos
templates = Jinja2Templates(directory="templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")

# ========= Modelos Pydantic =========
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class ChatResponse(BaseModel):
    response: str
    model: str
    processing_time: float
    tokens_used: Optional[Dict[str, int]] = None

class LLMConfig(BaseModel):
    provider: str = "ollama"
    model: str = DEFAULT_MODEL
    temperature: float = 0.7
    max_tokens: int = 1000
    context_window: int = 4096
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    additional_config: Optional[Dict[str, Any]] = None

# ========= Funções auxiliares =========
def get_llm_config() -> LLMConfig:
    """Obtém configurações do LLM do banco compartilhado"""
    try:
        response = requests.get(f"{SHARED_DB_URL}/llm/config")
        if response.status_code == 200:
            config_data = response.json()
            return LLMConfig(
                provider=config_data.get("provider", "ollama"),
                model=config_data.get("model", DEFAULT_MODEL),
                temperature=config_data.get("temperature", 0.7),
                max_tokens=config_data.get("max_tokens", 1000),
                context_window=config_data.get("context_window", 4096),
                api_key=config_data.get("api_key"),
                base_url=config_data.get("base_url"),
                additional_config=config_data.get("additional_config")
            )
        else:
            logger.warning(f"Erro ao buscar config LLM: {response.status_code}")
            return LLMConfig()
    except Exception as e:
        logger.error(f"Erro ao conectar com shared-db: {e}")
        return LLMConfig()

def call_ollama(message: str, config: LLMConfig) -> Dict[str, Any]:
    """Chama o provider correto baseado na configuração"""
    try:
        provider = config.provider.lower()
        
        if provider == "ollama":
            return call_ollama_local(message, config)
        else:
            # Para todos os providers externos, usar LiteLLM
            return call_external_via_litellm(message, config)
            
    except Exception as e:
        logger.error(f"Erro ao chamar LLM: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def call_ollama_local(message: str, config: LLMConfig) -> Dict[str, Any]:
    """Chama modelo local do Ollama"""
    try:
        from openai import OpenAI
        
        client = OpenAI(
            base_url=f"{OLLAMA_URL}/v1",
            api_key="ollama"
        )
        
        logger.info(f"Chamando modelo local Ollama: {config.model}")
        
        start_time = time.time()
        response = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": message}],
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "response": response.choices[0].message.content,
            "processing_time": processing_time,
            "model": config.model,
            "tokens_used": {
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens
            }
        }
            
    except Exception as e:
        logger.error(f"Erro ao chamar Ollama local: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def call_external_via_litellm(message: str, config: LLMConfig) -> Dict[str, Any]:
    """Chama providers externos via LiteLLM"""
    try:
        from litellm import completion
        
        # Configurar variáveis de ambiente para LiteLLM
        if config.provider == "openai":
            # Usar variável de ambiente se config.api_key for None
            if config.api_key:
                logger.info(f"DEBUG: config.api_key length: {len(config.api_key)}")
                logger.info(f"DEBUG: config.api_key prefix: {config.api_key[:50]}...")
                os.environ["OPENAI_API_KEY"] = config.api_key
                logger.info(f"DEBUG: os.environ OPENAI_API_KEY length: {len(os.environ.get('OPENAI_API_KEY', ''))}")
            if config.base_url:
                os.environ["OPENAI_API_BASE"] = config.base_url
            model_name = config.model  # Usar o modelo da configuração
            
        elif config.provider == "anthropic":
            # Usar variável de ambiente se config.api_key for None
            if config.api_key:
                os.environ["ANTHROPIC_API_KEY"] = config.api_key
            model_name = config.model  # Usar o modelo da configuração
            
        elif config.provider == "google":
            # Usar variável de ambiente se config.api_key for None
            if config.api_key:
                os.environ["GOOGLE_API_KEY"] = config.api_key
            model_name = config.model  # Usar o modelo da configuração
            
        elif config.provider == "deepseek":
            # Usar variável de ambiente se config.api_key for None
            if config.api_key:
                os.environ["DEEPSEEK_API_KEY"] = config.api_key
            if config.base_url:
                os.environ["DEEPSEEK_API_BASE"] = config.base_url
            model_name = config.model  # Usar o modelo da configuração
            
        else:
            return {
                "success": False,
                "error": f"Provider não suportado: {config.provider}"
            }
        
        logger.info(f"Chamando {config.provider} via LiteLLM: {model_name}")
        
        start_time = time.time()
        response = completion(
            model=model_name,
            messages=[{"role": "user", "content": message}],
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "response": response.choices[0].message.content,
            "processing_time": processing_time,
            "model": config.model,
            "tokens_used": {
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens
            }
        }
            
    except Exception as e:
        logger.error(f"Erro ao chamar {config.provider} via LiteLLM: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def ensure_model_exists(model_name: str, config: LLMConfig) -> bool:
    """Garante que o modelo existe no Ollama, puxando se necessário"""
    try:
        # Verificar se o modelo já existe
        response = requests.get(f"{OLLAMA_URL}/v1/models")
        if response.status_code == 200:
            models = response.json().get("data", [])
            model_ids = [model["id"] for model in models]
            
            if model_name in model_ids:
                logger.info(f"✅ Modelo {model_name} já existe")
                return True
        
        # Modelo não existe, tentar puxar
        logger.info(f"📥 Puxando modelo {model_name}...")
        
        if model_name.startswith("openai:"):
            return await pull_openai_model(model_name, config)
        elif model_name.startswith("anthropic:"):
            return await pull_anthropic_model(model_name, config)
        elif model_name.startswith("google:"):
            return await pull_google_model(model_name, config)
        elif model_name.startswith("azure:"):
            return await pull_azure_model(model_name, config)
        else:
            logger.warning(f"Provider não suportado para pull: {model_name}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao verificar/preparar modelo: {e}")
        return False

async def pull_openai_model(model_name: str, config: LLMConfig) -> bool:
    """Puxa modelo OpenAI para o Ollama"""
    try:
        if not config.api_key:
            logger.error("API key OpenAI não configurada")
            return False
        
        # Criar modelfile para OpenAI
        modelfile_content = f"""
FROM openai/gpt-4o-mini
PARAMETER api_key {config.api_key}
PARAMETER base_url {config.base_url or 'https://api.openai.com/v1'}
"""
        
        # Criar modelo no Ollama
        create_response = requests.post(
            f"{OLLAMA_URL}/api/create",
            json={
                "name": model_name,
                "modelfile": modelfile_content
            },
            timeout=60
        )
        
        if create_response.status_code == 200:
            logger.info(f"✅ Modelo OpenAI criado: {model_name}")
            return True
        else:
            logger.error(f"❌ Falha ao criar modelo OpenAI: {create_response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao puxar modelo OpenAI: {e}")
        return False

# ========= Endpoints da API =========
@app.get("/health")
async def health_check():
    """Health check do serviço"""
    try:
        # Verificar Ollama
        ollama_response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        ollama_status = "connected" if ollama_response.status_code == 200 else "disconnected"
        
        # Verificar shared-db
        shared_db_status = "connected"
        try:
            requests.get(f"{SHARED_DB_URL}/health", timeout=5)
        except:
            shared_db_status = "disconnected"
        
        # Verificar configuração atual
        try:
            config = get_llm_config()
            provider_info = {
                "provider": config.provider,
                "model": config.model,
                "status": "configured"
            }
        except:
            provider_info = {
                "provider": "unknown",
                "model": "unknown",
                "status": "error"
            }
        
        return {
            "status": "healthy",
            "service": "llm-service",
            "ollama_status": ollama_status,
            "shared_db_status": shared_db_status,
            "provider_info": provider_info,
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
        
        # Chamar Ollama (que decide internamente como rotear)
        result = call_ollama(request.message, config)
        
        if result["success"]:
            return ChatResponse(
                response=result["response"],
                model=result["model"],
                processing_time=result["processing_time"],
                tokens_used=result.get("tokens_used")
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Erro no chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
async def list_models():
    """Lista modelos disponíveis no Ollama"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {"models": models}
        else:
            raise HTTPException(status_code=500, detail="Erro ao listar modelos")
    except Exception as e:
        logger.error(f"Erro ao listar modelos: {e}")
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
    """Evento executado na inicialização"""
    logger.info("🚀 LLM Service iniciando...")
    
    # Verificar se o Ollama está rodando
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Ollama conectado com sucesso")
            
            # Verificar configuração inicial
            try:
                config = get_llm_config()
                logger.info(f"📋 Configuração carregada: {config.provider} - {config.model}")
                logger.info("🎯 LLM Service pronto para rotear chamadas!")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao carregar configuração: {e}")
                
        else:
            logger.error(f"❌ Ollama retornou status {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com Ollama: {e}")
    
    logger.info("🎯 LLM Service pronto!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 