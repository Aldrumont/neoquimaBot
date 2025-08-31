import time
import requests
from typing import Dict, Any
from .base import BaseLLMProvider, LLMResponse

class AnthropicProvider(BaseLLMProvider):
    """Provider para Anthropic (Claude)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.anthropic.com/v1")
        
        if not self.api_key:
            raise ValueError("Anthropic API key é obrigatória")
    
    async def generate_response(self, message: str, **kwargs) -> LLMResponse:
        """Gera resposta usando Anthropic API"""
        start_time = time.time()
        
        try:
            # Preparar payload para Anthropic
            payload = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [
                    {"role": "user", "content": message}
                ]
            }
            
            # Adicionar configurações extras se fornecidas
            if "top_p" in kwargs:
                payload["top_p"] = kwargs["top_p"]
            if "top_k" in kwargs:
                payload["top_k"] = kwargs["top_k"]
            
            # Headers com autenticação
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            # Chamar Anthropic API
            response = requests.post(
                f"{self.base_url}/messages",
                json=payload,
                headers=headers,
                timeout=120
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", [{}])[0]
                message_content = content.get("text", "")
                
                return self._create_success_response(
                    response=message_content,
                    processing_time=processing_time,
                    tokens_used={
                        "input_tokens": result.get("usage", {}).get("input_tokens", 0),
                        "output_tokens": result.get("usage", {}).get("output_tokens", 0)
                    },
                    metadata={
                        "anthropic_response": result,
                        "stop_reason": result.get("stop_reason"),
                        "model": result.get("model")
                    }
                )
            else:
                error_detail = response.json() if response.content else response.text
                return self._create_error_response(
                    f"Erro Anthropic: {response.status_code} - {error_detail}",
                    processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return self._create_error_response(str(e), processing_time)
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde da Anthropic API"""
        try:
            headers = {"x-api-key": self.api_key}
            response = requests.get(f"{self.base_url}/models", headers=headers, timeout=10)
            
            if response.status_code == 200:
                models = response.json().get("data", [])
                return {
                    "status": "healthy",
                    "provider": "anthropic",
                    "url": self.base_url,
                    "available_models": [m["id"] for m in models],
                    "total_models": len(models)
                }
            else:
                return {
                    "status": "unhealthy",
                    "provider": "anthropic",
                    "url": self.base_url,
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "anthropic",
                "url": self.base_url,
                "error": str(e)
            }
    
    def get_available_models(self) -> list:
        """Lista modelos disponíveis na Anthropic"""
        try:
            headers = {"x-api-key": self.api_key}
            response = requests.get(f"{self.base_url}/models", headers=headers, timeout=10)
            if response.status_code == 200:
                models = response.json().get("data", [])
                return [m["id"] for m in models]
            return []
        except:
            return [] 