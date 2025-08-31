from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

class LLMResponse(BaseModel):
    """Resposta padronizada de qualquer provider LLM"""
    success: bool
    response: str
    model: str
    provider: str
    processing_time: float
    tokens_used: Optional[Dict[str, int]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseLLMProvider(ABC):
    """Classe base abstrata para todos os providers LLM"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = config.get("provider", "unknown")
        self.model = config.get("model", "unknown")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)
        self.context_window = config.get("context_window", 4096)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.additional_config = config.get("additional_config", {})
    
    @abstractmethod
    async def generate_response(self, message: str, **kwargs) -> LLMResponse:
        """Gera resposta do LLM - deve ser implementado por cada provider"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do provider - deve ser implementado por cada provider"""
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Retorna informações do provider"""
        return {
            "provider": self.provider_name,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "context_window": self.context_window,
            "base_url": self.base_url,
            "additional_config": self.additional_config
        }
    
    def validate_config(self) -> bool:
        """Valida configuração básica do provider"""
        if not self.model:
            return False
        if self.temperature < 0.0 or self.temperature > 2.0:
            return False
        if self.max_tokens < 1:
            return False
        return True
    
    def _create_error_response(self, error: str, processing_time: float = 0.0) -> LLMResponse:
        """Cria resposta de erro padronizada"""
        return LLMResponse(
            success=False,
            response="",
            model=self.model,
            provider=self.provider_name,
            processing_time=processing_time,
            error=error
        )
    
    def _create_success_response(
        self, 
        response: str, 
        processing_time: float,
        tokens_used: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Cria resposta de sucesso padronizada"""
        return LLMResponse(
            success=True,
            response=response,
            model=self.model,
            provider=self.provider_name,
            processing_time=processing_time,
            tokens_used=tokens_used,
            metadata=metadata
        ) 