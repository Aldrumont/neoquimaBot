# 🗄️ Shared Database Module

Módulo compartilhado de banco de dados PostgreSQL com API REST para uso por todos os módulos do sistema.

## 🏗️ Arquitetura

```
Banco: neoquima_shared
├── 📊 Schema: public (tabelas compartilhadas)
├── 📱 Schema: whatsapp (usuários, mensagens)
├── 🤖 Schema: llm (conversas, contexto)
├── 📈 Schema: analytics (métricas, logs)
└── 🔐 Schema: auth (autenticação, permissões)
```

## 🚀 Funcionalidades

- **🗄️ PostgreSQL 15**: Banco de dados robusto e escalável
- **🌐 API REST**: Interface HTTP para acesso aos dados
- **🔐 Autenticação**: Sistema de tokens JWT
- **📊 Schemas Múltiplos**: Organização por módulo
- **🐳 Docker**: Containerização completa
- **🏥 Health Checks**: Monitoramento de saúde

## 🎯 Casos de Uso

- **WhatsApp Gateway**: Gestão de usuários e mensagens
- **LLM Module**: Histórico de conversas e contexto
- **Analytics**: Métricas e relatórios
- **Admin Panel**: Interface administrativa

## 🛠️ Tecnologias

- **Backend**: FastAPI + Python 3.11
- **Database**: PostgreSQL 15 + SQLAlchemy 2.0
- **ORM**: SQLAlchemy + Alembic
- **Auth**: JWT + Passlib
- **Container**: Docker + Docker Compose

## 📋 Status de Implementação

1. **✅ Estrutura de Pastas** - Criada
2. **✅ Docker Compose** - Integrado na infra
3. **✅ Scripts de Inicialização** - Criados
4. **✅ API Core** - Criada
5. **✅ Configuração Banco** - Criada
6. **⏳ Modelos de Dados** - Próximo
7. **⏳ Endpoints CRUD** - Próximo
8. **⏳ Autenticação** - Próximo

## 🚀 Como Usar

### 1. Iniciar Serviços
```bash
# Na pasta raiz do projeto
docker compose -f infra/compose.yml up -d --build
```

### 2. Acessar API
```bash
# Health check
curl http://localhost:8000/health

# Listar schemas
curl http://localhost:8000/schemas

# Documentação
open http://localhost:8000/docs
```

### 3. Acessar Banco
```bash
# Conectar ao PostgreSQL
docker exec -it shared-postgres psql -U neoquima_admin -d neoquima_shared

# Listar schemas
\dn+

# Ver tabelas de um schema
\dt whatsapp.*
```

## 🔗 Portas

- **API**: 8000
- **PostgreSQL**: 5433
- **Interface**: http://localhost:8000/docs

## 📚 Documentação da API

Acesse http://localhost:8000/docs para ver a documentação interativa da API.

## 🎯 Próximos Passos

1. **Criar modelos** para cada schema
2. **Implementar endpoints** CRUD
3. **Sistema de autenticação** JWT
4. **Migrações** Alembic
5. **Testes** automatizados 