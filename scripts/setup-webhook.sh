#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Configurador Automatizado de Webhook WhatsApp${NC}"
echo -e "${BLUE}===============================================${NC}\n"

# Verificar se o ngrok está instalado
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}❌ ngrok não encontrado!${NC}"
    echo -e "${YELLOW}📥 Instale o ngrok em: https://ngrok.com/download${NC}"
    echo -e "${YELLOW}💡 Ou use: snap install ngrok (Ubuntu)${NC}"
    exit 1
fi

# Verificar se o Docker está rodando
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker não está rodando!${NC}"
    echo -e "${YELLOW}🚀 Inicie o Docker primeiro${NC}"
    exit 1
fi

# Verificar se o serviço está rodando
if ! curl -s http://localhost:8081/health &> /dev/null; then
    echo -e "${YELLOW}⚠️  Serviço WhatsApp Gateway não está rodando${NC}"
    echo -e "${BLUE}🚀 Iniciando serviços...${NC}"
    
    # Iniciar os serviços
    docker compose -f infra/compose.yml --env-file infra/.env up -d --build
    
    # Aguardar o serviço estar pronto
    echo -e "${YELLOW}⏳ Aguardando serviço ficar pronto...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8081/health &> /dev/null; then
            echo -e "${GREEN}✅ Serviço pronto!${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    if ! curl -s http://localhost:8081/health &> /dev/null; then
        echo -e "\n${RED}❌ Serviço não iniciou em tempo hábil${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Serviço WhatsApp Gateway rodando em http://localhost:8081${NC}\n"

# Iniciar ngrok em background
echo -e "${BLUE}🌐 Iniciando ngrok para porta 8081...${NC}"
ngrok http 8081 > /dev/null 2>&1 &

# Aguardar ngrok inicializar
echo -e "${YELLOW}⏳ Aguardando ngrok inicializar...${NC}"
sleep 5

# Obter URL do ngrok
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null)

if [ -z "$NGROK_URL" ] || [ "$NGROK_URL" = "null" ]; then
    echo -e "${RED}❌ Não foi possível obter a URL do ngrok${NC}"
    echo -e "${YELLOW}💡 Verifique se o ngrok está rodando em http://localhost:4040${NC}"
    exit 1
fi

echo -e "\n${GREEN}🎉 ngrok configurado com sucesso!${NC}"
echo -e "${BLUE}🌐 URL Pública: ${GREEN}$NGROK_URL${NC}"
echo -e "${BLUE}🔗 URL Local: ${GREEN}http://localhost:8081${NC}\n"

# Mostrar informações para configuração
echo -e "${YELLOW}📋 CONFIGURAÇÃO DO WEBHOOK NO FACEBOOK:${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}1️⃣ Acesse:${NC} https://developers.facebook.com/apps/1559477822095103/whatsapp-business/wa-settings/?business_id=130384357976670"
echo -e "${GREEN}2️⃣ Configure o Webhook URL:${NC} $NGROK_URL/webhook"
echo -e "${GREEN}3️⃣ Verify Token:${NC} neoquima_webhook_2024"
echo -e "${GREEN}4️⃣ Selecione os campos:${NC} messages, message_deliveries"
echo -e "\n"

# Testar webhook
echo -e "${BLUE}🧪 Testando webhook...${NC}"
WEBHOOK_TEST=$(curl -s "$NGROK_URL/webhook?hub.mode=subscribe&hub.verify_token=neoquima_webhook_2024&hub.challenge=123")

if [ "$WEBHOOK_TEST" = "123" ]; then
    echo -e "${GREEN}✅ Webhook funcionando perfeitamente!${NC}"
else
    echo -e "${RED}❌ Webhook com problema: $WEBHOOK_TEST${NC}"
fi

echo -e "\n${BLUE}📱 AGORA TESTE ENVIANDO UMA MENSAGEM NO WHATSAPP!${NC}"
echo -e "${YELLOW}💡 O webhook receberá a mensagem em: $NGROK_URL/webhook${NC}"
echo -e "\n${BLUE}🛑 Para parar: Ctrl+C${NC}"
echo -e "${BLUE}🔍 Para ver logs: docker logs whatsapp-gateway-1${NC}"
echo -e "${BLUE}🌐 Interface ngrok: http://localhost:4040${NC}\n"

# Manter script rodando e mostrar logs
echo -e "${YELLOW}📊 Mostrando logs em tempo real...${NC}"
echo -e "${BLUE}===============================================${NC}"

# Função para limpar ao sair
cleanup() {
    echo -e "\n${YELLOW}🛑 Parando ngrok...${NC}"
    pkill ngrok
    echo -e "${GREEN}✅ ngrok parado. Webhook desabilitado.${NC}"
    exit 0
}

trap cleanup SIGINT

# Mostrar logs em tempo real
docker logs -f whatsapp-gateway-1 