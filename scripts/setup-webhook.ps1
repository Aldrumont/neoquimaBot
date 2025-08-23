# Script PowerShell para Configuração Automatizada do Webhook WhatsApp

Write-Host "🚀 Configurador Automatizado de Webhook WhatsApp" -ForegroundColor Blue
Write-Host "===============================================" -ForegroundColor Blue
Write-Host ""

# Verificar se o ngrok está instalado
try {
    $ngrokVersion = ngrok version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "ngrok não encontrado"
    }
    Write-Host "✅ ngrok encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ ngrok não encontrado!" -ForegroundColor Red
    Write-Host "📥 Instale o ngrok em: https://ngrok.com/download" -ForegroundColor Yellow
    Write-Host "💡 Ou use: winget install ngrok (Windows)" -ForegroundColor Yellow
    exit 1
}

# Verificar se o Docker está rodando
try {
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker não está rodando"
    }
    Write-Host "✅ Docker rodando" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker não está rodando!" -ForegroundColor Red
    Write-Host "🚀 Inicie o Docker primeiro" -ForegroundColor Yellow
    exit 1
}

# Verificar se o serviço está rodando
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8081/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Serviço WhatsApp Gateway rodando" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Serviço WhatsApp Gateway não está rodando" -ForegroundColor Yellow
    Write-Host "🚀 Iniciando serviços..." -ForegroundColor Blue
    
    # Iniciar os serviços
    docker compose -f infra/compose.yml --env-file infra/.env up -d --build
    
    # Aguardar o serviço estar pronto
    Write-Host "⏳ Aguardando serviço ficar pronto..." -ForegroundColor Yellow
    for ($i = 1; $i -le 30; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8081/health" -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Serviço pronto!" -ForegroundColor Green
                break
            }
        } catch {
            Write-Host "." -NoNewline
            Start-Sleep -Seconds 2
        }
    }
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8081/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -ne 200) {
            Write-Host "❌ Serviço não iniciou em tempo hábil" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "❌ Serviço não iniciou em tempo hábil" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ Serviço WhatsApp Gateway rodando em http://localhost:8081" -ForegroundColor Green
Write-Host ""

# Iniciar ngrok em background
Write-Host "🌐 Iniciando ngrok para porta 8081..." -ForegroundColor Blue
Start-Process -FilePath "ngrok" -ArgumentList "http", "8081" -WindowStyle Hidden

# Aguardar ngrok inicializar
Write-Host "⏳ Aguardando ngrok inicializar..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Obter URL do ngrok
try {
    $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -Method Get
    $ngrokUrl = $tunnels.tunnels[0].public_url
    
    if (-not $ngrokUrl) {
        throw "URL não encontrada"
    }
    
    Write-Host ""
    Write-Host "🎉 ngrok configurado com sucesso!" -ForegroundColor Green
    Write-Host "🌐 URL Pública: $ngrokUrl" -ForegroundColor Green
    Write-Host "🔗 URL Local: http://localhost:8081" -ForegroundColor Green
    Write-Host ""
    
    # Mostrar informações para configuração
    Write-Host "📋 CONFIGURAÇÃO DO WEBHOOK NO FACEBOOK:" -ForegroundColor Yellow
    Write-Host "===============================================" -ForegroundColor Blue
    Write-Host "1️⃣ Acesse: https://developers.facebook.com/apps/1559477822095103/whatsapp-business/wa-settings/?business_id=130384357976670" -ForegroundColor Green
    Write-Host "2️⃣ Configure o Webhook URL: $ngrokUrl/webhook" -ForegroundColor Green
    Write-Host "3️⃣ Verify Token: neoquima_webhook_2024" -ForegroundColor Green
    Write-Host "4️⃣ Selecione os campos: messages, message_deliveries" -ForegroundColor Green
    Write-Host ""
    
    # Testar webhook
    Write-Host "🧪 Testando webhook..." -ForegroundColor Blue
    $webhookTest = Invoke-RestMethod -Uri "$ngrokUrl/webhook?hub.mode=subscribe&hub.verify_token=neoquima_webhook_2024&hub.challenge=123" -Method Get
    
    if ($webhookTest -eq "123") {
        Write-Host "✅ Webhook funcionando perfeitamente!" -ForegroundColor Green
    } else {
        Write-Host "❌ Webhook com problema: $webhookTest" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "📱 AGORA TESTE ENVIANDO UMA MENSAGEM NO WHATSAPP!" -ForegroundColor Blue
    Write-Host "💡 O webhook receberá a mensagem em: $ngrokUrl/webhook" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🛑 Para parar: Ctrl+C" -ForegroundColor Blue
    Write-Host "🔍 Para ver logs: docker logs whatsapp-gateway-1" -ForegroundColor Blue
    Write-Host "🌐 Interface ngrok: http://localhost:4040" -ForegroundColor Blue
    Write-Host ""
    
    # Manter script rodando
    Write-Host "📊 Mostrando logs em tempo real..." -ForegroundColor Yellow
    Write-Host "===============================================" -ForegroundColor Blue
    
    # Mostrar logs em tempo real
    docker logs -f whatsapp-gateway-1
    
} catch {
    Write-Host "❌ Não foi possível obter a URL do ngrok" -ForegroundColor Red
    Write-Host "💡 Verifique se o ngrok está rodando em http://localhost:4040" -ForegroundColor Yellow
    exit 1
} 