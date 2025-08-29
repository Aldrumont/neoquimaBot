#!/usr/bin/env python3
"""
Script de teste para o ConversationManager
Testa todas as funcionalidades antes da integração
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.core.database import SessionLocal, engine
from api.models.conversation_config import ConversationConfig
from api.models.conversation_session import ConversationSession, ConversationTurn, UserMemory
from api.services.conversation_manager import ConversationManager
from datetime import datetime, timedelta
import uuid


def create_test_config():
    """Cria configuração de teste"""
    db = SessionLocal()
    
    # Verificar se já existe
    existing = db.query(ConversationConfig).filter(
        ConversationConfig.name == "Teste"
    ).first()
    
    if existing:
        print("✅ Configuração de teste já existe")
        return existing
    
    config = ConversationConfig(
        name="Teste",
        description="Configuração para testes do sistema de conversas",
        max_total_tokens=1500,
        summary_tokens=200,
        conversation_window_tokens=800,
        rag_context_tokens=500,
        session_ttl_minutes=30,
        max_conversation_turns=6,
        enable_user_memories=True,
        memory_retention_days=90,
        require_opt_in=True,
        enable_audit_log=True,
        log_citations=True,
        log_latency=True,
        enable_fallback=True,
        fallback_strategy="truncate_oldest"
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    print(f"✅ Configuração de teste criada: ID {config.id}")
    return config


def test_conversation_manager():
    """Testa o ConversationManager"""
    print("\n🧪 TESTANDO CONVERSATION MANAGER...")
    
    db = SessionLocal()
    manager = ConversationManager(db)
    
    # Teste 1: Criar sessão
    print("\n1️⃣ Teste: Criar sessão")
    whatsapp_number = "+5519995731769"
    session = manager.get_or_create_session(whatsapp_number)
    print(f"   ✅ Sessão criada: {session.session_key}")
    print(f"   📊 Turnos: {session.current_turn_count}")
    
    # Teste 2: Adicionar turnos
    print("\n2️⃣ Teste: Adicionar turnos")
    user_turn = manager.add_conversation_turn(
        session.session_key, "user", "Olá, qual é o valor da implantação?"
    )
    print(f"   ✅ Turno usuário adicionado: {user_turn.turn_number}")
    
    # Teste 3: Contexto RAG simulado
    print("\n3️⃣ Teste: Contexto RAG simulado")
    rag_context = {
        "citations": [
            {"document_id": "doc1", "chunk_id": "chunk1", "score": 0.8},
            {"document_id": "doc2", "chunk_id": "chunk2", "score": 0.7}
        ],
        "collection": "neoquima",
        "query": "valor implantação"
    }
    
    assistant_turn = manager.add_conversation_turn(
        session.session_key, "assistant", 
        "O valor da implantação é R$ 49.958,64 dividido em 6 parcelas.",
        rag_context
    )
    print(f"   ✅ Turno assistente adicionado: {assistant_turn.turn_number}")
    
    # Teste 4: Obter contexto
    print("\n4️⃣ Teste: Obter contexto")
    context = manager.get_conversation_context(session.session_key)
    print(f"   📊 Total de tokens: {context['total_tokens']}")
    print(f"   📝 Turnos recentes: {len(context['recent_turns'])}")
    print(f"   📋 Resumo: {len(context['rolling_summary'])} chars")
    
    # Teste 5: Atualizar resumo
    print("\n5️⃣ Teste: Atualizar resumo")
    new_summary = manager.update_rolling_summary(session.session_key, user_turn)
    print(f"   📋 Novo resumo: {len(new_summary)} chars")
    
    # Teste 6: Extrair memórias
    print("\n6️⃣ Teste: Extrair memórias")
    memories = manager.extract_user_memories(whatsapp_number, user_turn)
    print(f"   🧠 Memórias extraídas: {len(memories)}")
    
    # Teste 7: Log de auditoria
    print("\n7️⃣ Teste: Log de auditoria")
    manager.log_audit(
        session.session_key,
        "test_message",
        {"test": True, "correlation_id": str(uuid.uuid4())},
        total_tokens=150,
        rag_score_avg=0.75,
        latency_ms=500
    )
    print("   📊 Log de auditoria criado")
    
    # Teste 8: Reset de conversa
    print("\n8️⃣ Teste: Reset de conversa")
    reset_success = manager.handle_reset_command(whatsapp_number, session.session_id)
    print(f"   🔄 Reset realizado: {reset_success}")
    
    # Teste 9: Nova sessão após reset
    print("\n9️⃣ Teste: Nova sessão após reset")
    new_session = manager.get_or_create_session(whatsapp_number)
    print(f"   ✅ Nova sessão: {new_session.session_key}")
    print(f"   📊 Turnos: {new_session.current_turn_count}")
    
    db.close()
    print("\n🎉 TODOS OS TESTES PASSARAM!")


def test_conversation_flow():
    """Testa um fluxo completo de conversa"""
    print("\n🔄 TESTANDO FLUXO COMPLETO DE CONVERSA...")
    
    db = SessionLocal()
    manager = ConversationManager(db)
    
    whatsapp_number = "+5519995731769"
    
    # Simular conversa completa
    messages = [
        "Olá, sou da empresa ABC",
        "Quero saber sobre o produto NQ-204",
        "Qual é a dosagem recomendada?",
        "E quanto custa a implantação?",
        "Pode me enviar uma proposta?"
    ]
    
    session = manager.get_or_create_session(whatsapp_number)
    
    for i, message in enumerate(messages, 1):
        print(f"\n💬 Mensagem {i}: {message}")
        
        # Simular contexto RAG
        rag_context = {
            "citations": [
                {"document_id": f"doc{i}", "chunk_id": f"chunk{i}", "score": 0.8 - (i * 0.1)}
            ],
            "collection": "neoquima",
            "query": message
        }
        
        # Adicionar turno do usuário
        user_turn = manager.add_conversation_turn(
            session.session_key, "user", message, rag_context
        )
        
        # Simular resposta do assistente
        response = f"Resposta simulada para: {message}"
        assistant_turn = manager.add_conversation_turn(
            session.session_key, "assistant", response
        )
        
        # Atualizar resumo
        manager.update_rolling_summary(session.session_key, user_turn)
        
        # Extrair memórias
        memories = manager.extract_user_memories(whatsapp_number, user_turn)
        
        print(f"   📊 Turno: {user_turn.turn_number}")
        print(f"   🧠 Memórias: {len(memories)}")
        
        # Obter contexto atual
        context = manager.get_conversation_context(session.session_key)
        print(f"   📝 Contexto: {context['total_tokens']} tokens")
    
    # Verificar estado final
    final_context = manager.get_conversation_context(session.session_key)
    print(f"\n📊 ESTADO FINAL:")
    print(f"   📝 Total de turnos: {session.current_turn_count}")
    print(f"   🧠 Memórias totais: {len(manager.get_user_memories(whatsapp_number))}")
    print(f"   📋 Resumo: {len(final_context['rolling_summary'])} chars")
    
    db.close()
    print("\n🎉 FLUXO DE CONVERSA TESTADO COM SUCESSO!")


def cleanup_test_data():
    """Limpa dados de teste"""
    print("\n🧹 LIMPANDO DADOS DE TESTE...")
    
    db = SessionLocal()
    
    # Limpar sessões de teste
    test_sessions = db.query(ConversationSession).filter(
        ConversationSession.whatsapp_number == "+5519995731769"
    ).all()
    
    for session in test_sessions:
        # Limpar turnos
        db.query(ConversationTurn).filter(
            ConversationTurn.session_key == session.session_key
        ).delete()
        
        # Limpar memórias
        db.query(UserMemory).filter(
            UserMemory.whatsapp_number == "+5519995731769"
        ).delete()
        
        # Limpar sessão
        db.delete(session)
    
    # Limpar configuração de teste
    test_config = db.query(ConversationConfig).filter(
        ConversationConfig.name == "Teste"
    ).first()
    
    if test_config:
        db.delete(test_config)
    
    db.commit()
    db.close()
    
    print("✅ Dados de teste limpos!")


if __name__ == "__main__":
    print("🚀 INICIANDO TESTES DO SISTEMA DE CONVERSAS...")
    
    try:
        # Criar configuração de teste
        create_test_config()
        
        # Testar ConversationManager
        test_conversation_manager()
        
        # Testar fluxo completo
        test_conversation_flow()
        
        print("\n🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")
        
        # Perguntar se quer limpar dados
        response = input("\n🧹 Deseja limpar os dados de teste? (s/n): ")
        if response.lower() in ['s', 'sim', 'y', 'yes']:
            cleanup_test_data()
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 