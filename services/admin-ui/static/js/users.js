// Users Management JavaScript for Neoquima Admin UI

// Global variables
let users = [];
let currentUser = null;
let deleteUserId = null;

// Initialize users page when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Users page initialized');
    loadUsers();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterUsers, 300));
    }
    
    // Status filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', filterUsers);
    }
    
    // Add user form
    const addUserForm = document.getElementById('addUserForm');
    if (addUserForm) {
        addUserForm.addEventListener('submit', handleAddUser);
    }
    
    // Edit user form
    const editUserForm = document.getElementById('editUserForm');
    if (editUserForm) {
        editUserForm.addEventListener('submit', handleEditUser);
    }
}

// Load users from API
async function loadUsers() {
    try {
        showLoading(true);
        
        const response = await fetch('/api/users');
        if (response.ok) {
            const data = await response.json();
            users = data.users || [];
            renderUsersTable(users);
            updateTotalUsers();
        } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error loading users:', error);
        showToast('Erro', 'Falha ao carregar usuários', 'error');
        renderUsersTable([]);
    } finally {
        showLoading(false);
    }
}

// Render users table
function renderUsersTable(usersToRender) {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;
    
    if (usersToRender.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4">
                    <div class="text-muted">
                        <i class="bi bi-people display-4"></i>
                        <p class="mt-2">Nenhum usuário encontrado</p>
                        <small>Clique em "Novo Usuário" para adicionar</small>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = usersToRender.map(user => `
        <tr class="fade-in">
            <td>
                <div class="d-flex align-items-center">
                    <div class="avatar-sm me-3">
                        <i class="bi bi-person-circle text-primary fs-4"></i>
                    </div>
                    <div>
                        <div class="fw-bold">${user.name}</div>
                        <small class="text-muted">ID: ${user.id}</small>
                    </div>
                </div>
            </td>
            <td>
                <span class="badge bg-light text-dark">
                    <i class="bi bi-telephone me-1"></i>
                    ${formatPhoneNumber(user.number)}
                </span>
            </td>
            <td>
                <span class="text-truncate-2">${user.company || '-'}</span>
            </td>
            <td>
                <span class="badge ${user.active ? 'bg-success' : 'bg-secondary'}">
                    <i class="bi bi-${user.active ? 'check-circle' : 'x-circle'} me-1"></i>
                    ${user.active ? 'Ativo' : 'Inativo'}
                </span>
            </td>
            <td>
                <small class="text-muted">
                    ${formatDate(user.last_interact) || 'Nunca'}
                </small>
            </td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button type="button" class="btn btn-outline-primary" 
                            onclick="editUser(${user.id})" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button type="button" class="btn btn-outline-danger" 
                            onclick="deleteUser(${user.id}, '${user.name}')" title="Excluir">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Filter users based on search and status
function filterUsers() {
    const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';
    const statusFilter = document.getElementById('statusFilter')?.value || '';
    
    let filteredUsers = users.filter(user => {
        // Search filter
        const matchesSearch = !searchTerm || 
            user.name.toLowerCase().includes(searchTerm) ||
            user.number.toLowerCase().includes(searchTerm) ||
            (user.company && user.company.toLowerCase().includes(searchTerm));
        
        // Status filter
        const matchesStatus = !statusFilter || user.active.toString() === statusFilter;
        
        return matchesSearch && matchesStatus;
    });
    
    renderUsersTable(filteredUsers);
}

// Update total users count
function updateTotalUsers() {
    const totalUsersElement = document.getElementById('totalUsers');
    if (totalUsersElement) {
        totalUsersElement.textContent = `${users.length} usuários`;
    }
}

// Handle add user form submission
async function handleAddUser(event) {
    event.preventDefault();
    
    const formData = {
        name: document.getElementById('userName').value.trim(),
        number: document.getElementById('userNumber').value.trim(),
        company: document.getElementById('userCompany').value.trim() || null,
        note: document.getElementById('userNote').value.trim() || null,
        is_active: document.getElementById('userActive').checked
    };
    
    try {
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            const newUser = await response.json();
            showToast('Sucesso', 'Usuário criado com sucesso!', 'success');
            
            // Close modal and reset form
            const modal = bootstrap.Modal.getInstance(document.getElementById('addUserModal'));
            modal.hide();
            document.getElementById('addUserForm').reset();
            
            // Reload users
            await loadUsers();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erro ao criar usuário');
        }
    } catch (error) {
        console.error('Error creating user:', error);
        showToast('Erro', error.message, 'error');
    }
}

// Edit user
function editUser(userId) {
    const user = users.find(u => u.id === userId);
    if (!user) return;
    
    currentUser = user;
    
    // Populate form
    document.getElementById('editUserId').value = user.id;
    document.getElementById('editUserName').value = user.name;
    document.getElementById('editUserNumber').value = user.number;
    document.getElementById('editUserCompany').value = user.company || '';
    document.getElementById('editUserNote').value = user.note || '';
    document.getElementById('editUserActive').checked = user.active;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
    modal.show();
}

// Handle edit user form submission
async function handleEditUser(event) {
    event.preventDefault();
    
    if (!currentUser) return;
    
    const formData = {
        name: document.getElementById('editUserName').value.trim(),
        number: document.getElementById('editUserNumber').value.trim(),
        company: document.getElementById('editUserCompany').value.trim() || null,
        note: document.getElementById('editUserNote').value.trim() || null,
        is_active: document.getElementById('editUserActive').checked
    };
    
    try {
        const response = await fetch(`/api/users/${currentUser.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            const updatedUser = await response.json();
            showToast('Sucesso', 'Usuário atualizado com sucesso!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('editUserModal'));
            modal.hide();
            
            // Reload users
            await loadUsers();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erro ao atualizar usuário');
        }
    } catch (error) {
        console.error('Error updating user:', error);
        showToast('Erro', error.message, 'error');
    }
}

// Delete user
function deleteUser(userId, userName) {
    deleteUserId = userId;
    document.getElementById('deleteUserName').textContent = userName;
    
    const modal = new bootstrap.Modal(document.getElementById('deleteUserModal'));
    modal.show();
}

// Confirm delete user
async function confirmDeleteUser() {
    if (!deleteUserId) return;
    
    try {
        const response = await fetch(`/api/users/${deleteUserId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Sucesso', 'Usuário excluído com sucesso!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteUserModal'));
            modal.hide();
            
            // Reload users
            await loadUsers();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erro ao excluir usuário');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        showToast('Erro', error.message, 'error');
    } finally {
        deleteUserId = null;
    }
}

// Refresh users
function refreshUsers() {
    loadUsers();
}

// Show loading state
function showLoading(show) {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;
    
    if (show) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4">
                    <div class="text-muted">
                        <div class="spinner-border spinner-border-sm me-2" role="status">
                            <span class="visually-hidden">Carregando...</span>
                        </div>
                        Carregando usuários...
                    </div>
                </td>
            </tr>
        `;
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

// Utility function to debounce
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