#!/bin/bash

echo "🚀 Configurador Rápido de Webhook WhatsApp"
echo "=========================================="

# Verificar ngrok
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok não encontrado!"
    echo "📥 Instale: https://ngrok.com/download"
    exit 1
fi

# Verificar se o serviço está rodando
if ! curl -s http://localhost:8081/health &> /dev/null; then
    echo "⚠️  Serviço não está rodando. Iniciando..."
    docker compose -f infra/compose.yml --env-file infra/.env up -d --build
    echo "⏳ Aguardando serviço ficar pronto..."
    sleep 10
fi

echo "✅ Serviço rodando em http://localhost:8081"

# Iniciar ngrok
echo "🌐 Iniciando ngrok..."
ngrok http 8081 > /dev/null 2>&1 &
sleep 5

# Obter URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null)

if [ -z "$NGROK_URL" ] || [ "$NGROK_URL" = "null" ]; then
    echo "❌ Erro ao obter URL do ngrok"
    exit 1
fi

echo ""
echo "🎉 ngrok configurado!"
echo "🌐 URL: $NGROK_URL"
echo ""
echo "📋 CONFIGURAR NO FACEBOOK:"
echo "1️⃣ Acesse: https://developers.facebook.com/apps/1559477822095103/whatsapp-business/wa-settings/?business_id=130384357976670"
echo "2️⃣ Webhook URL: $NGROK_URL/webhook"
echo "3️⃣ Verify Token: neoquima_webhook_2024"
echo "4️⃣ Campos: messages, message_deliveries"
echo ""
echo "🧪 Testando webhook..."
curl -s "$NGROK_URL/webhook?hub.mode=subscribe&hub.verify_token=neoquima_webhook_2024&hub.challenge=123"
echo ""
echo "📱 Teste enviando mensagem no WhatsApp!"
echo "🛑 Para parar: pkill ngrok"
echo "🌐 Interface: http://localhost:4040" 