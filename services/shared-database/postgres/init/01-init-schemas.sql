-- =====================================================
-- Inicialização dos Schemas do Banco Compartilhado
-- =====================================================

-- Criar schemas para cada módulo
CREATE SCHEMA IF NOT EXISTS whatsapp;
CREATE SCHEMA IF NOT EXISTS llm;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS auth;

-- Schema público para tabelas compartilhadas
CREATE SCHEMA IF NOT EXISTS public;

-- Configurar permissões
GRANT USAGE ON SCHEMA whatsapp TO neoquima_admin;
GRANT USAGE ON SCHEMA llm TO neoquima_admin;
GRANT USAGE ON SCHEMA analytics TO neoquima_admin;
GRANT USAGE ON SCHEMA auth TO neoquima_admin;
GRANT USAGE ON SCHEMA public TO neoquima_admin;

-- Dar permissões de criação nas tabelas
GRANT CREATE ON SCHEMA whatsapp TO neoquima_admin;
GRANT CREATE ON SCHEMA llm TO neoquima_admin;
GRANT CREATE ON SCHEMA analytics TO neoquima_admin;
GRANT CREATE ON SCHEMA auth TO neoquima_admin;
GRANT CREATE ON SCHEMA public TO neoquima_admin;

-- Configurar search_path padrão
ALTER DATABASE neoquima_shared SET search_path TO public, whatsapp, llm, analytics, auth;

-- Comentários para documentação
COMMENT ON SCHEMA whatsapp IS 'Schema para módulo WhatsApp Gateway - usuários, mensagens, webhooks';
COMMENT ON SCHEMA llm IS 'Schema para módulo LLM - conversas, contexto, histórico';
COMMENT ON SCHEMA analytics IS 'Schema para analytics - métricas, logs, relatórios';
COMMENT ON SCHEMA auth IS 'Schema para autenticação - usuários, permissões, tokens';
COMMENT ON SCHEMA public IS 'Schema público - tabelas compartilhadas entre módulos';

-- Criar extensões úteis
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Criar tabela de log de inicialização
CREATE TABLE IF NOT EXISTS public.schema_init_log (
    id SERIAL PRIMARY KEY,
    schema_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'created'
);

-- Log de inicialização
INSERT INTO public.schema_init_log (schema_name, created_at, status) VALUES 
('whatsapp', NOW(), 'created'),
('llm', NOW(), 'created'),
('analytics', NOW(), 'created'),
('auth', NOW(), 'created'),
('public', NOW(), 'created')
ON CONFLICT DO NOTHING; 