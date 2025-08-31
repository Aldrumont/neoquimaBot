#!/usr/bin/env python3
"""
Script para configurar facilmente diferentes providers LLM
"""

import requests
import json
import os
import sys
from typing import Dict, Any

# Configurações
SHARED_DB_URL = os.getenv("SHARED_DB_URL", "http://localhost:8000")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8003")

def print_banner():
    """Imprime banner do script"""
    print("🤖" + "="*60 + "🤖")
    print("           CONFIGURADOR DE PROVIDERS LLM")
    print("           Neoquima Bot - Sistema de IA")
    print("🤖" + "="*60 + "🤖")
    print()

def get_supported_providers() -> Dict[str, Any]:
    """Obtém lista de providers suportados"""
    try:
        response = requests.get(f"{LLM_SERVICE_URL}/api/providers")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erro ao obter providers: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return {}

def get_current_config() -> Dict[str, Any]:
    """Obtém configuração atual do LLM"""
    try:
        response = requests.get(f"{LLM_SERVICE_URL}/api/config")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erro ao obter config atual: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return {}

def create_ollama_config() -> Dict[str, Any]:
    """Cria configuração para Ollama"""
    print("\n🔧 Configurando Ollama (Local)")
    print("-" * 40)
    
    model = input("📝 Modelo (ex: llama2:3b, qwen2.5:3b): ").strip()
    if not model:
        model = "llama2:3b"
    
    base_url = input("🌐 URL do Ollama (Enter para padrão): ").strip()
    if not base_url:
        base_url = "http://ollama:11434"
    
    temperature = input("🌡️ Temperatura (0.0-2.0, Enter para 0.7): ").strip()
    if not temperature:
        temperature = 0.7
    else:
        try:
            temperature = float(temperature)
        except ValueError:
            temperature = 0.7
    
    max_tokens = input("🔢 Máximo de tokens (Enter para 1000): ").strip()
    if not max_tokens:
        max_tokens = 1000
    else:
        try:
            max_tokens = int(max_tokens)
        except ValueError:
            max_tokens = 1000
    
    return {
        "provider": "ollama",
        "model": model,
        "base_url": base_url,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "context_window": 4096,
        "rag_enabled": True,
        "default_rag_collection": "neoquima"
    }

def create_openai_config() -> Dict[str, Any]:
    """Cria configuração para OpenAI"""
    print("\n🔧 Configurando OpenAI")
    print("-" * 40)
    
    api_key = input("🔑 API Key da OpenAI: ").strip()
    if not api_key:
        print("❌ API Key é obrigatória para OpenAI")
        return None
    
    model = input("📝 Modelo (ex: gpt-3.5-turbo, gpt-4): ").strip()
    if not model:
        model = "gpt-3.5-turbo"
    
    base_url = input("🌐 URL base (Enter para padrão): ").strip()
    if not base_url:
        base_url = "https://api.openai.com/v1"
    
    temperature = input("🌡️ Temperatura (0.0-2.0, Enter para 0.7): ").strip()
    if not temperature:
        temperature = 0.7
    else:
        try:
            temperature = float(temperature)
        except ValueError:
            temperature = 0.7
    
    max_tokens = input("🔢 Máximo de tokens (Enter para 1000): ").strip()
    if not max_tokens:
        max_tokens = 1000
    else:
        try:
            max_tokens = int(max_tokens)
        except ValueError:
            max_tokens = 1000
    
    return {
        "provider": "openai",
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "context_window": 4096,
        "rag_enabled": True,
        "default_rag_collection": "neoquima"
    }

def create_anthropic_config() -> Dict[str, Any]:
    """Cria configuração para Anthropic (Claude)"""
    print("\n🔧 Configurando Anthropic (Claude)")
    print("-" * 40)
    
    api_key = input("🔑 API Key da Anthropic: ").strip()
    if not api_key:
        print("❌ API Key é obrigatória para Anthropic")
        return None
    
    model = input("📝 Modelo (ex: claude-3-sonnet-20240229): ").strip()
    if not model:
        model = "claude-3-sonnet-20240229"
    
    base_url = input("🌐 URL base (Enter para padrão): ").strip()
    if not base_url:
        base_url = "https://api.anthropic.com/v1"
    
    temperature = input("🌡️ Temperatura (0.0-2.0, Enter para 0.7): ").strip()
    if not temperature:
        temperature = 0.7
    else:
        try:
            temperature = float(temperature)
        except ValueError:
            temperature = 0.7
    
    max_tokens = input("🔢 Máximo de tokens (Enter para 1000): ").strip()
    if not max_tokens:
        max_tokens = 1000
    else:
        try:
            max_tokens = int(max_tokens)
        except ValueError:
            max_tokens = 1000
    
    return {
        "provider": "anthropic",
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "context_window": 4096,
        "rag_enabled": True,
        "default_rag_collection": "neoquima"
    }

def create_google_config() -> Dict[str, Any]:
    """Cria configuração para Google (Gemini)"""
    print("\n🔧 Configurando Google (Gemini)")
    print("-" * 40)
    
    api_key = input("🔑 API Key do Google: ").strip()
    if not api_key:
        print("❌ API Key é obrigatória para Google")
        return None
    
    model = input("📝 Modelo (ex: gemini-1.5-flash): ").strip()
    if not model:
        model = "gemini-1.5-flash"
    
    base_url = input("🌐 URL base (Enter para padrão): ").strip()
    if not base_url:
        base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    temperature = input("🌡️ Temperatura (0.0-2.0, Enter para 0.7): ").strip()
    if not temperature:
        temperature = 0.7
    else:
        try:
            temperature = float(temperature)
        except ValueError:
            temperature = 0.7
    
    max_tokens = input("🔢 Máximo de tokens (Enter para 1000): ").strip()
    if not max_tokens:
        max_tokens = 1000
    else:
        try:
            max_tokens = int(max_tokens)
        except ValueError:
            max_tokens = 1000
    
    return {
        "provider": "google",
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "context_window": 4096,
        "rag_enabled": True,
        "default_rag_collection": "neoquima"
    }

