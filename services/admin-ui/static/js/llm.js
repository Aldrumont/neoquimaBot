/**
 * LLM Configuration Management
 * Neoquima Admin UI
 */

class LLMManager {
    constructor() {
        this.currentProvider = null;
        this.localModels = [];
        this.apiModels = {};
        this.init();
    }

    async init() {
        await this.loadAllData();
        this.setupEventListeners();
        this.updateUI();
    }

    async loadAllData() {
        try {
            // Carregar dados em paralelo
            const [providers, config, health, localModels, allModels] = await Promise.all([
                this.fetchProviders(),
                this.fetchCurrentConfig(),
                this.fetchSystemHealth(),
                this.fetchLocalModels(),
                this.fetchAllModels()
            ]);

            this.providers = providers;
            this.currentConfig = config;
            this.systemHealth = health;
            this.localModels = localModels;
            this.apiModels = allModels.api || {};

            console.log('Dados carregados:', {
                providers: this.providers,
                config: this.currentConfig,
                localModels: this.localModels,
                apiModels: this.apiModels
            });

        } catch (error) {
            console.error('Erro ao carregar dados:', error);
            this.showError('Erro ao carregar dados iniciais');
        }
    }

    async fetchLocalModels() {
        try {
            const response = await fetch('/api/llm/models/local');
            if (response.ok) {
                const data = await response.json();
                return data.models || [];
            }
            return [];
        } catch (error) {
            console.error('Erro ao buscar modelos locais:', error);
            return [];
        }
    }

    async fetchAllModels() {
        try {
            const response = await fetch('/api/llm/models/all');
            if (response.ok) {
                return await response.json();
            }
            return { local: { models: [] }, api: {} };
        } catch (error) {
            console.error('Erro ao buscar todos os modelos:', error);
            return { local: { models: [] }, api: {} };
        }
    }

    async fetchProviders() {
        try {
            const response = await fetch('/api/llm/providers');
            if (response.ok) {
                const data = await response.json();
                return data.providers || {};
            }
            return {};
        } catch (error) {
            console.error('Erro ao buscar providers:', error);
            return {};
        }
    }

    async fetchCurrentConfig() {
        try {
            const response = await fetch('/api/llm/config');
            if (response.ok) {
                return await response.json();
            }
            return null;
        } catch (error) {
            console.error('Erro ao buscar configuração atual:', error);
            return null;
        }
    }

    async fetchSystemHealth() {
        try {
            const response = await fetch('/api/llm/health');
            if (response.ok) {
                return await response.json();
            }
            return null;
        } catch (error) {
            console.error('Erro ao buscar saúde do sistema:', error);
            return null;
        }
    }

    setupEventListeners() {
        // Provider selection
        document.getElementById('providerSelect').addEventListener('change', (e) => {
            this.onProviderChange(e.target.value);
        });

        // Temperature slider
        document.getElementById('temperatureInput').addEventListener('input', (e) => {
            document.getElementById('temperatureValue').textContent = e.target.value;
        });

        // Form submission
        document.getElementById('llmConfigForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveConfiguration();
        });

