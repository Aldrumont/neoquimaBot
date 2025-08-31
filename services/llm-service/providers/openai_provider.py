import time
import requests
from typing import Dict, Any
from .base import BaseLLMProvider, LLMResponse

class OpenAIProvider(BaseLLMProvider):
    """Provider para OpenAI (API)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        
        if not self.api_key:
            raise ValueError("OpenAI API key é obrigatória")
    
    async def generate_response(self, message: str, **kwargs) -> LLMResponse:
        """Gera resposta usando OpenAI API"""
        start_time = time.time()
        
        try:
            # Preparar payload para OpenAI
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": message}
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": False
            }
            
            # Adicionar configurações extras se fornecidas
            if "top_p" in kwargs:
                payload["top_p"] = kwargs["top_p"]
            if "frequency_penalty" in kwargs:
                payload["frequency_penalty"] = kwargs["frequency_penalty"]
            if "presence_penalty" in kwargs:
                payload["presence_penalty"] = kwargs["presence_penalty"]
            
            # Headers com autenticação
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Chamar OpenAI API
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=120
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                choice = result.get("choices", [{}])[0]
                message_content = choice.get("message", {}).get("content", "")
                
                return self._create_success_response(
                    response=message_content,
                    processing_time=processing_time,
                    tokens_used=result.get("usage", {}),
                    metadata={
                        "openai_response": result,
                        "finish_reason": choice.get("finish_reason"),
                        "model": result.get("model")
                    }
                )
            else:
                error_detail = response.json() if response.content else response.text
                return self._create_error_response(
                    f"Erro OpenAI: {response.status_code} - {error_detail}",
                    processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return self._create_error_response(str(e), processing_time)
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde da OpenAI API"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(f"{self.base_url}/models", headers=headers, timeout=10)
            
            if response.status_code == 200:
                models = response.json().get("data", [])
                return {
                    "status": "healthy",
                    "provider": "openai",
                    "url": self.base_url,
                    "available_models": [m["id"] for m in models],
                    "total_models": len(models)
                }
            else:
                return {
                    "status": "unhealthy",
                    "provider": "openai",
                    "url": self.base_url,
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "openai",
                "url": self.base_url,
                "error": str(e)
            }
    
    def get_available_models(self) -> list:
        """Lista modelos disponíveis na OpenAI"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(f"{self.base_url}/models", headers=headers, timeout=10)
            if response.status_code == 200:
                models = response.json().get("data", [])
                return [m["id"] for m in models]
            return []
        except:
            return [] 