from typing import Dict, Any, Optional
from .base import BaseLLMProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider
from .azure_openai_provider import AzureOpenAIProvider

class LLMProviderFactory:
    """Factory para criar e gerenciar providers LLM"""
    
    # Mapeamento de providers suportados
    SUPPORTED_PROVIDERS = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "azure_openai": AzureOpenAIProvider
    }
    
    @classmethod
    def create_provider(cls, config: Dict[str, Any]) -> BaseLLMProvider:
        """
        Cria um provider baseado na configuração
        
        Args:
            config: Configuração do provider (deve incluir 'provider')
            
        Returns:
            Instância do provider configurado
            
        Raises:
            ValueError: Se o provider não for suportado ou configuração inválida
        """
        provider_name = config.get("provider", "").lower()
        
        if not provider_name:
            raise ValueError("Campo 'provider' é obrigatório na configuração")
        
        if provider_name not in cls.SUPPORTED_PROVIDERS:
            supported = ", ".join(cls.SUPPORTED_PROVIDERS.keys())
            raise ValueError(f"Provider '{provider_name}' não suportado. Suportados: {supported}")
        
        provider_class = cls.SUPPORTED_PROVIDERS[provider_name]
        
        try:
            return provider_class(config)
        except Exception as e:
            raise ValueError(f"Erro ao criar provider '{provider_name}': {str(e)}")
    
    @classmethod
    def get_supported_providers(cls) -> Dict[str, Dict[str, Any]]:
        """Retorna informações sobre todos os providers suportados"""
        providers_info = {}
        
        for name, provider_class in cls.SUPPORTED_PROVIDERS.items():
            # Criar instância temporária para obter informações
            try:
                temp_config = {
                    "provider": name,
                    "model": "test-model",
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
                temp_provider = provider_class(temp_config)
                providers_info[name] = {
                    "name": name,
                    "class": provider_class.__name__,
                    "description": provider_class.__doc__ or f"Provider {name}",
                    "requires_api_key": name != "ollama",
                    "supports_local": name == "ollama",
                    "supports_streaming": True,  # Todos suportam streaming
                    "config_fields": cls._get_config_fields(name)
                }
            except Exception:
                # Se falhar, usar informações básicas
                providers_info[name] = {
                    "name": name,
                    "class": provider_class.__name__,
                    "description": f"Provider {name}",
                    "requires_api_key": name != "ollama",
                    "supports_local": name == "ollama",
                    "supports_streaming": True,
                    "config_fields": cls._get_config_fields(name)
                }
        
        return providers_info
    
    @classmethod
    def _get_config_fields(cls, provider_name: str) -> Dict[str, Dict[str, Any]]:
        """Retorna campos de configuração específicos para cada provider"""
        base_fields = {
            "provider": {"type": "string", "required": True, "description": "Nome do provider"},
            "model": {"type": "string", "required": True, "description": "Nome do modelo"},
            "temperature": {"type": "float", "required": False, "default": 0.7, "min": 0.0, "max": 2.0},
            "max_tokens": {"type": "integer", "required": False, "default": 1000, "min": 1},
            "context_window": {"type": "integer", "required": False, "default": 4096, "min": 1024}
        }
        
        provider_specific = {
            "ollama": {
                "base_url": {"type": "string", "required": False, "default": "http://ollama:11434", "description": "URL do Ollama"}
            },
            "openai": {
                "api_key": {"type": "string", "required": True, "description": "Chave da API OpenAI"},
                "base_url": {"type": "string", "required": False, "default": "https://api.openai.com/v1", "description": "URL base da API"}
            },
            "anthropic": {
                "api_key": {"type": "string", "required": True, "description": "Chave da API Anthropic"},
                "base_url": {"type": "string", "required": False, "default": "https://api.anthropic.com/v1", "description": "URL base da API"}
            },
            "google": {
                "api_key": {"type": "string", "required": True, "description": "Chave da API Google"},
                "base_url": {"type": "string", "required": False, "default": "https://generativelanguage.googleapis.com/v1beta", "description": "URL base da API"}
            },
            "azure_openai": {
                "api_key": {"type": "string", "required": True, "description": "Chave da API Azure"},
                "base_url": {"type": "string", "required": True, "description": "URL base do Azure OpenAI"},
                "api_version": {"type": "string", "required": False, "default": "2024-02-15-preview", "description": "Versão da API"}
            }
        }
        
        # Combinar campos base com campos específicos do provider
        fields = base_fields.copy()
        if provider_name in provider_specific:
            fields.update(provider_specific[provider_name])
        
        return fields
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida configuração do provider
        
        Returns:
            Dict com resultado da validação
        """
        try:
            provider = cls.create_provider(config)
            is_valid = provider.validate_config()
            
            return {
                "valid": is_valid,
                "provider": config.get("provider"),
                "model": config.get("model"),
                "errors": [] if is_valid else ["Configuração inválida"]
            }
        except Exception as e:
            return {
                "valid": False,
                "provider": config.get("provider"),
                "model": config.get("model"),
                "errors": [str(e)]
            } 