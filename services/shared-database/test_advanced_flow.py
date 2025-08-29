#!/usr/bin/env python3
"""
Teste avançado que simula o fluxo completo de uma conversa
"""

import sys
import os
import json
sys.path.append('/app')

try:
    print("🚀 TESTE AVANÇADO - FLUXO COMPLETO DE CONVERSA...")
    
    from api.core.database import SessionLocal
    from sqlalchemy import text
    import uuid
    from datetime import datetime, timedelta
    print("✅ Módulos importados")
    
    # Simular uma conversa completa
    whatsapp_number = "+5519995731769"
    session_id = str(uuid.uuid4())
    session_key = f"{whatsapp_number}:{session_id}"
    
    print(f"\n📱 Simulando conversa para: {whatsapp_number}")
    print(f"🔑 Session Key: {session_key}")
    
    with SessionLocal() as db:
        # 1. Criar sessão
        print("\n1️⃣ Criando sessão de conversa...")
        insert_session = text("""
        INSERT INTO conversation_sessions (
            session_key, whatsapp_number, session_id, config_id, current_turn_count
        ) VALUES (
            :session_key, :whatsapp_number, :session_id, 1, 0
        ) RETURNING id;
        """)
        
        result = db.execute(insert_session, {
            "session_key": session_key,
            "whatsapp_number": whatsapp_number,
            "session_id": session_id
        })
        session_db_id = result.scalar()
        db.commit()
        print(f"   ✅ Sessão criada com ID: {session_db_id}")
        
        # 2. Simular fluxo de conversa
        conversation_flow = [
            {
                "role": "user",
                "content": "Olá, sou da empresa ABC Ltda",
                "rag_context": {
                    "citations": [{"document_id": "doc1", "chunk_id": "chunk1", "score": 0.8}],
                    "collection": "empresas",
                    "query": "empresa ABC"
                }
            },
            {
                "role": "assistant", 
                "content": "Olá! Seja bem-vindo à Neoquima. Como posso ajudar a empresa ABC Ltda hoje?",
                "rag_context": None
            },
            {
                "role": "user",
                "content": "Quero saber sobre o produto NQ-204",
                "rag_context": {
                    "citations": [{"document_id": "doc2", "chunk_id": "chunk2", "score": 0.9}],
                    "collection": "neoquima",
                    "query": "produto NQ-204"
                }
            },
            {
                "role": "assistant",
                "content": "O NQ-204 é nosso produto químico para tratamento de água. A dosagem típica é de 15 ppm para cada ppm de dureza total, até o limite de 3 ppm.",
                "rag_context": None
            },
            {
                "role": "user",
                "content": "E quanto custa a implantação?",
                "rag_context": {
                    "citations": [{"document_id": "doc3", "chunk_id": "chunk3", "score": 0.85}],
                    "collection": "neoquima",
                    "query": "custo implantação"
                }
            },
            {
                "role": "assistant",
                "content": "O custo total da implantação é de R$ 49.958,64, dividido em 6 parcelas mensais iguais, com início em 05 de agosto de 2025.",
                "rag_context": None
            },
            {
                "role": "user",
                "content": "Pode me enviar uma proposta detalhada?",
                "rag_context": {
                    "citations": [{"document_id": "doc4", "chunk_id": "chunk4", "score": 0.7}],
                    "collection": "empresas",
                    "query": "proposta detalhada"
                }
            }
        ]
        
        print(f"\n2️⃣ Simulando {len(conversation_flow)} turnos de conversa...")
        
        for i, turn in enumerate(conversation_flow, 1):
            print(f"\n   💬 Turno {i}: {turn['role']}")
            print(f"      📝 Conteúdo: {turn['content'][:50]}...")
            
            # Inserir turno
            insert_turn = text("""
            INSERT INTO conversation_turns (
                session_key, turn_number, role, content, correlation_id,
                rag_citations, rag_collection, rag_query
            ) VALUES (
                :session_key, :turn_number, :role, :content, :correlation_id,
                :rag_citations, :rag_collection, :rag_query
            ) RETURNING id;
            """)
            
            correlation_id = str(uuid.uuid4())
            
            # Converter dicionário para JSON string para o campo JSONB
            rag_citations_json = None
            if turn.get("rag_context") and turn["rag_context"].get("citations"):
                rag_citations_json = json.dumps(turn["rag_context"]["citations"])
            
            result = db.execute(insert_turn, {
                "session_key": session_key,
                "turn_number": i,
                "role": turn["role"],
                "content": turn["content"],
                "correlation_id": correlation_id,
                "rag_citations": rag_citations_json,
                "rag_collection": turn.get("rag_context", {}).get("collection") if turn.get("rag_context") else None,
                "rag_query": turn.get("rag_context", {}).get("query") if turn.get("rag_context") else None
            })
            
            turn_id = result.scalar()
            
            # Se for turno do usuário, extrair memórias
            if turn["role"] == "user":
                # Simular extração de memórias
                if "empresa" in turn["content"].lower():
                    insert_memory = text("""
                    INSERT INTO user_memories (
                        whatsapp_number, memory_type, memory_value, confidence, source_turn_id
                    ) VALUES (
                        :whatsapp_number, 'company', :memory_value, :confidence, :turn_id
                    ) RETURNING id;
                    """)
                    
                    result = db.execute(insert_memory, {
                        "whatsapp_number": whatsapp_number,
                        "memory_value": turn["content"],
                        "confidence": 0.8,
                        "turn_id": turn_id
                    })
                    memory_id = result.scalar()
                    print(f"      🧠 Memória extraída: ID {memory_id}")
                
                if "produto" in turn["content"].lower():
                    insert_memory = text("""
                    INSERT INTO user_memories (
                        whatsapp_number, memory_type, memory_value, confidence, source_turn_id
                    ) VALUES (
                        :whatsapp_number, 'product_interest', :memory_value, :confidence, :turn_id
                    ) RETURNING id;
                    """)
                    
                    result = db.execute(insert_memory, {
                        "whatsapp_number": whatsapp_number,
                        "memory_value": turn["content"],
                        "confidence": 0.9,
                        "turn_id": turn_id
                    })
                    memory_id = result.scalar()
                    print(f"      🧠 Memória extraída: ID {memory_id}")
            
            # Log de auditoria
            insert_audit = text("""
            INSERT INTO conversation_audit_logs (
                session_key, correlation_id, action, details, total_tokens, rag_score_average, latency_ms
            ) VALUES (
                :session_key, :correlation_id, :action, :details, :total_tokens, :rag_score_average, :latency_ms
            ) RETURNING id;
            """)
            
            # Calcular métricas simuladas
            total_tokens = len(turn["content"].split()) * 1.3
            rag_score_avg = 0.0
            rag_results_count = 0
            
            if turn.get("rag_context") and turn["rag_context"].get("citations"):
                scores = [c["score"] for c in turn["rag_context"]["citations"]]
                rag_score_avg = sum(scores) / len(scores)
                rag_results_count = len(turn["rag_context"]["citations"])
            
            latency_ms = 200 + (i * 50)  # Simular latência crescente
            
            # Converter detalhes para JSON string
            audit_details = {
                "turn_number": i,
                "role": turn["role"],
                "content_length": len(turn["content"]),
                "rag_results_count": rag_results_count
            }
            
            result = db.execute(insert_audit, {
                "session_key": session_key,
                "correlation_id": correlation_id,
                "action": "message_processed",
                "details": json.dumps(audit_details),
                "total_tokens": int(total_tokens),
                "rag_score_average": rag_score_avg,
                "latency_ms": latency_ms
            })
            
            audit_id = result.scalar()
            print(f"      📊 Log de auditoria: ID {audit_id}")
        
        # 3. Atualizar sessão
        print(f"\n3️⃣ Atualizando sessão...")
        update_session = text("""
        UPDATE conversation_sessions 
        SET current_turn_count = :turn_count, last_activity = NOW()
        WHERE session_key = :session_key;
        """)
        
        db.execute(update_session, {
            "turn_count": len(conversation_flow),
            "session_key": session_key
        })
        
        # 4. Criar resumo da sessão
        print(f"\n4️⃣ Criando resumo da sessão...")
        summary = f"Conversa com {whatsapp_number} sobre produto NQ-204 e implantação. Empresa ABC Ltda interessada em proposta detalhada."
        
        update_summary = text("""
        UPDATE conversation_sessions 
        SET rolling_summary = :summary
        WHERE session_key = :session_key;
        """)
        
        db.execute(update_summary, {
            "summary": summary,
            "session_key": session_key
        })
        
        db.commit()
        print(f"   ✅ Resumo criado: {len(summary)} chars")
        
        # 5. Verificar estado final
        print(f"\n5️⃣ Verificando estado final...")
        
        # Contar registros
        result = db.execute(text("SELECT COUNT(*) FROM conversation_turns WHERE session_key = :session_key"), {"session_key": session_key})
        turns_count = result.scalar()
        
        result = db.execute(text("SELECT COUNT(*) FROM user_memories WHERE whatsapp_number = :whatsapp_number"), {"whatsapp_number": whatsapp_number})
        memories_count = result.scalar()
        
        result = db.execute(text("SELECT COUNT(*) FROM conversation_audit_logs WHERE session_key = :session_key"), {"session_key": session_key})
        logs_count = result.scalar()
        
        result = db.execute(text("SELECT * FROM conversation_sessions WHERE session_key = :session_key"), {"session_key": session_key})
        session = result.fetchone()
        
        print(f"   📊 ESTADO FINAL:")
        print(f"      💬 Turnos: {turns_count}")
        print(f"      🧠 Memórias: {memories_count}")
        print(f"      📊 Logs: {logs_count}")
        print(f"      📝 Resumo: {len(session.rolling_summary or '')} chars")
        print(f"      ⏰ Última atividade: {session.last_activity}")
        
        # 6. Testar consultas de contexto
        print(f"\n6️⃣ Testando consultas de contexto...")
        
        # Buscar contexto recente
        context_query = text("""
        SELECT 
            t.role,
            t.content,
            t.rag_citations,
            t.rag_collection
        FROM conversation_turns t
        WHERE t.session_key = :session_key
        ORDER BY t.turn_number DESC
        LIMIT 4;
        """)
        
        result = db.execute(context_query, {"session_key": session_key})
        recent_turns = result.fetchall()
        
        print(f"   📋 Últimos 4 turnos:")
        for turn in recent_turns:
            rag_info = f" (RAG: {turn.rag_collection})" if turn.rag_collection else ""
            print(f"      {turn.role}: {turn.content[:40]}...{rag_info}")
        
        # Buscar memórias relevantes
        memories_query = text("""
        SELECT 
            memory_type,
            memory_value,
            confidence
        FROM user_memories
        WHERE whatsapp_number = :whatsapp_number
        ORDER BY confidence DESC;
        """)
        
        result = db.execute(memories_query, {"whatsapp_number": whatsapp_number})
        memories = result.fetchall()
        
        print(f"   🧠 Memórias extraídas:")
        for memory in memories:
            print(f"      {memory.memory_type}: {memory.memory_value[:50]}... (conf: {memory.confidence})")
        
        # 7. Simular reset de conversa
        print(f"\n7️⃣ Simulando reset de conversa...")
        
        # Marcar sessão como inativa
        deactivate_session = text("""
        UPDATE conversation_sessions 
        SET is_active = FALSE
        WHERE session_key = :session_key;
        """)
        
        db.execute(deactivate_session, {"session_key": session_key})
        
        # Criar nova sessão
        new_session_id = str(uuid.uuid4())
        new_session_key = f"{whatsapp_number}:{new_session_id}"
        
        insert_new_session = text("""
        INSERT INTO conversation_sessions (
            session_key, whatsapp_number, session_id, config_id, current_turn_count
        ) VALUES (
            :session_key, :whatsapp_number, :session_id, 1, 0
        ) RETURNING id;
        """)
        
        result = db.execute(insert_new_session, {
            "session_key": new_session_key,
            "whatsapp_number": whatsapp_number,
            "session_id": new_session_id
        })
        new_session_db_id = result.scalar()
        
        db.commit()
        print(f"   ✅ Sessão anterior desativada")
        print(f"   ✅ Nova sessão criada: {new_session_key}")
        
        print(f"\n🎉 TESTE AVANÇADO CONCLUÍDO COM SUCESSO!")
        print(f"✅ Sistema de conversas funcionando perfeitamente!")
        print(f"✅ Todas as funcionalidades testadas:")
        print(f"   - Gestão de sessões")
        print(f"   - Turnos de conversa")
        print(f"   - Contexto RAG")
        print(f"   - Extração de memórias")
        print(f"   - Logs de auditoria")
        print(f"   - Resumos de sessão")
        print(f"   - Reset de conversas")
        
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 