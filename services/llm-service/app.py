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
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
SHARED_DB_URL = os.getenv("SHARED_DATABASE_URL", "http://localhost:8000")
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

# ========= Funções auxiliares =========
def get_llm_config() -> LLMConfig:
    """Obtém configurações do LLM do banco compartilhado"""
    try:
        response = requests.get(f"{SHARED_DB_URL}/api/v1/llm/config")
        if response.status_code == 200:
            config_data = response.json()
            return LLMConfig(**config_data)
        else:
            logger.warning(f"Erro ao buscar config LLM: {response.status_code}")
            return LLMConfig()
    except Exception as e:
        logger.error(f"Erro ao conectar com shared-db: {e}")
        return LLMConfig()

def call_ollama(message: str, config: LLMConfig) -> Dict[str, Any]:
    """Chama o Ollama para gerar resposta"""
    try:
        payload = {
            "model": config.model,
            "prompt": message,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens
            }
        }
        
        start_time = time.time()
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=120
        )
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result.get("response", ""),
                "processing_time": processing_time,
                "model": config.model,
                "tokens_used": {
                    "prompt": result.get("prompt_eval_count", 0),
                    "completion": result.get("eval_count", 0)
                }
            }
        else:
            logger.error(f"Erro Ollama: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"Erro Ollama: {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"Erro ao chamar Ollama: {e}")
        return {
            "success": False,
            "error": str(e)
        }

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
        
        return {
            "status": "healthy",
            "service": "llm-service",
            "ollama_status": ollama_status,
            "shared_db_status": shared_db_status,
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
        
        # Chamar Ollama
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
        return config.dict()
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
            
            # Verificar se o modelo padrão está disponível
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            if DEFAULT_MODEL in model_names:
                logger.info(f"✅ Modelo {DEFAULT_MODEL} disponível")
            else:
                logger.warning(f"⚠️ Modelo {DEFAULT_MODEL} não encontrado. Modelos disponíveis: {model_names}")
        else:
            logger.error(f"❌ Ollama retornou status {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com Ollama: {e}")
    
    logger.info("🎯 LLM Service pronto!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 