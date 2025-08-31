# 🤖 Sistema de Providers LLM - Neoquima Bot

Este documento explica como usar o sistema modular de providers LLM que permite trocar facilmente entre diferentes provedores de IA, sejam locais ou via API.

## 🚀 Visão Geral

O sistema foi redesenhado para ser **100% modular** e **fácil de configurar**. Agora você pode trocar entre providers sem alterar código, apenas executando um script de configuração.

## 📚 Providers Suportados

### 🏠 **Ollama (Local)**
- **Vantagens**: Sem custos, sem limites de API, total controle
- **Requisitos**: Docker rodando com Ollama
- **Modelos**: Qualquer modelo disponível no Ollama
- **Configuração**: Apenas URL e modelo

### 🌐 **OpenAI**
- **Vantagens**: Modelos de alta qualidade, API estável
- **Requisitos**: API Key da OpenAI
- **Modelos**: GPT-3.5-turbo, GPT-4, etc.
- **Configuração**: API Key + modelo

### 🌐 **Anthropic (Claude)**
- **Vantagens**: Claude é excelente para conversas, ético
- **Requisitos**: API Key da Anthropic
- **Modelos**: Claude-3-Sonnet, Claude-3-Haiku, etc.
- **Configuração**: API Key + modelo

### 🌐 **Google (Gemini)**
- **Vantagens**: Integração com ecossistema Google, boa performance
- **Requisitos**: API Key do Google
- **Modelos**: Gemini-1.5-Flash, Gemini-1.5-Pro, etc.
- **Configuração**: API Key + modelo

### 🌐 **Azure OpenAI**
- **Vantagens**: Para empresas que usam Azure, compliance
- **Requisitos**: API Key do Azure + URL do deployment
- **Modelos**: Mesmos da OpenAI, mas via Azure
- **Configuração**: API Key + URL + deployment

## 🛠️ Como Configurar

### 1. **Executar o Script de Configuração**

```bash
# Navegar para o diretório do projeto
cd /caminho/para/neoquimaBot

# Executar o script
python scripts/configure_llm.py
```

### 2. **Seguir o Menu Interativo**

O script irá:
1. ✅ Verificar conectividade com os serviços
2. 📋 Mostrar configuração atual
3. 📚 Listar providers disponíveis
4. 🎯 Permitir escolher o provider
5. 🔧 Guiar na configuração
6. ✅ Validar a configuração
7. 💾 Salvar no banco de dados

### 3. **Exemplo de Configuração OpenAI**

```
🎯 Escolha uma opção (1-6): 2

🔧 Configurando OpenAI
----------------------------------------
🔑 API Key da OpenAI: sk-...abc123
📝 Modelo (ex: gpt-3.5-turbo, gpt-4): gpt-4
🌐 URL base (Enter para padrão): 
🌡️ Temperatura (0.0-2.0, Enter para 0.7): 0.8
🔢 Máximo de tokens (Enter para 1000): 1500

📋 Configuração criada:
{
  "provider": "openai",
  "model": "gpt-4",
  "api_key": "sk-...abc123",
  "base_url": "https://api.openai.com/v1",
  "temperature": 0.8,
  "max_tokens": 1500,
  "context_window": 4096,
  "rag_enabled": true,
  "default_rag_collection": "neoquima"
}

✅ Confirmar e salvar? (s/N): s
✅ Configuração válida!
✅ Configuração salva com sucesso!
🎉 Configuração aplicada com sucesso!
🔄 Reinicie o LLM Service para aplicar as mudanças.
```

## 🔄 Como Trocar de Provider

### **Método 1: Script Interativo (Recomendado)**
```bash
python scripts/configure_llm.py
```

### **Método 2: API Direta**
```bash
# Listar providers disponíveis
curl http://localhost:8003/api/providers

# Obter configuração atual
curl http://localhost:8003/api/config

# Validar nova configuração
curl -X POST http://localhost:8003/api/providers/validate \
  -H "Content-Type: application/json" \
  -d '{"provider":"openai","model":"gpt-4","api_key":"sua-key"}'
```

### **Método 3: Via Admin UI**
- Acesse: `http://localhost:8080`
- Navegue para configurações LLM
- Altere o provider e salve

## 🏗️ Arquitetura Técnica

