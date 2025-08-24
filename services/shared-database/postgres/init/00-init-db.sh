#!/bin/bash

# =====================================================
# Script de Inicialização do Banco Compartilhado
# =====================================================

set -e

# Variáveis do banco
DB_NAME="neoquima_shared"
DB_USER="neoquima_admin"
DB_PASS="neoquima_admin_pass_2024"

echo "🚀 Inicializando banco compartilhado..."

# Criar banco se não existir
echo "📊 Criando banco de dados..."
createdb -U "$POSTGRES_USER" "$DB_NAME" 2>/dev/null || echo "Banco já existe"

# Conectar ao banco criado
echo "🔗 Conectando ao banco..."
export PGPASSWORD="$DB_PASS"

# Executar script de schemas
echo "🏗️ Criando schemas..."
psql -U "$DB_USER" -d "$DB_NAME" -f /docker-entrypoint-initdb.d/01-init-schemas.sql

echo "✅ Banco compartilhado inicializado com sucesso!"
echo "📋 Schemas criados:"
echo "   - whatsapp (usuários, mensagens)"
echo "   - llm (conversas, contexto)"
echo "   - analytics (métricas, logs)"
echo "   - auth (autenticação)"
echo "   - public (compartilhado)"

# Verificar schemas criados
echo "🔍 Verificando schemas..."
psql -U "$DB_USER" -d "$DB_NAME" -c "\dn+" 