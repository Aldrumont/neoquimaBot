// WhatsApp Configuration Management
let currentWebhookUrl = '';

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    setupEventListeners();
    loadCurrentConfig();
    updateWebhookUrl();
});

function initializePage() {
    // Set current webhook URL from ngrok
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('ngrok')) {
        currentWebhookUrl = urlParams.get('ngrok');
    } else {
        // Try to get from localStorage or use default
        currentWebhookUrl = localStorage.getItem('ngrokUrl') || 'https://614ed1faf60f.ngrok-free.app';
    }
}

function setupEventListeners() {
    // Form submission
    const form = document.getElementById('whatsappConfigForm');
    if (form) {
        form.addEventListener('submit', saveConfiguration);
    }
    
    // Verify token input
    const verifyTokenInput = document.getElementById('verifyToken');
    if (verifyTokenInput) {
        verifyTokenInput.addEventListener('input', function() {
            updateWebhookUrl();
        });
    }
}

function updateWebhookUrl() {
    const verifyToken = document.getElementById('verifyToken')?.value || 'seu_token_aqui';
    const webhookUrl = `${currentWebhookUrl}/webhook`;
    
    // Update form field
    const webhookUrlInput = document.getElementById('webhookUrl');
    if (webhookUrlInput) {
        webhookUrlInput.value = webhookUrl;
    }
    
    // Update display
    const webhookUrlDisplay = document.getElementById('webhookUrlDisplay');
    if (webhookUrlDisplay) {
        webhookUrlDisplay.textContent = webhookUrl;
    }
    
    // Save to localStorage
    localStorage.setItem('ngrokUrl', currentWebhookUrl);
}

async function loadCurrentConfig() {
    try {
        const response = await fetch('/api/whatsapp/config');
        if (response.ok) {
            const config = await response.json();
            displayCurrentConfig(config);
            populateFormWithConfig(config);
        } else {
            displayCurrentConfig(null);
        }
    } catch (error) {
        console.error('Erro ao carregar configuração:', error);
        displayCurrentConfig(null);
    }
}

function displayCurrentConfig(config) {
    const currentConfigDiv = document.getElementById('currentWhatsAppConfig');
    
    if (!config) {
        currentConfigDiv.innerHTML = `
            <div class="text-center text-muted">
                <i class="bi bi-exclamation-triangle display-4 text-warning"></i>
                <p class="mt-2">Nenhuma configuração encontrada</p>
                <small>Configure o WhatsApp Business API para começar</small>
            </div>
        `;
        return;
    }
    
    const html = `
        <div class="row">
            <div class="col-md-6">
                <div class="text-center">
                    <i class="bi bi-check-circle display-4 text-success"></i>
                    <h6 class="mt-2">Status</h6>
                    <span class="badge bg-success fs-6">Configurado</span>
                </div>
            </div>
            <div class="col-md-6">
                <div class="text-center">
                    <i class="bi bi-phone display-4 text-primary"></i>
                    <h6 class="mt-2">Phone ID</h6>
                    <span class="badge bg-primary fs-6">${config.phone_number_id || 'N/A'}</span>
                </div>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-12">
                <div class="alert alert-light">
                    <small>
                        <strong>Business Account:</strong> ${config.business_account_id || 'N/A'} | 
                        <strong>Access Token:</strong> <span class="badge bg-info">Configurado</span> | 
                        <strong>Webhook:</strong> <span class="badge bg-success">Ativo</span>
                    </small>
                </div>
            </div>
        </div>
    `;
    
    currentConfigDiv.innerHTML = html;
}

function populateFormWithConfig(config) {
    if (!config) return;
    
    // Preencher campos se existirem
    if (config.access_token) {
        document.getElementById('accessToken').value = config.access_token;
    }
    if (config.phone_number_id) {
        document.getElementById('phoneNumberId').value = config.phone_number_id;
    }
    if (config.business_account_id) {
        document.getElementById('businessAccountId').value = config.business_account_id;
    }
    if (config.verify_token) {
        document.getElementById('verifyToken').value = config.verify_token;
    }
    
    updateWebhookUrl();
}

async function saveConfiguration() {
    event.preventDefault();
    
    const formData = new FormData(document.getElementById('whatsappConfigForm'));
    
    const config = {
        access_token: formData.get('accessToken'),
        phone_number_id: formData.get('phoneNumberId'),
        business_account_id: formData.get('businessAccountId'),
        verify_token: formData.get('verifyToken'),
        webhook_url: formData.get('webhookUrl')
    };
    
    try {
        const response = await fetch('/api/whatsapp/config', {
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

async function testWhatsApp() {
    const number = document.getElementById('testNumber').value.trim();
    const message = document.getElementById('testMessage').value.trim();
    
    if (!number || !message) {
        showError('Preencha o número e a mensagem para testar');
        return;
    }
    
    if (!number.startsWith('+')) {
        showError('Número deve começar com + (ex: +5511999999999)');
        return;
    }
    
    try {
        const response = await fetch('/api/whatsapp/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                number: number,
                message: message
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            displayTestResult(result, true);
        } else {
            const error = await response.json();
            displayTestResult(error, false);
        }
    } catch (error) {
        showError('Erro de conexão: ' + error.message);
    }
}

function displayTestResult(result, success) {
    const testResultDiv = document.getElementById('testResult');
    
    if (success) {
        testResultDiv.innerHTML = `
            <div class="alert alert-success">
                <i class="bi bi-check-circle"></i>
                <strong>Mensagem enviada com sucesso!</strong><br>
                <small>Message ID: ${result.message_id || 'N/A'}</small>
            </div>
        `;
    } else {
        testResultDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i>
                <strong>Erro ao enviar mensagem:</strong><br>
                <small>${result.detail || result.error || 'Erro desconhecido'}</small>
            </div>
        `;
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

function showSuccess(message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-success border-0 position-fixed';
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-check-circle"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
}

function showError(message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-danger border-0 position-fixed';
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-exclamation-triangle"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
} 