def create_azure_openai_config() -> Dict[str, Any]:
    """Cria configuração para Azure OpenAI"""
    print("\n🔧 Configurando Azure OpenAI")
    print("-" * 40)
    
    api_key = input("🔑 API Key do Azure: ").strip()
    if not api_key:
        print("❌ API Key é obrigatória para Azure OpenAI")
        return None
    
    base_url = input("🌐 URL base do Azure OpenAI: ").strip()
    if not base_url:
        print("❌ URL base é obrigatória para Azure OpenAI")
        return None
    
    deployment = input("📝 Nome do deployment: ").strip()
    if not deployment:
        print("❌ Nome do deployment é obrigatório")
        return None
    
    api_version = input("📋 Versão da API (Enter para padrão): ").strip()
    if not api_version:
        api_version = "2024-02-15-preview"
    
    temperature = input("🌡️ Temperatura (0.0-2.0, Enter para 0.7): ").strip()
    if not temperature:
        temperature = 0.7
    else:
        try:
            temperature = float(temperature)
        except ValueError:
            temperature = 0.7
    
    max_tokens = input("🔢 Máximo de tokens (Enter para 1000): ").strip()
    if not max_tokens:
        max_tokens = 1000
    else:
        try:
            max_tokens = int(max_tokens)
        except ValueError:
            max_tokens = 1000
    
    return {
        "provider": "azure_openai",
        "model": deployment,
        "api_key": api_key,
        "base_url": base_url,
        "api_version": api_version,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "context_window": 4096,
        "rag_enabled": True,
        "default_rag_collection": "neoquima"
    }

def validate_config(config: Dict[str, Any]) -> bool:
    """Valida configuração do provider"""
    try:
        response = requests.post(f"{LLM_SERVICE_URL}/api/providers/validate", json=config)
        if response.status_code == 200:
            result = response.json()
            if result["validation"]["valid"]:
                print("✅ Configuração válida!")
                return True
            else:
                print("❌ Configuração inválida:")
                for error in result["validation"]["errors"]:
                    print(f"   - {error}")
                return False
        else:
            print(f"❌ Erro na validação: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def save_config_to_db(config: Dict[str, Any]) -> bool:
    """Salva configuração no banco de dados"""
    try:
        # Primeiro, desativar todas as configurações
        response = requests.put(f"{SHARED_DB_URL}/api/v1/llm/config", json=config)
        if response.status_code == 200:
            print("✅ Configuração salva com sucesso!")
            return True
        else:
            print(f"❌ Erro ao salvar: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def main():
    """Função principal"""
    print_banner()
    
    # Verificar conectividade
    print("🔍 Verificando conectividade...")
    
    providers = get_supported_providers()
    if not providers:
        print("❌ Não foi possível conectar ao LLM Service")
        print("   Verifique se o serviço está rodando em:", LLM_SERVICE_URL)
        sys.exit(1)
    
    current_config = get_current_config()
    if current_config:
        print(f"📋 Configuração atual: {current_config['provider']} - {current_config['model']}")
    
    print(f"✅ Conectado ao LLM Service em: {LLM_SERVICE_URL}")
    print(f"✅ Conectado ao Shared Database em: {SHARED_DB_URL}")
    
    # Mostrar providers disponíveis
    print(f"\n📚 Providers disponíveis ({len(providers['providers'])}):")
    for name, info in providers["providers"].items():
        local_icon = "🏠" if info["supports_local"] else "🌐"
        key_icon = "🔑" if info["requires_api_key"] else "🔓"
        print(f"   {local_icon} {key_icon} {name}: {info['description']}")
    
    # Menu de seleção
    print("\n" + "="*60)
    print("🎯 SELECIONE O PROVIDER:")
    print("="*60)
    print("1. Ollama (Local) - 🏠 Sem API key necessária")
    print("2. OpenAI - 🌐 Requer API key")
    print("3. Anthropic (Claude) - 🌐 Requer API key")
    print("4. Google (Gemini) - 🌐 Requer API key")
    print("5. Azure OpenAI - 🌐 Requer API key")
    print("6. Sair")
    print("="*60)
    
    while True:
        choice = input("\n🎯 Escolha uma opção (1-6): ").strip()
        
        config = None
        
        if choice == "1":
            config = create_ollama_config()
        elif choice == "2":
            config = create_openai_config()
        elif choice == "3":
            config = create_anthropic_config()
        elif choice == "4":
            config = create_google_config()
        elif choice == "5":
            config = create_azure_openai_config()
        elif choice == "6":
            print("\n👋 Até logo!")
            sys.exit(0)
        else:
            print("❌ Opção inválida. Escolha 1-6.")
            continue
        
        if config is None:
            continue
        
        # Mostrar configuração criada
        print("\n📋 Configuração criada:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
        
        # Confirmar
        confirm = input("\n✅ Confirmar e salvar? (s/N): ").strip().lower()
        if confirm in ['s', 'sim', 'y', 'yes']:
            # Validar configuração
            if validate_config(config):
                # Salvar no banco
                if save_config_to_db(config):
                    print("\n🎉 Configuração aplicada com sucesso!")
                    print("🔄 Reinicie o LLM Service para aplicar as mudanças.")
                    break
                else:
                    print("\n❌ Falha ao salvar configuração.")
            else:
                print("\n❌ Configuração inválida. Tente novamente.")
        else:
            print("\n🔄 Voltando ao menu...")

if __name__ == "__main__":
    main() 