import time
import requests
from typing import Dict, Any
from .base import BaseLLMProvider, LLMResponse

class GoogleProvider(BaseLLMProvider):
    """Provider para Google (Gemini)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://generativelanguage.googleapis.com/v1beta")
        
        if not self.api_key:
            raise ValueError("Google API key é obrigatória")
    
    async def generate_response(self, message: str, **kwargs) -> LLMResponse:
        """Gera resposta usando Google Gemini API"""
        start_time = time.time()
        
        try:
            # Preparar payload para Gemini
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": message}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": self.temperature,
                    "maxOutputTokens": self.max_tokens,
                    "topP": kwargs.get("top_p", 0.8),
                    "topK": kwargs.get("top_k", 40)
                }
            }
            
            # Chamar Gemini API
            response = requests.post(
                f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                json=payload,
                timeout=120
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [{}])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [{}])
                    if parts:
                        message_content = parts[0].get("text", "")
                    else:
                        message_content = ""
                else:
                    message_content = ""
                
                return self._create_success_response(
                    response=message_content,
                    processing_time=processing_time,
                    tokens_used={
                        "input_tokens": result.get("usageMetadata", {}).get("promptTokenCount", 0),
                        "output_tokens": result.get("usageMetadata", {}).get("candidatesTokenCount", 0)
                    },
                    metadata={
                        "gemini_response": result,
                        "finish_reason": candidates[0].get("finishReason") if candidates else None,
                        "model": result.get("model")
                    }
                )
            else:
                error_detail = response.json() if response.content else response.text
                return self._create_error_response(
                    f"Erro Gemini: {response.status_code} - {error_detail}",
                    processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return self._create_error_response(str(e), processing_time)
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde da Google Gemini API"""
        try:
            response = requests.get(
                f"{self.base_url}/models?key={self.api_key}",
                timeout=10
            )
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "status": "healthy",
                    "provider": "google",
                    "url": self.base_url,
                    "available_models": [m["name"] for m in models],
                    "total_models": len(models)
                }
            else:
                return {
                    "status": "unhealthy",
                    "provider": "google",
                    "url": self.base_url,
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "google",
                "url": self.base_url,
                "error": str(e)
            }
    
    def get_available_models(self) -> list:
        """Lista modelos disponíveis no Google Gemini"""
        try:
            response = requests.get(
                f"{self.base_url}/models?key={self.api_key}",
                timeout=10
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m["name"] for m in models]
            return []
        except:
            return [] 