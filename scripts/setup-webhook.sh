#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Configurador Automatizado de Webhook WhatsApp${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "${YELLOW}🏗️  Arquitetura: WhatsApp Gateway + API Compartilhada + Banco PostgreSQL${NC}\n"

# Verificar se o ngrok está instalado
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}❌ ngrok não encontrado!${NC}"
    echo -e "${YELLOW}📥 Instale o ngrok em: https://ngrok.com/download${NC}"
    echo -e "${YELLOW}💡 Ou use: snap install ngrok (Ubuntu)${NC}"
    exit 1
fi

# Verificar se o jq está instalado (para testes)
if ! command -v jq &> /dev/null; then
    echo -e "${RED}❌ jq não encontrado!${NC}"
    echo -e "${YELLOW}📥 Instale o jq: sudo apt install jq (Ubuntu/Debian)${NC}"
    echo -e "${YELLOW}💡 Ou use: snap install jq (Ubuntu)${NC}"
    exit 1
fi

# Verificar se o Docker está rodando
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker não está rodando!${NC}"
    echo -e "${YELLOW}🚀 Inicie o Docker primeiro${NC}"
    exit 1
fi

# Verificar se os serviços estão rodando
echo -e "${BLUE}🔍 Verificando status dos serviços...${NC}"

# Verificar WhatsApp Gateway
WHATSAPP_HEALTH=false
if curl -s http://localhost:8081/health &> /dev/null; then
    WHATSAPP_HEALTH=true
    echo -e "${GREEN}✅ WhatsApp Gateway rodando${NC}"
else
    echo -e "${YELLOW}⚠️  WhatsApp Gateway não está rodando${NC}"
fi

# Verificar API Compartilhada
SHARED_API_HEALTH=false
if curl -s http://localhost:8000/health &> /dev/null; then
    SHARED_API_HEALTH=true
    echo -e "${GREEN}✅ API Compartilhada rodando${NC}"
else
    echo -e "${YELLOW}⚠️  API Compartilhada não está rodando${NC}"
fi

# Verificar Banco Compartilhado
POSTGRES_HEALTH=false
if docker ps | grep -q "shared-postgres.*healthy"; then
    POSTGRES_HEALTH=true
    echo -e "${GREEN}✅ Banco Compartilhado rodando${NC}"
else
    echo -e "${YELLOW}⚠️  Banco Compartilhado não está rodando${NC}"
fi

# Se algum serviço não estiver rodando, iniciar todos
if [ "$WHATSAPP_HEALTH" = false ] || [ "$SHARED_API_HEALTH" = false ] || [ "$POSTGRES_HEALTH" = false ]; then
    echo -e "${BLUE}🚀 Iniciando todos os serviços...${NC}"
    
    # Iniciar os serviços
    docker compose -f infra/compose.yml --env-file infra/.env up -d --build
    
    # Aguardar os serviços ficarem prontos
    echo -e "${YELLOW}⏳ Aguardando serviços ficarem prontos...${NC}"
    
    # Aguardar banco
    echo -e "${BLUE}📊 Aguardando banco compartilhado...${NC}"
    for i in {1..30}; do
        if docker ps | grep -q "shared-postgres.*healthy"; then
            echo -e "${GREEN}✅ Banco pronto!${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Aguardar API compartilhada
    echo -e "${BLUE}🔌 Aguardando API compartilhada...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8000/health &> /dev/null; then
            echo -e "${GREEN}✅ API compartilhada pronta!${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Aguardar WhatsApp Gateway
    echo -e "${BLUE}📱 Aguardando WhatsApp Gateway...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8081/health &> /dev/null; then
            echo -e "${GREEN}✅ WhatsApp Gateway pronto!${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Verificar se todos estão funcionando
    if ! curl -s http://localhost:8081/health &> /dev/null; then
        echo -e "\n${RED}❌ WhatsApp Gateway não iniciou em tempo hábil${NC}"
        exit 1
    fi
    
    if ! curl -s http://localhost:8000/health &> /dev/null; then
        echo -e "\n${RED}❌ API Compartilhada não iniciou em tempo hábil${NC}"
        exit 1
    fi
    
    if ! docker ps | grep -q "shared-postgres.*healthy"; then
        echo -e "\n${RED}❌ Banco Compartilhado não iniciou em tempo hábil${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Todos os serviços rodando!${NC}"
