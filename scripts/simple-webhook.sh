#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setup Simples do Webhook WhatsApp${NC}"
echo -e "${BLUE}===============================${NC}\n"

# Verificar se o ngrok está instalado
if ! command -v ngrok &> /dev/null; then
    echo -e "${YELLOW}❌ ngrok não encontrado!${NC}"
    echo -e "${YELLOW}📥 Instale: snap install ngrok (Ubuntu)${NC}"
    exit 1
fi

# Verificar se o WhatsApp Gateway está rodando
echo -e "${BLUE}🔍 Verificando WhatsApp Gateway...${NC}"
if ! curl -s http://localhost:8081/health &> /dev/null; then
    echo -e "${YELLOW}⚠️  WhatsApp Gateway não está rodando${NC}"
    echo -e "${YELLOW}🚀 Inicie primeiro: docker compose -f infra/compose.yml up -d${NC}"
    exit 1
fi

echo -e "${GREEN}✅ WhatsApp Gateway rodando!${NC}\n"

# Iniciar ngrok
echo -e "${BLUE}🌐 Iniciando ngrok...${NC}"
ngrok http 8081 > /dev/null 2>&1 &

# Aguardar ngrok inicializar
echo -e "${YELLOW}⏳ Aguardando ngrok...${NC}"
sleep 3

# Obter URL do ngrok
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null)

if [ -z "$NGROK_URL" ] || [ "$NGROK_URL" = "null" ]; then
    echo -e "${YELLOW}⏳ Aguardando mais um pouco...${NC}"
    sleep 3
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null)
fi

if [ -z "$NGROK_URL" ] || [ "$NGROK_URL" = "null" ]; then
    echo -e "${YELLOW}❌ Não foi possível obter a URL do ngrok${NC}"
    echo -e "${YELLOW}💡 Verifique: http://localhost:4040${NC}"
    exit 1
fi

echo -e "\n${GREEN}🎉 ngrok configurado!${NC}"
echo -e "${BLUE}🌐 URL Pública: ${GREEN}$NGROK_URL${NC}"
echo -e "${BLUE}🔗 Webhook URL: ${GREEN}$NGROK_URL/webhook${NC}\n"

# Mostrar configuração
echo -e "${YELLOW}📋 CONFIGURAÇÃO NO FACEBOOK:${NC}"
echo -e "${BLUE}===============================${NC}"
echo -e "${GREEN}Webhook URL:${NC} $NGROK_URL/webhook"
echo -e "${GREEN}Verify Token:${NC} neoquima_webhook_2024"
echo -e "${GREEN}Campos:${NC} messages, message_deliveries\n"

# Abrir Facebook Developers
echo -e "${BLUE}🌐 Abrindo Facebook Developers...${NC}"
xdg-open "https://developers.facebook.com/apps/1559477822095103/whatsapp-business/wa-settings/?business_id=130384357976670" 2>/dev/null || \
firefox "https://developers.facebook.com/apps/1559477822095103/whatsapp-business/wa-settings/?business_id=130384357976670" 2>/dev/null || \
google-chrome "https://developers.facebook.com/apps/1559477822095103/whatsapp-business/wa-settings/?business_id=130384357976670" 2>/dev/null || \
echo -e "${YELLOW}💡 Abra manualmente: https://developers.facebook.com/apps/1559477822095103/whatsapp-business/wa-settings/?business_id=130384357976670${NC}"

echo -e "\n${GREEN}✅ Pronto! Cole o link do webhook no Facebook:${NC}"
echo -e "${BLUE}$NGROK_URL/webhook${NC}\n"

echo -e "${BLUE}🛑 Para parar: Ctrl+C${NC}"
echo -e "${BLUE}🌐 Interface ngrok: http://localhost:4040${NC}\n"

# Manter rodando
while true; do
    sleep 1
done 