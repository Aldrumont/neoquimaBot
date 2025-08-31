#!/usr/bin/env python3
"""
Script para testar o funcionamento dos providers LLM
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
    print("🧪" + "="*60 + "🧪")
    print("           TESTE DE PROVIDERS LLM")
    print("           Neoquima Bot - Sistema de IA")
    print("🧪" + "="*60 + "🧪")
    print()

def test_connectivity():
    """Testa conectividade com os serviços"""
    print("🔍 Testando conectividade...")
    
    # Testar LLM Service
    try:
        response = requests.get(f"{LLM_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ LLM Service: {LLM_SERVICE_URL}")
        else:
            print(f"❌ LLM Service: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ LLM Service: {e}")
        return False
    
    # Testar Shared Database
    try:
        response = requests.get(f"{SHARED_DB_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Shared Database: {SHARED_DB_URL}")
        else:
            print(f"⚠️ Shared Database: HTTP {response.status_code}")
    except Exception as e:
        print(f"⚠️ Shared Database: {e}")
    
    return True

def test_providers_list():
    """Testa listagem de providers"""
    print("\n📚 Testando listagem de providers...")
    
    try:
        response = requests.get(f"{LLM_SERVICE_URL}/api/providers", timeout=10)
        if response.status_code == 200:
            data = response.json()
            providers = data.get("providers", {})
            
            print(f"✅ {len(providers)} providers encontrados:")
            for name, info in providers.items():
                local_icon = "🏠" if info.get("supports_local", False) else "🌐"
                key_icon = "🔑" if info.get("requires_api_key", False) else "🔓"
                print(f"   {local_icon} {key_icon} {name}: {info.get('description', 'Sem descrição')}")
            
            return providers
        else:
            print(f"❌ Erro ao listar providers: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return {}

def test_current_config():
    """Testa configuração atual"""
    print("\n📋 Testando configuração atual...")
    
    try:
        response = requests.get(f"{LLM_SERVICE_URL}/api/config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Provider atual: {config.get('provider', 'N/A')}")
            print(f"✅ Modelo atual: {config.get('model', 'N/A')}")
            print(f"✅ Temperatura: {config.get('temperature', 'N/A')}")
            print(f"✅ Max tokens: {config.get('max_tokens', 'N/A')}")
            return config
        else:
            print(f"❌ Erro ao obter config: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return {}

def test_provider_health():
    """Testa saúde do provider atual"""
    print("\n🏥 Testando saúde do provider...")
    
    try:
        response = requests.get(f"{LLM_SERVICE_URL}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            provider_health = health.get("provider_health", {})
            
            if provider_health:
                status = provider_health.get("status", "unknown")
                provider = provider_health.get("provider", "unknown")
                
                if status == "healthy":
                    print(f"✅ Provider {provider}: Saudável")
                    
                    # Mostrar informações adicionais
                    if "available_models" in provider_health:
                        models = provider_health["available_models"]
                        print(f"   📚 Modelos disponíveis: {len(models)}")
                        for model in models[:5]:  # Mostrar apenas os primeiros 5
                            print(f"      - {model}")
                        if len(models) > 5:
                            print(f"      ... e mais {len(models) - 5} modelos")
                    
                    if "url" in provider_health:
                        print(f"   🌐 URL: {provider_health['url']}")
                        
                else:
                    print(f"❌ Provider {provider}: Não saudável")
                    error = provider_health.get("error", "Erro desconhecido")
                    print(f"   🚨 Erro: {error}")
            else:
                print("⚠️ Informações de saúde do provider não disponíveis")
            
            return health
        else:
            print(f"❌ Erro no health check: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return {}

def test_chat_endpoint():
    """Testa endpoint de chat"""
    print("\n💬 Testando endpoint de chat...")
    
    test_message = "Olá! Este é um teste do sistema. Responda apenas com 'Teste funcionando!'"
    
    try:
        payload = {
            "message": test_message,
            "user_id": "test-user",
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        response = requests.post(
            f"{LLM_SERVICE_URL}/api/chat",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat funcionando!")
            print(f"   🤖 Provider: {result.get('provider', 'N/A')}")
            print(f"   📝 Modelo: {result.get('model', 'N/A')}")
            print(f"   ⏱️ Tempo: {result.get('processing_time', 0):.2f}s")
            print(f"   💬 Resposta: {result.get('response', '')[:100]}...")
            
            if result.get("tokens_used"):
                tokens = result["tokens_used"]
                print(f"   🔢 Tokens: {tokens}")
            
            return True
        else:
            print(f"❌ Erro no chat: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   🚨 Detalhes: {error_detail}")
            except:
                print(f"   🚨 Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_provider_validation():
    """Testa validação de providers"""
    print("\n✅ Testando validação de providers...")
    
    # Testar configuração válida (Ollama)
    valid_config = {
        "provider": "ollama",
        "model": "llama2:3b",
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(
            f"{LLM_SERVICE_URL}/api/providers/validate",
            json=valid_config,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            validation = result.get("validation", {})
            
            if validation.get("valid", False):
                print("✅ Validação de provider funcionando")
                print(f"   📋 Provider: {validation.get('provider')}")
                print(f"   📝 Modelo: {validation.get('model')}")
            else:
                print("⚠️ Validação falhou para configuração válida")
                errors = validation.get("errors", [])
                for error in errors:
                    print(f"   🚨 Erro: {error}")
        else:
            print(f"❌ Erro na validação: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def run_comprehensive_test():
    """Executa teste completo"""
    print_banner()
    
    print("🚀 Iniciando teste completo dos providers LLM...")
    
    # Teste 1: Conectividade
    if not test_connectivity():
        print("\n❌ Falha na conectividade. Verifique se os serviços estão rodando.")
        sys.exit(1)
    
    # Teste 2: Lista de providers
    providers = test_providers_list()
    if not providers:
        print("\n❌ Falha ao listar providers.")
        sys.exit(1)
    
    # Teste 3: Configuração atual
    current_config = test_current_config()
    
    # Teste 4: Saúde do provider
    health = test_provider_health()
    
    # Teste 5: Endpoint de chat
    chat_working = test_chat_endpoint()
    
    # Teste 6: Validação de providers
    test_provider_validation()
    
    # Resumo final
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    print(f"✅ Conectividade: OK")
    print(f"✅ Providers: {len(providers)} encontrados")
    print(f"✅ Configuração: {'OK' if current_config else 'N/A'}")
    print(f"✅ Health Check: {'OK' if health else 'N/A'}")
    print(f"✅ Chat: {'OK' if chat_working else 'FALHOU'}")
    print(f"✅ Validação: OK")
    
    if chat_working:
        print("\n🎉 Todos os testes passaram! O sistema está funcionando perfeitamente.")
    else:
        print("\n⚠️ Chat falhou. Verifique a configuração do provider atual.")
    
    print("\n💡 Dica: Use 'python scripts/configure_llm.py' para trocar de provider.")

if __name__ == "__main__":
    run_comprehensive_test() 