### **Estrutura de Arquivos**
```
services/llm-service/
├── providers/
│   ├── __init__.py          # Inicialização dos providers
│   ├── base.py              # Classe base abstrata
│   ├── factory.py            # Factory para criar providers
│   ├── ollama_provider.py    # Provider Ollama
│   ├── openai_provider.py    # Provider OpenAI
│   ├── anthropic_provider.py # Provider Anthropic
│   ├── google_provider.py    # Provider Google
│   └── azure_openai_provider.py # Provider Azure OpenAI
├── app.py                    # API principal (atualizada)
└── requirements.txt          # Dependências
```

### **Fluxo de Funcionamento**
1. **ConversationHandler** envia mensagem para **LLM Service**
2. **LLM Service** busca configuração no banco
3. **ProviderFactory** cria provider correto
4. **Provider** processa mensagem e retorna resposta
5. **Resposta** é enviada de volta via WhatsApp

## 🔧 Configurações Avançadas

### **Variáveis de Ambiente**
```bash
# URLs dos serviços
SHARED_DATABASE_URL=http://shared-database-api:8000
LLM_SERVICE_PORT=8003

# Para providers específicos
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_BASE_URL=https://...
```

### **Configurações por Provider**

#### **Ollama**
```json
{
  "provider": "ollama",
  "model": "llama2:3b",
  "base_url": "http://ollama:11434",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

#### **OpenAI**
```json
{
  "provider": "openai",
  "model": "gpt-4",
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

#### **Anthropic**
```json
{
  "provider": "anthropic",
  "model": "claude-3-sonnet-20240229",
  "api_key": "sk-ant-...",
  "base_url": "https://api.anthropic.com/v1",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

## 🚨 Troubleshooting

### **Problema: Provider não reconhecido**
```bash
# Verificar se o provider está na lista
curl http://localhost:8003/api/providers

# Verificar logs do LLM Service
docker logs neoquima-llm-service
```

### **Problema: API Key inválida**
```bash
# Validar configuração
curl -X POST http://localhost:8003/api/providers/validate \
  -H "Content-Type: application/json" \
  -d '{"provider":"openai","api_key":"sua-key"}'
```

### **Problema: Serviço não responde**
```bash
# Verificar saúde do serviço
curl http://localhost:8003/health

# Verificar se está rodando
docker ps | grep llm-service
```

## 📊 Monitoramento

### **Health Check**
```bash
curl http://localhost:8003/health
```

### **Status dos Providers**
```bash
# Listar todos os providers
curl http://localhost:8003/api/providers

# Info de um provider específico
curl http://localhost:8003/api/providers/openai
```

### **Logs em Tempo Real**
```bash
# Logs do LLM Service
docker logs -f neoquima-llm-service

# Logs do WhatsApp Gateway
docker logs -f infra-whatsapp-gateway-1
```

## 🔮 Próximos Passos

### **Providers Planejados**
- [ ] **Hugging Face** (modelos locais e remotos)
- [ ] **Cohere** (modelos empresariais)
- [ **Mistral AI** (modelos open source)
- [ ] **Perplexity** (modelos de busca)
- [ ] **Custom Provider** (para modelos próprios)

### **Funcionalidades Futuras**
- [ ] **A/B Testing** entre providers
- [ ] **Fallback automático** se um provider falhar
- [ ] **Load balancing** entre múltiplos providers
- [ ] **Métricas de performance** por provider
- [ ] **Cache inteligente** de respostas

## 💡 Dicas de Uso

### **Para Desenvolvimento**
- Use **Ollama** para testes e desenvolvimento
- Sem custos, sem limites de API
- Fácil de debugar e testar

### **Para Produção**
- Use **OpenAI** ou **Claude** para qualidade
- Configure **fallback** para Ollama
- Monitore custos e performance

### **Para Empresas**
- Use **Azure OpenAI** para compliance
- Configure **rate limiting** adequado
- Implemente **audit logs** completos

## 🤝 Suporte

### **Comunidade**
- Issues no GitHub
- Discussões no Discord
- Documentação colaborativa

### **Desenvolvimento**
- Pull requests bem-vindos
- Testes para novos providers
- Melhorias na documentação

---

**🎉 Agora você pode trocar entre qualquer provider LLM com apenas alguns cliques!**

**🚀 O sistema é totalmente modular e extensível para suas necessidades.** 