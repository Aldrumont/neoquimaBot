# Neoquima – WhatsApp Gateway

## 📋 Descrição
Gateway para WhatsApp que gerencia usuários, autenticação e roteamento de mensagens para módulos LLM.

## 🏗️ Arquitetura
- **WhatsApp Gateway**: Recebe mensagens, valida usuários, roteia para LLM
- **PostgreSQL**: Banco de dados para gestão de usuários
- **Módulo LLM**: Processa mensagens e retorna respostas (futuro)

## 🚀 Funcionalidades

### ✅ Implementado
- [x] Webhook de verificação do WhatsApp
- [x] CRUD completo de usuários
- [x] Sistema de expiração automática
- [x] Autenticação via admin token
- [x] Validação de números E.164
- [x] Rastreamento de interações
- [x] Sistema de tags e roles
- [x] Envio de mensagens de resposta
- [x] Modo de teste integrado

### 🔄 Fluxo de Mensagens
1. **Recebe** mensagem do WhatsApp
2. **Valida** usuário no banco
3. **Identifica** se é mensagem de teste
4. **Roteia** para LLM ou retorna resposta de teste
5. **Envia** resposta de volta para o usuário

## 📡 Endpoints

### Webhook
- `GET /webhook` - Verificação do WhatsApp
- `POST /webhook` - Recebimento de mensagens

### Usuários
- `GET /admin/users` - Listar usuários
- `POST /admin/users` - Criar usuário
- `GET /admin/users/{id}` - Obter usuário
- `PUT /admin/users/{id}` - Atualizar usuário
- `DELETE /admin/users/{id}` - Deletar usuário
- `PATCH /admin/users/{id}/deactivate` - Desativar usuário

### Expiração
- `GET /admin/users/expired` - Usuários expirados
- `GET /admin/users/expiring-soon` - Usuários expirando em breve
- `POST /admin/users/deactivate-expired` - Desativar expirados automaticamente

### Estatísticas
- `GET /admin/users/stats` - Estatísticas gerais
- `GET /health` - Status de saúde

## 🔧 Configuração

### Variáveis de Ambiente

**⚠️ IMPORTANTE**: Nunca commite tokens reais no repositório!

1. **Copie o arquivo de exemplo:**
```bash
cp infra/env.example infra/.env
```

2. **Edite o arquivo `.env` com suas credenciais:**
```bash
# WhatsApp Business API
WHATSAPP_TOKEN=seu_token_whatsapp_aqui
WHATSAPP_PHONE_ID=seu_phone_id_aqui

# Admin Authentication  
ADMIN_TOKEN=seu_token_admin_aqui

# Webhook Verification
VERIFY_TOKEN=seu_verify_token_aqui

# Database (opcional, já configurado no compose)
DATABASE_URL=postgresql://user:pass@host:port/db
```

3. **O arquivo `.env` já está no .gitignore para segurança**

### Docker Compose

**Com variáveis de ambiente:**
```bash
# Usando arquivo .env (recomendado)
docker compose -f infra/compose.yml --env-file infra/.env up -d --build

# Ou exportando variáveis manualmente
export WHATSAPP_TOKEN="seu_token"
export ADMIN_TOKEN="seu_admin_token"
docker compose -f infra/compose.yml up -d --build
```

## 🧪 Modo de Teste

### Como Ativar
Envie uma mensagem contendo qualquer um destes termos:
- `🧪` (emoji de tubo de ensaio)
- `teste`
- `TESTE`
- `test`

### Resposta de Teste
```
🧪 TESTE EXECUTADO

📱 Número: +5511999998888
💬 Mensagem: "oi teste"
📊 Cadastro no banco:
   • ID: 1
   • Nome: João Silva
   • Empresa: Tech Corp
   • Status: Ativo
   • Última interação: 2025-08-22T19:08:45Z
   • Contador: 1
```

## 📊 Modelo de Dados

### Usuário
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    company VARCHAR(100),
    note TEXT,
    added_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    last_interact TIMESTAMP WITH TIME ZONE,
    interact_count INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    role VARCHAR(50) DEFAULT 'user',
    status_reason TEXT,
    tags JSON DEFAULT '[]'
);
```

## 🔐 Autenticação

### Admin Token
Use o header `X-Admin-Token` para endpoints administrativos.

### Exemplo
```bash
curl -H 'X-Admin-Token: seu_token_aqui' \
     http://localhost:8081/admin/users
```

## 📝 Contratos de API

### Mensagem Recebida (Webhook)
```json
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "+5511999998888",
          "text": {"body": "mensagem do usuário"}
        }]
      }
    }]
  }]
}
```

### Resposta de Sucesso
```json
{
  "status": "accepted",
  "user_id": 1,
  "message_sent": true
}
```

### Resposta de Bloqueio
```json
{
  "status": "blocked",
  "reason": "user_not_found|user_inactive|user_expired",
  "message_sent": true
}
```

## 🚀 Desenvolvimento

### Estrutura de Arquivos
```
services/whatsapp-gateway/
├── app.py                 # Aplicação principal
├── database/             # Camada de dados
│   ├── config.py        # Configuração do banco
│   ├── models.py        # Modelos SQLAlchemy
│   ├── schemas.py       # Schemas Pydantic
│   └── crud.py          # Operações CRUD
├── requirements.txt      # Dependências Python
└── Dockerfile           # Containerização
```

### Comandos Úteis
```bash
# Reconstruir container
docker compose -f infra/compose.yml up -d --build

# Ver logs
docker logs infra-whatsapp-gateway-1

# Acessar banco
docker exec -it infra-postgres-1 psql -U neoquima_user -d neoquima_bot
```

## 🔮 Próximos Passos
- [ ] Integração com módulo LLM
- [ ] Sistema de templates de mensagens
- [ ] Dashboard administrativo
- [ ] Métricas e analytics
- [ ] Sistema de notificações
