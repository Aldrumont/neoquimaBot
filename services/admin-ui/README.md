# Neoquima Admin UI

Interface web para administração do sistema Neoquima, permitindo gerenciar usuários permitidos e futuramente configurar parâmetros do LLM, prompts e dashboards.

## 🚀 Funcionalidades

### ✅ Implementado
- **Dashboard** com estatísticas do sistema
- **Gerenciamento de Usuários** (CRUD completo)
  - Criar novos usuários
  - Editar usuários existentes
  - Deletar usuários
  - Buscar e filtrar usuários
  - Visualizar status e informações

### 🔮 Em Desenvolvimento
- **Configuração de LLM** (parâmetros, modelos)
- **Gerenciamento de Prompts** (templates, variáveis)
- **Dashboards Analytics** (métricas, relatórios)
- **Configurações do Sistema** (webhooks, tokens)

## 🏗️ Arquitetura

- **Frontend**: HTML5 + Bootstrap 5 + JavaScript ES6+
- **Backend**: Flask (Python)
- **API**: RESTful com integração à API compartilhada
- **Containerização**: Docker com health checks

## 📁 Estrutura do Projeto

```
admin-ui/
├── app.py                 # Aplicação Flask principal
├── requirements.txt       # Dependências Python
├── Dockerfile            # Containerização
├── static/               # Arquivos estáticos
│   ├── css/
│   │   └── style.css     # CSS personalizado
│   └── js/
│       ├── dashboard.js  # JavaScript do dashboard
│       └── users.js      # JavaScript de usuários
└── templates/            # Templates HTML
    ├── index.html        # Dashboard principal
    └── users.html        # Gerenciamento de usuários
```

## 🚀 Como Executar

### Opção 1: Docker Compose (Recomendado)
```bash
# Na raiz do projeto
docker compose -f infra/compose.yml up -d
```

### Opção 2: Local
```bash
cd services/admin-ui
pip install -r requirements.txt
python app.py
```

## 🌐 Acesso

- **URL**: http://localhost:8080
- **Dashboard**: http://localhost:8080/
- **Usuários**: http://localhost:8080/users
- **Health Check**: http://localhost:8080/health

## 🔌 Integração

### API Compartilhada
- **URL**: Configurada via `SHARED_DATABASE_URL`
- **Endpoints**: `/api/v1/whatsapp/users`
- **Autenticação**: Futuramente implementada

### WhatsApp Gateway
- **Status**: Monitorado via health check
- **Webhook**: Status verificado via ngrok

## 🎨 Interface

### Design System
- **Framework**: Bootstrap 5.3.0
- **Ícones**: Bootstrap Icons 1.10.0
- **Tema**: Customizado com CSS personalizado
- **Responsivo**: Mobile-first design

### Componentes
- **Navbar**: Navegação principal com status online
- **Cards**: Estatísticas e informações do sistema
- **Tabelas**: Lista de usuários com ações
- **Modais**: Formulários de criação/edição
- **Toasts**: Notificações do sistema

## 🔧 Configuração

### Variáveis de Ambiente
```bash
ADMIN_UI_PORT=8080                    # Porta do Admin UI
SHARED_DATABASE_URL=http://localhost:8000  # URL da API compartilhada
SECRET_KEY=admin-secret-key-2024      # Chave secreta do Flask
DEBUG=false                           # Modo debug
```

### Portas
- **8080**: Admin UI (padrão)
- **8000**: API Compartilhada
- **8081**: WhatsApp Gateway
- **5433**: PostgreSQL

## 📱 Funcionalidades da Interface

### Dashboard
- Contador de usuários ativos
- Status dos serviços
- Status do webhook ngrok
- Atualização automática a cada 30s

### Gerenciamento de Usuários
- **Listagem**: Tabela com paginação e filtros
- **Busca**: Por nome, número ou empresa
- **Filtros**: Por status (ativo/inativo)
- **CRUD**: Criar, ler, atualizar, deletar
- **Validação**: Formato internacional de telefone

### Formulários
- **Validação**: Campos obrigatórios
- **Formato**: Número com + (ex: +5511999999999)
- **Campos**: Nome, número, empresa, observação, status

## 🧪 Testes

### Funcionalidades Testadas
- ✅ Criação de usuários
- ✅ Edição de usuários
- ✅ Exclusão de usuários
- ✅ Filtros e busca
- ✅ Validação de formulários
- ✅ Integração com API

### Como Testar
1. Acesse http://localhost:8080
2. Vá para "Usuários"
3. Teste criar, editar e deletar usuários
4. Use os filtros de busca
5. Verifique as notificações toast

## 🔮 Roadmap

### Versão 1.1
- [ ] Autenticação e autorização
- [ ] Logs de auditoria
- [ ] Exportação de dados

### Versão 1.2
- [ ] Configuração de LLM
- [ ] Gerenciamento de prompts
- [ ] Templates de mensagens

### Versão 1.3
- [ ] Dashboards analytics
- [ ] Relatórios em PDF
- [ ] Integração com webhooks

## 🐛 Troubleshooting

### Problemas Comuns
1. **Erro de conexão com API**: Verifique se a API compartilhada está rodando
2. **Usuário não criado**: Verifique o formato do número (+5511999999999)
3. **Interface não carrega**: Verifique se o Admin UI está rodando na porta 8080

### Logs
```bash
# Ver logs do Admin UI
docker logs infra-admin-ui-1

# Ver logs da API compartilhada
docker logs shared-database-api
```

## 📄 Licença

Projeto interno Neoquima - 2024 