echo -e "${BLUE}📱 WhatsApp Gateway: ${GREEN}http://localhost:8081${NC}"
echo -e "${BLUE}🔌 API Compartilhada: ${GREEN}http://localhost:8000${NC}"
echo -e "${BLUE}📊 Banco Compartilhado: ${GREEN}Porta 5433${NC}\n"

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

# Testar serviços
echo -e "${BLUE}🧪 Testando serviços...${NC}"

# Testar webhook
echo -e "${BLUE}📱 Testando webhook...${NC}"
WEBHOOK_TEST=$(curl -s "$NGROK_URL/webhook?hub.mode=subscribe&hub.verify_token=neoquima_webhook_2024&hub.challenge=123")

if [ "$WEBHOOK_TEST" = "123" ]; then
    echo -e "${GREEN}✅ Webhook funcionando perfeitamente!${NC}"
else
    echo -e "${RED}❌ Webhook com problema: $WEBHOOK_TEST${NC}"
fi

# Testar API compartilhada
echo -e "${BLUE}🔌 Testando API compartilhada...${NC}"
API_TEST=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null)

if [ "$API_TEST" = "healthy" ]; then
    echo -e "${GREEN}✅ API compartilhada funcionando!${NC}"
else
    echo -e "${RED}❌ API compartilhada com problema: $API_TEST${NC}"
fi

# Testar banco compartilhado
echo -e "${BLUE}📊 Testando banco compartilhado...${NC}"
DB_TEST=$(docker exec shared-postgres pg_isready -U neoquima_admin -d neoquima_shared 2>/dev/null && echo "ready" || echo "not ready")

if [ "$DB_TEST" = "ready" ]; then
    echo -e "${GREEN}✅ Banco compartilhado funcionando!${NC}"
else
    echo -e "${RED}❌ Banco compartilhado com problema${NC}"
fi

echo -e "\n${BLUE}📱 AGORA TESTE ENVIANDO UMA MENSAGEM NO WHATSAPP!${NC}"
echo -e "${YELLOW}💡 O webhook receberá a mensagem em: $NGROK_URL/webhook${NC}"
echo -e "\n${BLUE}🛑 Para parar: Ctrl+C${NC}"
echo -e "${BLUE}🔍 Para ver logs:${NC}"
echo -e "${BLUE}   📱 WhatsApp Gateway: ${GREEN}docker logs infra-whatsapp-gateway-1${NC}"
echo -e "${BLUE}   🔌 API Compartilhada: ${GREEN}docker logs shared-database-api${NC}"
echo -e "${BLUE}   📊 Banco: ${GREEN}docker logs shared-postgres${NC}"
echo -e "${BLUE}🌐 Interface ngrok: ${GREEN}http://localhost:4040${NC}\n"

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

# Mostrar logs em tempo real de todos os serviços
echo -e "${BLUE}📊 Mostrando logs em tempo real de todos os serviços...${NC}"
echo -e "${BLUE}===============================================${NC}"

# Função para mostrar logs de todos os serviços
show_logs() {
    echo -e "${YELLOW}📱 WhatsApp Gateway:${NC}"
    docker logs infra-whatsapp-gateway-1 --tail 5
    
    echo -e "\n${YELLOW}🔌 API Compartilhada:${NC}"
    docker logs shared-database-api --tail 5
    
    echo -e "\n${YELLOW}📊 Banco Compartilhado:${NC}"
    docker logs shared-postgres --tail 3
    
    echo -e "\n${BLUE}🔄 Atualizando logs a cada 10 segundos...${NC}"
    echo -e "${BLUE}===============================================${NC}"
}

# Mostrar logs iniciais
show_logs

# Loop para atualizar logs
while true; do
    sleep 10
    show_logs
done 