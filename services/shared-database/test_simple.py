#!/usr/bin/env python3
"""
Script simples para testar a criação das tabelas
"""

import sys
import os
sys.path.append('/app')

try:
    print("🔍 Importando módulos...")
    from api.core.database import engine, SessionLocal
    from sqlalchemy import text
    print("✅ Database importado")
    
    from api.models.base import Base
    print("✅ Base importado")
    
    # Importar todos os modelos
    from api.models.user import User
    from api.models.llm_config import LLMConfig
    print("✅ Modelos existentes importados")
    
    # Criar tabelas existentes primeiro
    print("🏗️ Criando tabelas existentes...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas existentes criadas")
    
    # Agora vamos criar as novas tabelas manualmente
    print("🏗️ Criando novas tabelas...")
    
    # Tabela conversation_configs
    create_config_table = text("""
    CREATE TABLE IF NOT EXISTS conversation_configs (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL,
        description TEXT,
        max_total_tokens INTEGER DEFAULT 1500,
        summary_tokens INTEGER DEFAULT 200,
        conversation_window_tokens INTEGER DEFAULT 800,
        rag_context_tokens INTEGER DEFAULT 500,
        session_ttl_minutes INTEGER DEFAULT 30,
        max_conversation_turns INTEGER DEFAULT 6,
        enable_user_memories BOOLEAN DEFAULT TRUE,
        memory_retention_days INTEGER DEFAULT 90,
        require_opt_in BOOLEAN DEFAULT TRUE,
        enable_audit_log BOOLEAN DEFAULT TRUE,
        log_citations BOOLEAN DEFAULT TRUE,
        log_latency BOOLEAN DEFAULT TRUE,
        enable_fallback BOOLEAN DEFAULT TRUE,
        fallback_strategy VARCHAR(50) DEFAULT 'truncate_oldest',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE
    );
    """)
    
    # Tabela conversation_sessions
    create_sessions_table = text("""
    CREATE TABLE IF NOT EXISTS conversation_sessions (
        id SERIAL PRIMARY KEY,
        session_key VARCHAR(100) UNIQUE NOT NULL,
        whatsapp_number VARCHAR(20) NOT NULL,
        session_id VARCHAR(50) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        rolling_summary TEXT,
        current_turn_count INTEGER DEFAULT 0,
        total_tokens_used INTEGER DEFAULT 0,
        config_id INTEGER
    );
    """)
    
    # Tabela conversation_turns
    create_turns_table = text("""
    CREATE TABLE IF NOT EXISTS conversation_turns (
        id SERIAL PRIMARY KEY,
        session_key VARCHAR(100) NOT NULL,
        turn_number INTEGER NOT NULL,
        role VARCHAR(10) NOT NULL,
        content TEXT NOT NULL,
        tokens_used INTEGER,
        rag_citations JSONB,
        rag_collection VARCHAR(100),
        rag_query TEXT,
        correlation_id VARCHAR(100),
        latency_ms INTEGER,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """)
    
    # Tabela user_memories
    create_memories_table = text("""
    CREATE TABLE IF NOT EXISTS user_memories (
        id SERIAL PRIMARY KEY,
        whatsapp_number VARCHAR(20) NOT NULL,
        memory_type VARCHAR(50) NOT NULL,
        memory_value TEXT NOT NULL,
        confidence FLOAT,
        source_turn_id INTEGER,
        opt_in_status BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        expires_at TIMESTAMP WITH TIME ZONE
    );
    """)
    
    # Tabela conversation_audit_logs
    create_audit_table = text("""
    CREATE TABLE IF NOT EXISTS conversation_audit_logs (
        id SERIAL PRIMARY KEY,
        session_key VARCHAR(100) NOT NULL,
        correlation_id VARCHAR(100) NOT NULL,
        action VARCHAR(50) NOT NULL,
        details JSONB,
        total_tokens INTEGER,
        rag_score_average FLOAT,
        latency_ms INTEGER,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """)
    
    # Executar criação das tabelas
    with engine.connect() as conn:
        print("📋 Criando tabela conversation_configs...")
        conn.execute(create_config_table)
        
        print("📋 Criando tabela conversation_sessions...")
        conn.execute(create_sessions_table)
        
        print("📋 Criando tabela conversation_turns...")
        conn.execute(create_turns_table)
        
        print("📋 Criando tabela user_memories...")
        conn.execute(create_memories_table)
        
        print("📋 Criando tabela conversation_audit_logs...")
        conn.execute(create_audit_table)
        
        conn.commit()
    
    print("🎉 TODAS AS TABELAS FORAM CRIADAS COM SUCESSO!")
    
    # Testar inserção de configuração
    print("\n🧪 Testando inserção de configuração...")
    with SessionLocal() as db:
        # Verificar se já existe
        result = db.execute(text("SELECT COUNT(*) FROM conversation_configs WHERE name = 'Teste'"))
        count = result.scalar()
        
        if count == 0:
            insert_config = text("""
            INSERT INTO conversation_configs (
                name, description, max_total_tokens, summary_tokens, 
                conversation_window_tokens, rag_context_tokens
            ) VALUES (
                'Teste', 'Configuração para testes', 1500, 200, 800, 500
            ) RETURNING id;
            """)
            
            result = db.execute(insert_config)
            config_id = result.scalar()
            db.commit()
            print(f"✅ Configuração de teste criada com ID: {config_id}")
        else:
            print("✅ Configuração de teste já existe")
    
    print("\n🎯 SISTEMA DE CONVERSAS PRONTO PARA TESTES!")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 