#!/usr/bin/env python3
"""
Teste de integração do ConversationHandler no WhatsApp Gateway
"""

import requests
import json
import time

def test_webhook_simulation():
    """Testa a simulação de webhook do WhatsApp"""
    
    # URL do WhatsApp Gateway
    webhook_url = "http://localhost:8081/webhook"
    
    # Simular payload do WhatsApp
    test_payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "+5519995731769",
                        "text": {"body": "Olá, sou da empresa XYZ"}
                    }]
                }
            }]
        }]
    }
    
    print("🧪 TESTANDO INTEGRAÇÃO DO CONVERSATIONHANDLER...")
    print(f"📡 URL: {webhook_url}")
    print(f"📱 Número: +5519995731769")
    print(f"💬 Mensagem: {test_payload['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']}")
    
    try:
        # Fazer requisição POST para o webhook
        print("\n🚀 Enviando requisição...")
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Resposta recebida:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Verificar se o sistema de contexto está funcionando
            if "correlation_id" in result:
                print("\n🎉 SISTEMA DE CONTEXTO FUNCIONANDO!")
                print(f"🔑 Correlation ID: {result['correlation_id']}")
                
                if "session_key" in result:
                    print(f"📝 Session Key: {result['session_key']}")
                
                if "rag_context" in result:
                    print(f"🔍 RAG Context: {result['rag_context']}")
                
                return True
            else:
                print("\n⚠️ Resposta não contém correlation_id")
                return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de requisição: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_reset_command():
    """Testa o comando de reset"""
    
    webhook_url = "http://localhost:8081/webhook"
    
    # Simular comando de reset
    reset_payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "+5519995731769",
                        "text": {"body": "novo assunto"}
                    }]
                }
            }]
        }]
    }
    
    print("\n🔄 TESTANDO COMANDO DE RESET...")
    print(f"💬 Comando: {reset_payload['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']}")
    
    try:
        response = requests.post(
            webhook_url,
            json=reset_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Resposta de reset:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get("status") == "reset_success":
                print("\n🎉 COMANDO DE RESET FUNCIONANDO!")
                return True
            else:
                print("\n⚠️ Reset não foi bem-sucedido")
                return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de reset: {e}")
        return False

def test_context_dependent_questions():
    """Testa perguntas dependentes de contexto"""
    
    webhook_url = "http://localhost:8081/webhook"
    
    # Sequência de perguntas dependentes
    questions = [
        "Qual é a capital do Brasil?",
        "Qual é a população dessa cidade?"
    ]
    
    print("\n🧠 TESTANDO PERGUNTAS DEPENDENTES...")
    
    for i, question in enumerate(questions, 1):
        print(f"\n💬 Pergunta {i}: {question}")
        
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "+5519995731769",
                            "text": {"body": question}
                        }]
                    }
                }]
            }]
        }
        
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Resposta {i}: {result.get('status', 'unknown')}")
                
                if "correlation_id" in result:
                    print(f"🔑 Correlation ID: {result['correlation_id']}")
                
                if "session_key" in result:
                    print(f"📝 Session Key: {result['session_key']}")
                
                # Aguardar um pouco entre as perguntas
                time.sleep(2)
            else:
                print(f"❌ Erro na pergunta {i}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na pergunta {i}: {e}")
            return False
    
    print("\n🎉 TESTE DE PERGUNTAS DEPENDENTES CONCLUÍDO!")
    return True

if __name__ == "__main__":
    print("🚀 INICIANDO TESTES DE INTEGRAÇÃO...")
    
    # Teste 1: Mensagem básica
    test1_success = test_webhook_simulation()
    
    # Teste 2: Comando de reset
    test2_success = test_reset_command()
    
    # Teste 3: Perguntas dependentes
    test3_success = test_context_dependent_questions()
    
    # Resultado final
    print("\n" + "="*50)
    print("📊 RESULTADO DOS TESTES:")
    print(f"✅ Teste 1 (Mensagem básica): {'PASSOU' if test1_success else 'FALHOU'}")
    print(f"✅ Teste 2 (Comando reset): {'PASSOU' if test2_success else 'FALHOU'}")
    print(f"✅ Teste 3 (Perguntas dependentes): {'PASSOU' if test3_success else 'FALHOU'}")
    
    total_tests = 3
    passed_tests = sum([test1_success, test2_success, test3_success])
    
    print(f"\n🎯 TOTAL: {passed_tests}/{total_tests} testes passaram")
    
    if passed_tests == total_tests:
        print("🎉 TODOS OS TESTES PASSARAM! SISTEMA INTEGRADO COM SUCESSO!")
    else:
        print("⚠️ ALGUNS TESTES FALHARAM. Verifique os logs.")
    
    print("="*50) 