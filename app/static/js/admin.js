// Admin panel functionality
let usersData = [];

// Load users on page load
document.addEventListener('DOMContentLoaded', function() {
    loadUsers();
});

async function loadUsers() {
    try {
        const response = await fetch('/api/admin/users');
        const data = await response.json();
        
        if (data.users) {
            usersData = data.users;
            updateStats();
            renderUsersTable();
        }
    } catch (error) {
        console.error('Error loading users:', error);
        showToast(window.getTranslation('admin.errorLoading', 'Error loading users'), 'error');
    }
}

function updateStats() {
    const totalUsers = usersData.length;
    const adminUsers = usersData.filter(u => u.is_admin).length;
    const twoFAUsers = usersData.filter(u => u.two_factor_enabled).length;
    
    document.getElementById('total-users').textContent = totalUsers;
    document.getElementById('admin-users').textContent = adminUsers;
    document.getElementById('twofa-users').textContent = twoFAUsers;
}

function renderUsersTable() {
    const tbody = document.getElementById('users-table');
    
    if (usersData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="px-6 py-8 text-center text-text-muted dark:text-slate-400">
                    ${window.getTranslation('admin.noUsers', 'No users found')}
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = usersData.map(user => `
        <tr class="hover:bg-background-light dark:hover:bg-slate-800/50">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-text-main dark:text-white">${escapeHtml(user.username)}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-text-muted dark:text-slate-400">${escapeHtml(user.email)}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                ${user.is_admin ? 
                    `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-500/20 text-blue-800 dark:text-blue-400">
                        ${window.getTranslation('admin.admin', 'Admin')}
                    </span>` : 
                    `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-slate-700 text-gray-800 dark:text-slate-300">
                        ${window.getTranslation('admin.user', 'User')}
                    </span>`
                }
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                ${user.two_factor_enabled ?
                    `<span class="material-symbols-outlined text-green-500 text-[20px]">check_circle</span>` :
                    `<span class="material-symbols-outlined text-text-muted dark:text-slate-600 text-[20px]">cancel</span>`
                }
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-text-muted dark:text-slate-400">${user.language.toUpperCase()}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-text-muted dark:text-slate-400">${user.currency}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-text-muted dark:text-slate-400">${new Date(user.created_at).toLocaleDateString()}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
                <div class="flex items-center gap-2">
                    <button onclick="editUser(${user.id})" class="text-primary hover:text-primary/80 transition-colors" title="${window.getTranslation('common.edit', 'Edit')}">
                        <span class="material-symbols-outlined text-[20px]">edit</span>
                    </button>
                    <button onclick="deleteUser(${user.id}, '${escapeHtml(user.username)}')" class="text-red-500 hover:text-red-600 transition-colors" title="${window.getTranslation('common.delete', 'Delete')}">
                        <span class="material-symbols-outlined text-[20px]">delete</span>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function openCreateUserModal() {
    document.getElementById('create-user-modal').classList.remove('hidden');
    document.getElementById('create-user-modal').classList.add('flex');
}

function closeCreateUserModal() {
    document.getElementById('create-user-modal').classList.add('hidden');
    document.getElementById('create-user-modal').classList.remove('flex');
    document.getElementById('create-user-form').reset();
}

document.getElementById('create-user-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const userData = {
        username: formData.get('username'),
        email: formData.get('email'),
        password: formData.get('password'),
        is_admin: formData.get('is_admin') === 'on'
    };
    
    try {
        const response = await fetch('/api/admin/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(window.getTranslation('admin.userCreated', 'User created successfully'), 'success');
            closeCreateUserModal();
            loadUsers();
        } else {
            showToast(data.message || window.getTranslation('admin.errorCreating', 'Error creating user'), 'error');
        }
    } catch (error) {
        console.error('Error creating user:', error);
        showToast(window.getTranslation('admin.errorCreating', 'Error creating user'), 'error');
    }
});

async function deleteUser(userId, username) {
    if (!confirm(window.getTranslation('admin.confirmDelete', 'Are you sure you want to delete user') + ` "${username}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/users/${userId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(window.getTranslation('admin.userDeleted', 'User deleted successfully'), 'success');
            loadUsers();
        } else {
            showToast(data.message || window.getTranslation('admin.errorDeleting', 'Error deleting user'), 'error');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        showToast(window.getTranslation('admin.errorDeleting', 'Error deleting user'), 'error');
    }
}

async function editUser(userId) {
    // Placeholder for edit functionality
    showToast(window.getTranslation('admin.editNotImplemented', 'Edit functionality coming soon'), 'info');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'info') {
    if (typeof window.showToast === 'function') {
        window.showToast(message, type);
    } else {
        alert(message);
    }
}
