# 🚀 Scripts de Configuração Automática do Webhook

Scripts para automatizar a configuração do ngrok e orientar a configuração do webhook no Facebook.

## 📁 Arquivos Disponíveis

### 🐧 Linux/Mac
- **`setup-webhook.sh`** - Script completo com verificações e logs em tempo real
- **`setup-webhook-simple.sh`** - Versão simplificada e rápida

### 🪟 Windows
- **`setup-webhook.ps1`** - Script PowerShell completo

## 🚀 Como Usar

### Linux/Mac
```bash
# Versão completa (recomendada)
./scripts/setup-webhook.sh

# Versão rápida
./scripts/setup-webhook-simple.sh
```

### Windows (PowerShell)
```powershell
# Executar como administrador
.\scripts\setup-webhook.ps1
```

## ✨ O que os Scripts Fazem

1. **🔍 Verificações Automáticas**
   - ngrok instalado
   - Docker rodando
   - Serviço WhatsApp Gateway ativo

2. **🚀 Inicialização Automática**
   - Inicia serviços se necessário
   - Configura ngrok para porta 8081
   - Obtém URL pública automaticamente

3. **📋 Orientações de Configuração**
   - Mostra exatamente o que configurar no Facebook
   - Testa o webhook automaticamente
   - Fornece todas as informações necessárias

4. **📊 Monitoramento**
   - Logs em tempo real
   - Interface ngrok disponível
   - Status do webhook

## 🎯 Passos Após Executar o Script

1. **📱 Acesse o Facebook Developers**
   - Link direto fornecido pelo script
   - Vá em WhatsApp > Webhook

2. **🔗 Configure o Webhook**
   - **URL**: `https://seu-ngrok.ngrok.io/webhook`
   - **Verify Token**: `neoquima_webhook_2024`
   - **Campos**: `messages`, `message_deliveries`

3. **✅ Teste**
   - Envie uma mensagem no WhatsApp
   - Verifique os logs em tempo real

## 🛠️ Comandos Úteis

```bash
# Parar ngrok
pkill ngrok

# Ver logs do serviço
docker logs whatsapp-gateway-1

# Interface do ngrok
open http://localhost:4040

# Status do serviço
curl http://localhost:8081/health
```

## 🔧 Solução de Problemas

### ngrok não encontrado
```bash
# Ubuntu/Debian
snap install ngrok

# macOS
brew install ngrok

# Windows
winget install ngrok
```

### Porta 8081 ocupada
```bash
# Verificar o que está usando a porta
lsof -i :8081

# Parar processo
kill -9 <PID>
```

### Docker não rodando
```bash
# Iniciar Docker
sudo systemctl start docker

# Verificar status
sudo systemctl status docker
```

## 📱 Testando o Webhook

Após configurar no Facebook:

1. **Envie uma mensagem** para o número do WhatsApp Business
2. **Verifique os logs** em tempo real
3. **Confirme** que a mensagem foi recebida

## 🎉 Pronto!

Seu webhook estará funcionando e recebendo mensagens do WhatsApp em tempo real! 