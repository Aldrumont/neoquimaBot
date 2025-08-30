#!/usr/bin/env python3
"""
Script de teste para verificar se o contexto está sendo construído corretamente
"""

import os
import sys
import logging
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from conversation_handler import ConversationHandler
from shared_database_service import SharedDatabaseService
from whatsapp_service import WhatsAppService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_conversation_context():
    """Testa se o contexto está sendo construído corretamente"""
    
    print("🧪 TESTANDO CONSTRUÇÃO DE CONTEXTO")
    print("=" * 50)
    
    # Inicializar serviços
    shared_db = SharedDatabaseService()
    whatsapp = WhatsAppService()
    handler = ConversationHandler(shared_db, whatsapp)
    
    # Simular dados de sessão
    session_data = {
        "session_key": "test:123",
        "whatsapp_number": "5511999999999",
        "session_id": "123",
        "config_id": 1,
        "current_turn_count": 4,  # Simular que já tem 4 turnos
        "rolling_summary": "Usuário perguntou sobre produtos químicos para tratamento de água"
    }
    
    # Simular contexto RAG
    rag_context = {
        "citations": [
            {
                "document_id": "doc1",
                "chunk_id": "chunk1",
                "score": 0.85,
                "content": "Produtos químicos para tratamento de água potável e efluentes industriais."
            }
        ],
        "average_score": 0.85,
        "collection": "neoquima",
        "query": "produtos químicos"
    }
    
    # Simular mensagem do usuário
    message_text = "Quais são os benefícios dos seus produtos?"
    
    print(f"📝 Mensagem do usuário: {message_text}")
    print(f"🔑 Sessão: {session_data['session_key']}")
    print(f"📊 Turnos anteriores: {session_data['current_turn_count']}")
    print(f"📚 Contexto RAG: {len(rag_context['citations'])} citações")
    print()
    
    try:
        # Construir prompt (isso vai gerar os logs DEBUG)
        prompt = handler._build_structured_prompt(message_text, session_data, rag_context)
        
        print("✅ Prompt construído com sucesso!")
        print(f"📏 Tamanho: {len(prompt)} caracteres")
        print()
        
        # Mostrar primeiros 500 caracteres do prompt
        print("📋 PRIMEIROS 500 CARACTERES DO PROMPT:")
        print("-" * 50)
        print(prompt[:500])
        if len(prompt) > 500:
            print("...")
        print("-" * 50)
        
        # Verificar se contém elementos esperados
        checks = [
            ("Histórico da conversa", "💬 HISTÓRICO DA CONVERSA:" in prompt),
            ("Contexto RAG", "📚 INFORMAÇÕES RELEVANTES:" in prompt),
            ("Instruções", "🤖 INSTRUÇÕES:" in prompt),
            ("Pergunta do usuário", "💬 PERGUNTA DO USUÁRIO:" in prompt),
            ("Mensagem original", message_text in prompt)
        ]
        
        print("\n🔍 VERIFICAÇÕES:")
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}: {result}")
        
    except Exception as e:
        print(f"❌ Erro ao testar: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_conversation_context() 