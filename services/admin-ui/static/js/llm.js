// LLM Configuration and Testing JavaScript

// Modelos disponíveis para cada provider com suas escalas de temperatura
const PROVIDER_MODELS = {
    'ollama': [
        { value: 'qwen2.5:3b-instruct-q4_K_M', label: 'Qwen 2.5 3B (Instruct)', tempRange: [0.0, 2.0] },
        { value: 'tinyllama:latest', label: 'TinyLlama', tempRange: [0.0, 2.0] }
    ],
    'openai': [
        { value: 'gpt-4o-mini', label: 'GPT-4o Mini', tempRange: [0.0, 2.0] },
        { value: 'gpt-4o', label: 'GPT-4o', tempRange: [0.0, 2.0] },
        { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', tempRange: [0.0, 2.0] }
    ],
    'google': [
        { value: 'gemini/gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash Lite', tempRange: [0.0, 1.0] },
        { value: 'gemini/gemini-2.5-flash', label: 'Gemini 2.5 Flash', tempRange: [0.0, 1.0] },
        { value: 'gemini/gemini-2.0-flash-exp', label: 'Gemini 2.0 Flash Exp', tempRange: [0.0, 1.0] },
        { value: 'gemini/gemini-1.5-flash', label: 'Gemini 1.5 Flash', tempRange: [0.0, 1.0] }
    ],
    'anthropic': [
        { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet', tempRange: [0.0, 1.0] },
        { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku', tempRange: [0.0, 1.0] },
        { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus', tempRange: [0.0, 1.0] }
    ],
    'deepseek': [
        { value: 'deepseek-chat', label: 'DeepSeek Chat', tempRange: [0.0, 2.0] },
        { value: 'deepseek-coder', label: 'DeepSeek Coder', tempRange: [0.0, 2.0] }
    ]
};

// Inicialização quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
});

function initializePage() {
    // Carregar configuração atual
    loadCurrentConfig();
    
    // Configurar eventos
    setupEventListeners();
    
    // Configurar slider de temperatura
    setupTemperatureSlider();
}

function setupEventListeners() {
    // Provider change
    document.getElementById('provider').addEventListener('change', async function() {
        await updateModelOptions(this.value);
    });
    
    // Model change
    document.getElementById('model').addEventListener('change', function() {
        updateTemperatureRange(this.value);
    });
    
    // Form de configuração
    
    // Form de configuração
    document.getElementById('llmConfigForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveConfiguration();
    });
    
    // Form de teste
    document.getElementById('llmTestForm').addEventListener('submit', function(e) {
        e.preventDefault();
        testLLM();
    });
}

function setupTemperatureSlider() {
    const tempSlider = document.getElementById('temperature');
    const tempValue = document.getElementById('tempValue');
    
    tempSlider.addEventListener('input', function() {
        tempValue.textContent = this.value;
    });
}

async function updateModelOptions(provider) {
    const modelSelect = document.getElementById('model');
    modelSelect.innerHTML = '<option value="">Selecione um modelo</option>';
    
    if (provider && PROVIDER_MODELS[provider]) {
        PROVIDER_MODELS[provider].forEach(model => {
            const option = document.createElement('option');
            option.value = model.value;
            option.textContent = model.label;
            option.dataset.tempRange = JSON.stringify(model.tempRange);
            modelSelect.appendChild(option);
        });
    }
    
    // Gerenciar campos de API key
    updateApiKeyFields(provider);
    
    // Carregar API key salva para este provider se existir
    await loadApiKeyForProvider(provider);
}

async function loadApiKeyForProvider(provider) {
    try {
        // Buscar todas as configurações para encontrar uma com API key para este provider
        const response = await fetch('/api/llm/configs');
        if (response.ok) {
            const configs = await response.json();
            
            // Procurar por uma configuração com API key para o provider selecionado
            const configWithApiKey = configs.find(config => 
                config.provider === provider && config.api_key
            );
            
            if (configWithApiKey && configWithApiKey.api_key) {
                // Preencher o campo de API key correspondente
                if (provider === 'openai') {
                    document.getElementById('openaiApiKey').value = configWithApiKey.api_key;
                } else if (provider === 'google') {
                    document.getElementById('googleApiKey').value = configWithApiKey.api_key;
                } else if (provider === 'anthropic') {
                    document.getElementById('anthropicApiKey').value = configWithApiKey.api_key;
                } else if (provider === 'deepseek') {
                    document.getElementById('deepseekApiKey').value = configWithApiKey.api_key;
                }
                
                console.log(`API key carregada automaticamente para ${provider}`);
            } else {
                // Limpar o campo se não houver API key salva
                if (provider === 'openai') {
                    document.getElementById('openaiApiKey').value = '';
                } else if (provider === 'google') {
                    document.getElementById('googleApiKey').value = '';
                } else if (provider === 'anthropic') {
                    document.getElementById('anthropicApiKey').value = '';
                } else if (provider === 'deepseek') {
                    document.getElementById('deepseekApiKey').value = '';
                }
            }
        }
    } catch (error) {
        console.log('Erro ao carregar API key:', error);
    }
}

function updateTemperatureRange(modelValue) {
    const provider = document.getElementById('provider').value;
    if (!provider || !modelValue) return;
    
    // Encontrar o modelo selecionado
    const model = PROVIDER_MODELS[provider]?.find(m => m.value === modelValue);
    if (!model || !model.tempRange) return;
    
    const [minTemp, maxTemp] = model.tempRange;
    const tempSlider = document.getElementById('temperature');
    const tempValue = document.getElementById('tempValue');
    
    // Ajustar range do slider
    tempSlider.min = minTemp;
    tempSlider.max = maxTemp;
    tempSlider.step = 0.1;
    
    // Ajustar valor atual se estiver fora do range
    const currentValue = parseFloat(tempSlider.value);
    if (currentValue < minTemp || currentValue > maxTemp) {
        tempSlider.value = (minTemp + maxTemp) / 2; // Valor médio
        tempValue.textContent = tempSlider.value;
    }
    
    // Atualizar display do valor
    tempValue.textContent = tempSlider.value;
    
    // Adicionar tooltip ou informação sobre o range
    const tempContainer = tempSlider.closest('.mb-3');
    let rangeInfo = tempContainer.querySelector('.temp-range-info');
    if (!rangeInfo) {
        rangeInfo = document.createElement('small');
        rangeInfo.className = 'text-muted temp-range-info';
        tempContainer.appendChild(rangeInfo);
    }
    rangeInfo.textContent = `Range: ${minTemp} - ${maxTemp}`;
    
    console.log(`Temperatura ajustada para modelo ${modelValue}: ${minTemp} - ${maxTemp}`);
}

function updateApiKeyFields(provider) {
    const apiKeyFields = document.getElementById('apiKeyFields');
    const openaiField = document.getElementById('openaiApiKeyField');
    const googleField = document.getElementById('googleApiKeyField');
    const anthropicField = document.getElementById('anthropicApiKeyField');
    const deepseekField = document.getElementById('deepseekApiKeyField');
    
    // Esconder todos os campos primeiro
    openaiField.style.display = 'none';
    googleField.style.display = 'none';
    anthropicField.style.display = 'none';
    deepseekField.style.display = 'none';
    
    // Mostrar apenas o campo relevante para o provider selecionado
    if (provider === 'openai') {
        openaiField.style.display = 'block';
        apiKeyFields.style.display = 'block';
    } else if (provider === 'google') {
        googleField.style.display = 'block';
        apiKeyFields.style.display = 'block';
    } else if (provider === 'anthropic') {
        anthropicField.style.display = 'block';
        apiKeyFields.style.display = 'block';
    } else if (provider === 'deepseek') {
        deepseekField.style.display = 'block';
        apiKeyFields.style.display = 'block';
    } else {
        // Ollama não precisa de API key
        apiKeyFields.style.display = 'none';
    }
}

function togglePasswordVisibility(fieldId) {
    const field = document.getElementById(fieldId);
    const button = field.nextElementSibling;
    const icon = button.querySelector('i');
    
    if (field.type === 'password') {
        field.type = 'text';
        icon.className = 'bi bi-eye-slash';
    } else {
        field.type = 'password';
        icon.className = 'bi bi-eye';
    }
}

async function loadCurrentConfig() {
    try {
        const response = await fetch('/api/llm/config');
        if (response.ok) {
            const config = await response.json();
            displayCurrentConfig(config);
            populateFormWithConfig(config);
        } else {
            showError('Erro ao carregar configuração atual');
        }
    } catch (error) {
        showError('Erro de conexão: ' + error.message);
    }
}

function displayCurrentConfig(config) {
    const currentConfigDiv = document.getElementById('currentConfig');
    
    const html = `
        <div class="row">
            <div class="col-md-3">
                <div class="text-center">
                    <i class="bi bi-robot display-4 text-primary"></i>
                    <h6 class="mt-2">Provider</h6>
                    <span class="badge bg-primary fs-6">${config.provider}</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <i class="bi bi-cpu display-4 text-success"></i>
                    <h6 class="mt-2">Modelo</h6>
                    <span class="badge bg-success fs-6">${config.model}</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <i class="bi bi-thermometer-half display-4 text-warning"></i>
                    <h6 class="mt-2">Temperatura</h6>
                    <span class="badge bg-warning fs-6">${config.temperature}</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <i class="bi bi-hash display-4 text-info"></i>
                    <h6 class="mt-2">Max Tokens</h6>
                    <span class="badge bg-info fs-6">${config.max_tokens}</span>
                </div>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-12">
                <div class="alert alert-light">
                    <small>
                        <strong>ID:</strong> ${config.id} | 
                        <strong>Status:</strong> <span class="badge bg-success">${config.is_active ? 'Ativo' : 'Inativo'}</span> | 
                        <strong>Atualizado:</strong> ${new Date(config.created_at).toLocaleString('pt-BR')}
                        ${config.api_key ? ' | <strong>API Key:</strong> <span class="badge bg-info">Configurada</span>' : ''}
                    </small>
                </div>
            </div>
        </div>
    `;
    
    currentConfigDiv.innerHTML = html;
}

function populateFormWithConfig(config) {
    // Selecionar provider
    const providerSelect = document.getElementById('provider');
    providerSelect.value = config.provider;
    
    // Atualizar modelos disponíveis
    updateModelOptions(config.provider);
    
    // Selecionar modelo
    setTimeout(() => {
        const modelSelect = document.getElementById('model');
        modelSelect.value = config.model;
        // Ajustar range de temperatura para o modelo selecionado
        updateTemperatureRange(config.model);
    }, 100);
    
    // Configurar outros campos
    document.getElementById('temperature').value = config.temperature;
    document.getElementById('tempValue').textContent = config.temperature;
    document.getElementById('max_tokens').value = config.max_tokens;
    
    // Preencher campos de API key se existirem
    if (config.api_key) {
        if (config.provider === 'openai') {
            document.getElementById('openaiApiKey').value = config.api_key;
        } else if (config.provider === 'google') {
            document.getElementById('googleApiKey').value = config.api_key;
        } else if (config.provider === 'anthropic') {
            document.getElementById('anthropicApiKey').value = config.api_key;
        } else if (config.provider === 'deepseek') {
            document.getElementById('deepseekApiKey').value = config.api_key;
        }
    }
}

async function saveConfiguration() {
    const formData = new FormData(document.getElementById('llmConfigForm'));
    const provider = formData.get('provider');
    
    const config = {
        provider: provider,
        model: formData.get('model'),
        temperature: parseFloat(formData.get('temperature')),
        max_tokens: parseInt(formData.get('max_tokens')),
        context_window: 8192,
        rag_enabled: true,
        default_rag_collection: 'neoquima'
    };
    
    // Adicionar API key se for um provider que precisa
    if (provider !== 'ollama') {
        let apiKey = null;
        if (provider === 'openai') {
            apiKey = document.getElementById('openaiApiKey').value.trim();
        } else if (provider === 'google') {
            apiKey = document.getElementById('googleApiKey').value.trim();
        } else if (provider === 'anthropic') {
            apiKey = document.getElementById('anthropicApiKey').value.trim();
        } else if (provider === 'deepseek') {
            apiKey = document.getElementById('deepseekApiKey').value.trim();
        }
        
        if (apiKey) {
            config.api_key = apiKey;
        }
    }
    
    try {
        const response = await fetch('/api/llm/config', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        if (response.ok) {
            const result = await response.json();
            showSuccess('Configuração salva com sucesso!');
            loadCurrentConfig(); // Recarregar configuração atual
        } else {
            const error = await response.json();
            showError('Erro ao salvar: ' + (error.detail || 'Erro desconhecido'));
        }
    } catch (error) {
        showError('Erro de conexão: ' + error.message);
    }
}

async function testLLM() {
    const message = document.getElementById('testMessage').value;
    if (!message.trim()) {
        showError('Digite uma mensagem para testar');
        return;
    }
    
    const testData = {
        message: message,
        temperature: parseFloat(document.getElementById('temperature').value),
        max_tokens: parseInt(document.getElementById('max_tokens').value)
    };
    
    // Mostrar loading
    const testButton = document.querySelector('#llmTestForm button[type="submit"]');
    const originalText = testButton.innerHTML;
    testButton.innerHTML = '<i class="bi bi-hourglass-split"></i> Testando...';
    testButton.disabled = true;
    
    try {
        const response = await fetch('/api/llm/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testData)
        });
        
        if (response.ok) {
            const result = await response.json();
            displayTestResult(result);
        } else {
            const error = await response.json();
            showError('Erro no teste: ' + (error.detail || 'Erro desconhecido'));
        }
    } catch (error) {
        showError('Erro de conexão: ' + error.message);
    } finally {
        // Restaurar botão
        testButton.innerHTML = originalText;
        testButton.disabled = false;
    }
}

function displayTestResult(result) {
    document.getElementById('testResponse').textContent = result.response;
    document.getElementById('testModel').textContent = result.model;
    document.getElementById('testTime').textContent = result.processing_time.toFixed(2);
    document.getElementById('testTokens').textContent = `${result.tokens_used.prompt} + ${result.tokens_used.completion} = ${result.tokens_used.prompt + result.tokens_used.completion}`;
    
    document.getElementById('testResult').style.display = 'block';
    
    // Scroll para o resultado
    document.getElementById('testResult').scrollIntoView({ behavior: 'smooth' });
}

function showSuccess(message) {
    // Criar toast de sucesso
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-success border-0 position-fixed top-0 end-0 m-3';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-check-circle"></i> ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remover após ser fechado
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
}

function showError(message) {
    // Criar toast de erro
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-danger border-0 position-fixed top-0 end-0 m-3';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-exclamation-triangle"></i> ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remover após ser fechado
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
} 