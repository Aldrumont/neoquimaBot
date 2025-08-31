import time
import requests
from typing import Dict, Any
from .base import BaseLLMProvider, LLMResponse

class OllamaProvider(BaseLLMProvider):
    """Provider para Ollama (local)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.ollama_url = config.get("base_url", "http://ollama:11434")
    
    async def generate_response(self, message: str, **kwargs) -> LLMResponse:
        """Gera resposta usando Ollama"""
        start_time = time.time()
        
        try:
            # Preparar payload para Ollama
            payload = {
                "model": self.model,
                "prompt": message,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            # Adicionar configurações extras se fornecidas
            if "top_p" in kwargs:
                payload["options"]["top_p"] = kwargs["top_p"]
            if "top_k" in kwargs:
                payload["options"]["top_k"] = kwargs["top_k"]
            
            # Chamar Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return self._create_success_response(
                    response=result.get("response", ""),
                    processing_time=processing_time,
                    tokens_used={
                        "prompt": result.get("prompt_eval_count", 0),
                        "completion": result.get("eval_count", 0)
                    },
                    metadata={
                        "ollama_response": result,
                        "total_duration": result.get("total_duration", 0)
                    }
                )
            else:
                return self._create_error_response(
                    f"Erro Ollama: {response.status_code} - {response.text}",
                    processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return self._create_error_response(str(e), processing_time)
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do Ollama"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "status": "healthy",
                    "provider": "ollama",
                    "url": self.ollama_url,
                    "available_models": [m["name"] for m in models],
                    "total_models": len(models)
                }
            else:
                return {
                    "status": "unhealthy",
                    "provider": "ollama",
                    "url": self.ollama_url,
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "ollama",
                "url": self.ollama_url,
                "error": str(e)
            }
    
    def get_available_models(self) -> list:
        """Lista modelos disponíveis no Ollama"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m["name"] for m in models]
            return []
        except:
            return [] 