        // Test button
        document.getElementById('testConfigBtn').addEventListener('click', () => {
            this.testConfiguration();
        });

        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshData();
        });

        // Quick switch buttons
        document.getElementById('switchToOllamaBtn').addEventListener('click', () => {
            this.quickSwitch('ollama');
        });

        document.getElementById('switchToOpenAIBtn').addEventListener('click', () => {
            this.quickSwitch('openai');
        });

        document.getElementById('switchToClaudeBtn').addEventListener('click', () => {
            this.quickSwitch('anthropic');
        });

        document.getElementById('switchToGeminiBtn').addEventListener('click', () => {
            this.quickSwitch('google');
        });

        // API key visibility toggle
        document.getElementById('toggleApiKey').addEventListener('click', () => {
            this.toggleApiKeyVisibility();
        });
    }

    onProviderChange(providerName) {
        console.log('onProviderChange chamado com provider:', providerName);
        this.currentProvider = providerName;
        this.updateModelOptions(providerName);
        this.updateProviderInfo(providerName);
        this.updateApiConfigSection(providerName);
    }

    updateModelOptions(providerName) {
        console.log('updateModelOptions chamado com provider:', providerName);
        console.log('this.localModels:', this.localModels);
        console.log('this.apiModels:', this.apiModels);
        
        // Verificar se já existe um select (modelo já foi trocado)
        let existingSelect = document.getElementById('modelSelect');
        let modelInput = document.getElementById('modelInput');
        
        console.log('Elementos encontrados:', { existingSelect, modelInput });
        
        const provider = this.providers[providerName];
        
        console.log('Provider encontrado:', provider);
        
        if (!provider) {
            console.log('Provider não encontrado, retornando');
            return;
        }

        if (providerName === 'ollama') {
            console.log('Configurando para Ollama (local)');
            // Para Ollama, mostrar apenas modelos locais disponíveis
            if (this.localModels.length > 0) {
                console.log('Criando dropdown com modelos locais:', this.localModels);
                // Criar dropdown com modelos locais
                if (existingSelect) {
                    // Se já existe um select, atualizar as opções
                    this.updateSelectOptions(existingSelect, this.localModels, 'Selecione um modelo local...');
                } else if (modelInput) {
                    // Se existe um input, criar dropdown
                    this.createModelDropdown(modelInput, this.localModels, 'Selecione um modelo local...');
                }
            } else {
                console.log('Nenhum modelo local encontrado, restaurando input');
                // Manter como input de texto se não houver modelos
                if (existingSelect) {
                    this.restoreModelInputFromSelect(existingSelect);
                }
            }
        } else {
            console.log('Configurando para API provider:', providerName);
            // Para APIs, mostrar todos os modelos disponíveis
            const apiModels = this.apiModels[providerName] || [];
            console.log('Modelos de API encontrados:', apiModels);
            if (apiModels.length > 0) {
                console.log('Criando dropdown com modelos de API:', apiModels);
                if (existingSelect) {
                    // Se já existe um select, atualizar as opções
                    this.updateSelectOptions(existingSelect, apiModels, 'Selecione um modelo...');
                } else if (modelInput) {
                    // Se existe um input, criar dropdown
                    this.createModelDropdown(modelInput, apiModels, 'Selecione um modelo...');
                }
            } else {
                console.log('Nenhum modelo de API encontrado, restaurando input');
                if (existingSelect) {
                    this.restoreModelInputFromSelect(existingSelect);
                }
            }
        }
    }

    createModelDropdown(modelInput, models, placeholder) {
        console.log('createModelDropdown chamado com:', { modelInput, models, placeholder });
        
        // Verificar se o elemento existe
        if (!modelInput) {
            console.error('modelInput é null, não é possível criar dropdown');
            return;
        }
        
        // Salvar o input original
        if (!modelInput.dataset.originalType) {
            modelInput.dataset.originalType = modelInput.type;
            modelInput.dataset.originalValue = modelInput.value;
        }

        // Criar select
        const select = document.createElement('select');
        select.className = 'form-select';
        select.id = 'modelSelect';
        
        // Opção padrão
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = placeholder;
        select.appendChild(defaultOption);
        
        // Opções dos modelos
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            select.appendChild(option);
        });
        
        // Substituir input por select
        if (modelInput.parentNode) {
            modelInput.parentNode.replaceChild(select, modelInput);
            
            // Event listener para mudança
            select.addEventListener('change', (e) => {
                if (e.target.value) {
                    this.showSuccess(`Modelo selecionado: ${e.target.value}`);
                }
            });
        } else {
            console.error('modelInput não tem parentNode');
        }
    }

    restoreModelInput(modelInput) {
        console.log('restoreModelInput chamado com:', modelInput);
        
        // Verificar se o elemento existe
        if (!modelInput) {
            console.error('modelInput é null, não é possível restaurar');
            return;
        }
        
        // Restaurar input original se existir
        if (modelInput.dataset.originalType) {
            const input = document.createElement('input');
            input.type = modelInput.dataset.originalType;
            input.className = 'form-control';
            input.id = 'modelInput';
            input.value = modelInput.dataset.originalValue || '';
            input.required = true;
            
            // Substituir select por input
            const select = document.getElementById('modelSelect');
            if (select && select.parentNode) {
                select.parentNode.replaceChild(input, select);
            } else {
                console.error('Select não encontrado ou não tem parentNode');
            }
        } else {
            console.log('Nenhum dataset original encontrado para restaurar');
        }
    }

    updateSelectOptions(select, models, placeholder) {
        console.log('updateSelectOptions chamado com:', { select, models, placeholder });
        
        // Limpar opções existentes
        select.innerHTML = '';
        
        // Opção padrão
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = placeholder;
        select.appendChild(defaultOption);
        
        // Opções dos modelos
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            select.appendChild(option);
        });
    }

    restoreModelInputFromSelect(select) {
        console.log('restoreModelInputFromSelect chamado com:', select);
        
        if (!select || !select.parentNode) {
            console.error('Select não encontrado ou não tem parentNode');
            return;
        }
        
        // Verificar se temos dados salvos
        const originalType = select.dataset.originalType || 'text';
        const originalValue = select.dataset.originalValue || '';
        
        // Criar input
        const input = document.createElement('input');
        input.type = originalType;
        input.className = 'form-control';
        input.id = 'modelInput';
        input.value = originalValue;
        input.required = true;
        
        // Substituir select por input
        select.parentNode.replaceChild(input, select);
    }

    updateProviderInfo(providerName) {
        const providerInfo = document.getElementById('providerInfo');
        const provider = this.providers[providerName];
        
        if (!provider) {
            providerInfo.innerHTML = '<p class="text-muted">Selecione um provider para ver informações</p>';
            return;
        }

        const infoHtml = `
            <div class="mb-3">
                <strong>Nome:</strong> ${provider.name}<br>
                <strong>Descrição:</strong> ${provider.description}<br>
                <strong>API Key:</strong> ${provider.requires_api_key ? 'Sim' : 'Não'}<br>
                <strong>Local:</strong> ${provider.supports_local ? 'Sim' : 'Não'}<br>
                <strong>Streaming:</strong> ${provider.supports_streaming ? 'Sim' : 'Não'}
            </div>
        `;
        
        providerInfo.innerHTML = infoHtml;
    }

    updateApiConfigSection(providerName) {
        const apiConfigSection = document.getElementById('apiConfigSection');
        const provider = this.providers[providerName];
        
        if (provider && provider.requires_api_key) {
            apiConfigSection.style.display = 'block';
        } else {
            apiConfigSection.style.display = 'none';
        }
    }

    updateUI() {
        this.updateStatusCards();
        this.populateProviderSelect();
        this.populateForm();
    }

    updateStatusCards() {
        // Provider ativo
        if (this.currentConfig) {
            document.getElementById('activeProvider').textContent = this.currentConfig.provider || '-';
            document.getElementById('activeModel').textContent = this.currentConfig.model || '-';
        }

        // Status do sistema
        if (this.systemHealth) {
            const status = this.systemHealth.status || 'unknown';
            const statusElement = document.getElementById('llmStatus');
            statusElement.textContent = status;
            statusElement.className = status === 'healthy' ? 'text-success' : 'text-danger';
        }

        // Performance (simulado)
        document.getElementById('llmPerformance').textContent = '~2.5s';
    }

    populateProviderSelect() {
        const select = document.getElementById('providerSelect');
        select.innerHTML = '<option value="">Selecione um provider...</option>';
        
        Object.keys(this.providers).forEach(providerName => {
            const option = document.createElement('option');
            option.value = providerName;
            option.textContent = providerName.charAt(0).toUpperCase() + providerName.slice(1);
            select.appendChild(option);
        });

        // Selecionar provider atual se existir
        if (this.currentConfig && this.currentConfig.provider) {
            select.value = this.currentConfig.provider;
            this.onProviderChange(this.currentConfig.provider);
        }
    }

    populateForm() {
        if (!this.currentConfig) return;

        // Preencher campos do formulário
        document.getElementById('modelInput').value = this.currentConfig.model || '';
        document.getElementById('temperatureInput').value = this.currentConfig.temperature || 0.7;
        document.getElementById('maxTokensInput').value = this.currentConfig.max_tokens || 1000;
        document.getElementById('contextWindowInput').value = this.currentConfig.context_window || 4096;
        document.getElementById('ragEnabledInput').checked = true;
        document.getElementById('ragCollectionInput').value = 'neoquima';
        
        // Atualizar valor da temperatura
        document.getElementById('temperatureValue').textContent = this.currentConfig.temperature || 0.7;
    }

    async saveConfiguration() {
        try {
            const formData = this.getFormData();
            
            const response = await fetch('/api/llm/config', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                this.showSuccess('Configuração salva com sucesso!');
                await this.refreshData();
            } else {
                const error = await response.json();
                this.showError(`Erro ao salvar: ${error.detail || 'Erro desconhecido'}`);
            }
        } catch (error) {
            this.showError(`Erro ao salvar: ${error.message}`);
        }
    }

    getFormData() {
        const provider = document.getElementById('providerSelect').value;
        const modelInput = document.getElementById('modelInput');
        const modelSelect = document.getElementById('modelSelect');
        
        // Pegar valor do modelo (pode ser input ou select)
        const model = modelSelect ? modelSelect.value : modelInput.value;
        
        return {
            provider: provider,
            model: model,
            temperature: parseFloat(document.getElementById('temperatureInput').value),
            max_tokens: parseInt(document.getElementById('maxTokensInput').value),
            context_window: parseInt(document.getElementById('contextWindowInput').value),
            rag_enabled: document.getElementById('ragEnabledInput').checked,
            default_rag_collection: document.getElementById('ragCollectionInput').value,
            api_key: document.getElementById('apiKeyInput')?.value || null,
            base_url: document.getElementById('baseUrlInput')?.value || null
        };
    }

    async testConfiguration() {
        try {
            const config = this.getFormData();
            
            const response = await fetch('/api/llm/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config: config })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showTestResults(result.message, result.details, true);
            } else {
                this.showTestResults(result.message, result.details, false);
            }
        } catch (error) {
            this.showTestResults('Erro no teste', { error: error.message }, false);
        }
    }

    showTestResults(title, details, success) {
        const modal = new bootstrap.Modal(document.getElementById('testResultsModal'));
        const content = document.getElementById('testResultsContent');
        
        const icon = success ? '✅' : '❌';
        const colorClass = success ? 'text-success' : 'text-danger';
        
        content.innerHTML = `
            <div class="text-center mb-3">
                <h4 class="${colorClass}">${icon} ${title}</h4>
            </div>
            <div class="mb-3">
                <strong>Detalhes:</strong>
                <pre class="bg-light p-3 rounded">${JSON.stringify(details, null, 2)}</pre>
            </div>
        `;
        
        modal.show();
    }

    async quickSwitch(providerName) {
        try {
            document.getElementById('providerSelect').value = providerName;
            this.onProviderChange(providerName);
            
            // Preencher valores padrão para o provider
            this.fillDefaultValues(providerName);
            
            this.showSuccess(`Switched para ${providerName}!`);
        } catch (error) {
            this.showError(`Erro ao trocar para ${providerName}: ${error.message}`);
        }
    }

    fillDefaultValues(providerName) {
        const provider = this.providers[providerName];
        if (!provider) return;

        // Preencher modelo padrão
        if (providerName === 'ollama' && this.localModels.length > 0) {
            const modelSelect = document.getElementById('modelSelect');
            if (modelSelect) {
                modelSelect.value = this.localModels[0];
            }
        } else if (this.apiModels[providerName] && this.apiModels[providerName].length > 0) {
            const modelSelect = document.getElementById('modelSelect');
            if (modelSelect) {
                modelSelect.value = this.apiModels[providerName][0];
            }
        }

        // Preencher outros campos padrão
        document.getElementById('temperatureInput').value = 0.7;
        document.getElementById('maxTokensInput').value = 1000;
        document.getElementById('contextWindowInput').value = 4096;
        document.getElementById('ragEnabledInput').checked = true;
        document.getElementById('ragCollectionInput').value = 'neoquima';
    }

    toggleApiKeyVisibility() {
        const apiKeyInput = document.getElementById('apiKeyInput');
        const toggleBtn = document.getElementById('toggleApiKey');
        const icon = toggleBtn.querySelector('i');
        
        if (apiKeyInput.type === 'password') {
            apiKeyInput.type = 'text';
            icon.className = 'bi bi-eye-slash';
        } else {
            apiKeyInput.type = 'password';
            icon.className = 'bi bi-eye';
        }
    }

    async refreshData() {
        try {
            this.showInfo('Atualizando dados...');
            await this.loadAllData();
            this.updateUI();
            this.showSuccess('Dados atualizados com sucesso!');
        } catch (error) {
            this.showError(`Erro ao atualizar: ${error.message}`);
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'danger');
    }

    showInfo(message) {
        this.showNotification(message, 'info');
    }

    showNotification(message, type) {
        // Criar toast notification
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remover toast após ser fechado
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.llmManager = new LLMManager();
}); 