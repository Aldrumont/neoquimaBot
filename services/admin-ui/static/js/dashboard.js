// Dashboard JavaScript for Neoquima Admin UI

// Global variables
let dashboardData = {};
let updateInterval;

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    loadDashboardData();
    
    // Set up auto-refresh every 30 seconds
    updateInterval = setInterval(loadDashboardData, 30000);
    
    // Update timestamp
    updateTimestamp();
});

// Load dashboard data
async function loadDashboardData() {
    try {
        // Load users count
        const usersResponse = await fetch('/api/users');
        if (usersResponse.ok) {
            const usersData = await usersResponse.json();
            updateUsersCount(usersData);
        }
        
        // Load system health
        await loadSystemHealth();
        
        // Load LLM status
        await loadLLMStatus();
        
        // Load recent activity
        await loadRecentActivity();
        
        // Update timestamp
        updateTimestamp();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showToast('Erro ao carregar dados', 'Erro de conexão com o servidor', 'error');
    }
}

// Update users count
function updateUsersCount(usersData) {
    const activeUsers = usersData.users ? usersData.users.filter(user => user.active).length : 0;
    const totalUsers = usersData.users ? usersData.users.length : 0;
    
    document.getElementById('activeUsers').textContent = activeUsers;
    
    // Update total users badge if it exists
    const totalUsersElement = document.getElementById('totalUsers');
    if (totalUsersElement) {
        totalUsersElement.textContent = `${totalUsers} usuários`;
    }
}

// Load system health
async function loadSystemHealth() {
    try {
        // Check shared database API
        const apiResponse = await fetch('/health');
        if (apiResponse.ok) {
            const apiData = await apiResponse.json();
            updateApiStatus(apiData);
        }
        
        // Check webhook status (ngrok)
        await checkWebhookStatus();
        
    } catch (error) {
        console.error('Error loading system health:', error);
        updateApiStatus({ status: 'error' });
    }
}

// Update API status
function updateApiStatus(apiData) {
    const apiStatusElement = document.getElementById('apiStatus');
    if (apiStatusElement) {
        if (apiData.status === 'healthy') {
            apiStatusElement.textContent = 'OK';
            apiStatusElement.className = 'text-info';
        } else {
            apiStatusElement.textContent = 'ERRO';
            apiStatusElement.className = 'text-danger';
        }
    }
}

// Load LLM status
async function loadLLMStatus() {
    try {
        const response = await fetch('/api/llm/health');
        if (response.ok) {
            const llmData = await response.json();
            updateLLMStatus(llmData);
        } else {
            updateLLMStatus({ status: 'error' });
        }
    } catch (error) {
        console.error('Error loading LLM status:', error);
        updateLLMStatus({ status: 'error' });
    }
}

// Update LLM status
function updateLLMStatus(llmData) {
    const llmStatusElement = document.getElementById('llmStatus');
    if (llmStatusElement) {
        if (llmData.status === 'healthy') {
            const providerHealth = llmData.provider_health;
            if (providerHealth && providerHealth.provider) {
                llmStatusElement.textContent = providerHealth.provider.toUpperCase();
                llmStatusElement.className = 'text-success';
            } else {
                llmStatusElement.textContent = 'OK';
                llmStatusElement.className = 'text-success';
            }
        } else {
            llmStatusElement.textContent = 'ERRO';
            llmStatusElement.className = 'text-danger';
        }
    }
}

// Check webhook status
async function checkWebhookStatus() {
    try {
        // Use our own endpoint to check ngrok status
        const response = await fetch('/api/ngrok-status');
        if (response.ok) {
            const data = await response.json();
            if (data.status === 'active') {
                updateWebhookStatus('ATIVO');
                // Store ngrok URL for later use
                window.ngrokUrl = data.url;
            } else {
                updateWebhookStatus('INATIVO');
            }
        } else {
            updateWebhookStatus('INATIVO');
        }
    } catch (error) {
        console.error('Error checking webhook status:', error);
        updateWebhookStatus('INATIVO');
    }
}

// Update webhook status
function updateWebhookStatus(status) {
    const webhookStatusElement = document.getElementById('webhookStatus');
    if (webhookStatusElement) {
        webhookStatusElement.textContent = status;
        if (status === 'ATIVO') {
            webhookStatusElement.className = 'text-success';
        } else {
            webhookStatusElement.className = 'text-danger';
        }
    }
}

// Update today's messages count
async function updateTodayMessages() {
    try {
        const response = await fetch('/api/stats/messages-today');
        if (response.ok) {
            const data = await response.json();
            const todayMessagesElement = document.getElementById('todayMessages');
            if (todayMessagesElement) {
                todayMessagesElement.textContent = data.today_messages || 0;
            }
        }
    } catch (error) {
        console.error('Error updating today messages:', error);
        const todayMessagesElement = document.getElementById('todayMessages');
        if (todayMessagesElement) {
            todayMessagesElement.textContent = '0';
        }
    }
}

// Load recent activity
async function loadRecentActivity() {
    try {
        // For now, we'll show a placeholder
        // In the future, this could fetch from an analytics endpoint
        const recentActivityElement = document.getElementById('recentActivity');
        if (recentActivityElement) {
            recentActivityElement.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="bi bi-clock-history display-4"></i>
                    <p class="mt-2">Funcionalidade em desenvolvimento</p>
                    <small>Em breve: histórico de mensagens e atividades</small>
                </div>
            `;
        }
        
        // Update today's messages count
        await updateTodayMessages();
        
    } catch (error) {
        console.error('Error loading recent activity:', error);
    }
}

// Update timestamp
function updateTimestamp() {
    const lastUpdateElement = document.getElementById('lastUpdate');
    if (lastUpdateElement) {
        const now = new Date();
        lastUpdateElement.textContent = now.toLocaleTimeString('pt-BR');
    }
}

// Show toast notification
function showToast(title, message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastTitle = document.getElementById('toastTitle');
    const toastBody = document.getElementById('toastBody');
    
    if (toast && toastTitle && toastBody) {
        // Set content
        toastTitle.textContent = title;
        toastBody.textContent = message;
        
        // Set type-specific styling
        toast.className = 'toast';
        if (type === 'success') {
            toast.classList.add('bg-success', 'text-white');
        } else if (type === 'error') {
            toast.classList.add('bg-danger', 'text-white');
        } else if (type === 'warning') {
            toast.classList.add('bg-warning', 'text-dark');
        }
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
}

// Utility function to format phone numbers
function formatPhoneNumber(phoneNumber) {
    if (!phoneNumber) return '';
    
    // Remove all non-digit characters
    const cleaned = phoneNumber.replace(/\D/g, '');
    
    // Format based on length
    if (cleaned.length === 11) {
        return `(${cleaned.slice(0,2)}) ${cleaned.slice(2,7)}-${cleaned.slice(7)}`;
    } else if (cleaned.length === 13) {
        return `+${cleaned.slice(0,2)} (${cleaned.slice(2,4)}) ${cleaned.slice(4,9)}-${cleaned.slice(9)}`;
    }
    
    return phoneNumber;
}

// Utility function to format dates
function formatDate(dateString) {
    if (!dateString) return '-';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        return dateString;
    }
}

// Utility function to debounce API calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});

// Export functions for global use
window.dashboardUtils = {
    showToast,
    formatPhoneNumber,
    formatDate,
    debounce
}; 