import time
import requests
from typing import Dict, Any
from .base import BaseLLMProvider, LLMResponse

class AzureOpenAIProvider(BaseLLMProvider):
    """Provider para Azure OpenAI"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.api_version = config.get("api_version", "2024-02-15-preview")
        
        if not self.api_key:
            raise ValueError("Azure OpenAI API key é obrigatória")
        if not self.base_url:
            raise ValueError("Azure OpenAI base_url é obrigatória")
    
    async def generate_response(self, message: str, **kwargs) -> LLMResponse:
        """Gera resposta usando Azure OpenAI API"""
        start_time = time.time()
        
        try:
            # Preparar payload para Azure OpenAI
            payload = {
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
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # URL para Azure OpenAI
            url = f"{self.base_url}/openai/deployments/{self.model}/chat/completions?api-version={self.api_version}"
            
            # Chamar Azure OpenAI API
            response = requests.post(
                url,
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
                        "azure_openai_response": result,
                        "finish_reason": choice.get("finish_reason"),
                        "deployment": self.model,
                        "api_version": self.api_version
                    }
                )
            else:
                error_detail = response.json() if response.content else response.text
                return self._create_error_response(
                    f"Erro Azure OpenAI: {response.status_code} - {error_detail}",
                    processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return self._create_error_response(str(e), processing_time)
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde da Azure OpenAI API"""
        try:
            headers = {"api-key": self.api_key}
            url = f"{self.base_url}/openai/deployments?api-version={self.api_version}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                deployments = response.json().get("data", [])
                return {
                    "status": "healthy",
                    "provider": "azure_openai",
                    "url": self.base_url,
                    "available_deployments": [d["id"] for d in deployments],
                    "total_deployments": len(deployments),
                    "api_version": self.api_version
                }
            else:
                return {
                    "status": "unhealthy",
                    "provider": "azure_openai",
                    "url": self.base_url,
                    "error": f"HTTP {response.status_code}",
                    "api_version": self.api_version
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "azure_openai",
                "url": self.base_url,
                "error": str(e),
                "api_version": self.api_version
            }
    
    def get_available_models(self) -> list:
        """Lista deployments disponíveis no Azure OpenAI"""
        try:
            headers = {"api-key": self.api_key}
            url = f"{self.base_url}/openai/deployments?api-version={self.api_version}"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                deployments = response.json().get("data", [])
                return [d["id"] for d in deployments]
            return []
        except:
            return [] 