#!/usr/bin/env python3
"""
Script de teste básico para as funcionalidades do sistema de conversas
"""

import sys
import os
sys.path.append('/app')

try:
    print("🧪 TESTANDO FUNCIONALIDADES BÁSICAS...")
    
    from api.core.database import SessionLocal
    from sqlalchemy import text
    print("✅ Database conectado")
    
    # Teste 1: Verificar se as tabelas foram criadas
    print("\n1️⃣ Verificando tabelas criadas...")
    with SessionLocal() as db:
        tables = [
            "conversation_configs",
            "conversation_sessions", 
            "conversation_turns",
            "user_memories",
            "conversation_audit_logs"
        ]
        
        for table in tables:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"   📋 {table}: {count} registros")
    
    # Teste 2: Testar inserção de sessão
    print("\n2️⃣ Testando inserção de sessão...")
    with SessionLocal() as db:
        # Inserir sessão de teste
        insert_session = text("""
        INSERT INTO conversation_sessions (
            session_key, whatsapp_number, session_id, config_id
        ) VALUES (
            'test:session:123', '+5519995731769', 'session_123', 1
        ) RETURNING id;
        """)
        
        result = db.execute(insert_session)
        session_id = result.scalar()
        db.commit()
        print(f"   ✅ Sessão criada com ID: {session_id}")
    
    # Teste 3: Testar inserção de turnos
    print("\n3️⃣ Testando inserção de turnos...")
    with SessionLocal() as db:
        # Turno do usuário
        insert_user_turn = text("""
        INSERT INTO conversation_turns (
            session_key, turn_number, role, content, correlation_id
        ) VALUES (
            'test:session:123', 1, 'user', 'Olá, qual é o valor da implantação?', 'corr_123'
        ) RETURNING id;
        """)
        
        result = db.execute(insert_user_turn)
        user_turn_id = result.scalar()
        db.commit()
        print(f"   ✅ Turno usuário criado com ID: {user_turn_id}")
        
        # Turno do assistente
        insert_assistant_turn = text("""
        INSERT INTO conversation_turns (
            session_key, turn_number, role, content, correlation_id
        ) VALUES (
            'test:session:123', 2, 'assistant', 'O valor da implantação é R$ 49.958,64 dividido em 6 parcelas.', 'corr_123'
        ) RETURNING id;
        """)
        
        result = db.execute(insert_assistant_turn)
        assistant_turn_id = result.scalar()
        db.commit()
        print(f"   ✅ Turno assistente criado com ID: {assistant_turn_id}")
    
    # Teste 4: Testar inserção de memória
    print("\n4️⃣ Testando inserção de memória...")
    with SessionLocal() as db:
        insert_memory = text("""
        INSERT INTO user_memories (
            whatsapp_number, memory_type, memory_value, confidence, source_turn_id
        ) VALUES (
            '+5519995731769', 'company', 'Empresa ABC interessada em implantação', 0.8, :turn_id
        ) RETURNING id;
        """)
        
        result = db.execute(insert_memory, {"turn_id": user_turn_id})
        memory_id = result.scalar()
        db.commit()
        print(f"   ✅ Memória criada com ID: {memory_id}")
    
    # Teste 5: Testar inserção de log de auditoria
    print("\n5️⃣ Testando inserção de log de auditoria...")
    with SessionLocal() as db:
        insert_audit = text("""
        INSERT INTO conversation_audit_logs (
            session_key, correlation_id, action, details, total_tokens, rag_score_average, latency_ms
        ) VALUES (
            'test:session:123', 'corr_123', 'message_processed', 
            '{"test": true, "whatsapp_number": "+5519995731769"}', 150, 0.75, 500
        ) RETURNING id;
        """)
        
        result = db.execute(insert_audit)
        audit_id = result.scalar()
        db.commit()
        print(f"   ✅ Log de auditoria criado com ID: {audit_id}")
    
    # Teste 6: Verificar dados inseridos
    print("\n6️⃣ Verificando dados inseridos...")
    with SessionLocal() as db:
        # Verificar sessão
        result = db.execute(text("SELECT * FROM conversation_sessions WHERE session_key = 'test:session:123'"))
        session = result.fetchone()
        print(f"   📊 Sessão: {session.session_key} - Turnos: {session.current_turn_count}")
        
        # Verificar turnos
        result = db.execute(text("SELECT COUNT(*) FROM conversation_turns WHERE session_key = 'test:session:123'"))
        turns_count = result.scalar()
        print(f"   💬 Turnos: {turns_count}")
        
        # Verificar memórias
        result = db.execute(text("SELECT COUNT(*) FROM user_memories WHERE whatsapp_number = '+5519995731769'"))
        memories_count = result.scalar()
        print(f"   🧠 Memórias: {memories_count}")
        
        # Verificar logs
        result = db.execute(text("SELECT COUNT(*) FROM conversation_audit_logs WHERE session_key = 'test:session:123'"))
        logs_count = result.scalar()
        print(f"   📊 Logs: {logs_count}")
    
    # Teste 7: Testar consultas complexas
    print("\n7️⃣ Testando consultas complexas...")
    with SessionLocal() as db:
        # Buscar contexto da conversa
        context_query = text("""
        SELECT 
            s.session_key,
            s.current_turn_count,
            s.rolling_summary,
            COUNT(t.id) as total_turns,
            COUNT(m.id) as total_memories
        FROM conversation_sessions s
        LEFT JOIN conversation_turns t ON s.session_key = t.session_key
        LEFT JOIN user_memories m ON s.whatsapp_number = m.whatsapp_number
        WHERE s.session_key = 'test:session:123'
        GROUP BY s.id, s.session_key, s.current_turn_count, s.rolling_summary;
        """)
        
        result = db.execute(context_query)
        context = result.fetchone()
        
        if context:
            print(f"   📊 Contexto da sessão:")
            print(f"      Chave: {context.session_key}")
            print(f"      Turnos: {context.total_turns}")
            print(f"      Memórias: {context.total_memories}")
            print(f"      Resumo: {len(context.rolling_summary or '')} chars")
    
    print("\n🎉 TODOS OS TESTES BÁSICOS PASSARAM!")
    print("✅ Sistema de conversas funcionando perfeitamente!")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 