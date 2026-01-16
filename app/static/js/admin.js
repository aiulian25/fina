// Admin panel functionality
let usersData = [];

// Load users on page load
document.addEventListener('DOMContentLoaded', function() {
    loadUsers();
    setupPasswordValidation();
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

// ==================== Password Validation ====================

function setupPasswordValidation() {
    // Create user form password validation
    const createPassword = document.getElementById('create-password');
    const createConfirmPassword = document.getElementById('create-confirm-password');
    
    if (createPassword) {
        createPassword.addEventListener('input', () => {
            updatePasswordStrength('create', createPassword.value);
            validatePasswordMatch('create');
        });
    }
    
    if (createConfirmPassword) {
        createConfirmPassword.addEventListener('input', () => validatePasswordMatch('create'));
    }
    
    // Edit user form password validation
    const editPassword = document.getElementById('edit-password');
    const editConfirmPassword = document.getElementById('edit-confirm-password');
    
    if (editPassword) {
        editPassword.addEventListener('input', () => {
            const value = editPassword.value;
            updatePasswordStrength('edit', value);
            
            // Show/hide confirm password field based on whether password is entered
            const confirmContainer = document.getElementById('edit-confirm-password-container');
            if (value.length > 0) {
                confirmContainer.classList.remove('hidden');
            } else {
                confirmContainer.classList.add('hidden');
                editConfirmPassword.value = '';
                document.getElementById('edit-password-match').classList.add('hidden');
            }
            
            validatePasswordMatch('edit');
        });
    }
    
    if (editConfirmPassword) {
        editConfirmPassword.addEventListener('input', () => validatePasswordMatch('edit'));
    }
}

function updatePasswordStrength(prefix, password) {
    const strengthContainer = document.getElementById(`${prefix}-password-strength`);
    const strengthText = document.getElementById(`${prefix}-strength-text`);
    
    if (!password) {
        strengthContainer.classList.add('hidden');
        return;
    }
    
    strengthContainer.classList.remove('hidden');
    
    let strength = 0;
    
    // Length check
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    
    // Character variety checks
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    
    // Cap at 4
    strength = Math.min(strength, 4);
    
    // Update bars
    const colors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-green-500'];
    const labels = [
        window.getTranslation('admin.passwordWeak', 'Weak'),
        window.getTranslation('admin.passwordFair', 'Fair'),
        window.getTranslation('admin.passwordGood', 'Good'),
        window.getTranslation('admin.passwordStrong', 'Strong')
    ];
    
    for (let i = 1; i <= 4; i++) {
        const bar = document.getElementById(`${prefix}-strength-${i}`);
        bar.className = 'h-1 flex-1 rounded';
        if (i <= strength) {
            bar.classList.add(colors[strength - 1]);
        } else {
            bar.classList.add('bg-slate-200', 'dark:bg-slate-700');
        }
    }
    
    strengthText.textContent = labels[strength - 1] || labels[0];
    strengthText.className = 'text-xs';
    if (strength <= 1) strengthText.classList.add('text-red-500');
    else if (strength === 2) strengthText.classList.add('text-orange-500');
    else if (strength === 3) strengthText.classList.add('text-yellow-600', 'dark:text-yellow-400');
    else strengthText.classList.add('text-green-500');
}

function validatePasswordMatch(prefix) {
    const password = document.getElementById(`${prefix}-password`).value;
    const confirmPassword = document.getElementById(`${prefix}-confirm-password`).value;
    const matchIndicator = document.getElementById(`${prefix}-password-match`);
    
    if (!confirmPassword) {
        matchIndicator.classList.add('hidden');
        return true;
    }
    
    matchIndicator.classList.remove('hidden');
    
    if (password === confirmPassword) {
        matchIndicator.textContent = window.getTranslation('admin.passwordsMatch', 'Passwords match');
        matchIndicator.className = 'text-xs mt-1 text-green-500';
        return true;
    } else {
        matchIndicator.textContent = window.getTranslation('admin.passwordsNoMatch', 'Passwords do not match');
        matchIndicator.className = 'text-xs mt-1 text-red-500';
        return false;
    }
}

function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;
    const icon = button.querySelector('.material-symbols-outlined');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.textContent = 'visibility_off';
    } else {
        input.type = 'password';
        icon.textContent = 'visibility';
    }
}

// ==================== Create User Modal ====================

function openCreateUserModal() {
    document.getElementById('create-user-modal').classList.remove('hidden');
    document.getElementById('create-user-modal').classList.add('flex');
    // Reset form
    document.getElementById('create-user-form').reset();
    document.getElementById('create-password-strength').classList.add('hidden');
    document.getElementById('create-password-match').classList.add('hidden');
}

function closeCreateUserModal() {
    document.getElementById('create-user-modal').classList.add('hidden');
    document.getElementById('create-user-modal').classList.remove('flex');
    document.getElementById('create-user-form').reset();
}

document.getElementById('create-user-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const password = formData.get('password');
    const confirmPassword = formData.get('confirm_password');
    
    // Validate password match
    if (password !== confirmPassword) {
        showToast(window.getTranslation('admin.passwordsNoMatch', 'Passwords do not match'), 'error');
        return;
    }
    
    // Validate password length
    if (password.length < 8) {
        showToast(window.getTranslation('admin.passwordTooShort', 'Password must be at least 8 characters'), 'error');
        return;
    }
    
    const userData = {
        username: formData.get('username'),
        email: formData.get('email'),
        password: password,
        is_admin: formData.get('is_admin') === 'on',
        language: formData.get('language'),
        currency: formData.get('currency')
    };
    
    // Show loading state
    const submitBtn = document.getElementById('create-user-btn');
    const spinner = document.getElementById('create-user-spinner');
    submitBtn.disabled = true;
    spinner.classList.remove('hidden');
    
    try {
        const response = await fetch('/api/admin/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
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
    } finally {
        submitBtn.disabled = false;
        spinner.classList.add('hidden');
    }
});

// ==================== Edit User Modal ====================

async function editUser(userId) {
    try {
        const response = await fetch(`/api/admin/users/${userId}`);
        const data = await response.json();
        
        if (!data.success) {
            showToast(data.message || window.getTranslation('admin.errorLoading', 'Error loading user'), 'error');
            return;
        }
        
        const user = data.user;
        
        // Populate form
        document.getElementById('edit-user-id').value = user.id;
        document.getElementById('edit-username').value = user.username;
        document.getElementById('edit-email').value = user.email;
        document.getElementById('edit-language').value = user.language;
        document.getElementById('edit-currency').value = user.currency;
        document.getElementById('edit-is-admin-checkbox').checked = user.is_admin;
        
        // Reset password fields
        document.getElementById('edit-password').value = '';
        document.getElementById('edit-confirm-password').value = '';
        document.getElementById('edit-confirm-password-container').classList.add('hidden');
        document.getElementById('edit-password-strength').classList.add('hidden');
        document.getElementById('edit-password-match').classList.add('hidden');
        
        // Show modal
        document.getElementById('edit-user-modal').classList.remove('hidden');
        document.getElementById('edit-user-modal').classList.add('flex');
        
    } catch (error) {
        console.error('Error loading user:', error);
        showToast(window.getTranslation('admin.errorLoading', 'Error loading user'), 'error');
    }
}

function closeEditUserModal() {
    document.getElementById('edit-user-modal').classList.add('hidden');
    document.getElementById('edit-user-modal').classList.remove('flex');
    document.getElementById('edit-user-form').reset();
}

document.getElementById('edit-user-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const userId = formData.get('user_id');
    const password = formData.get('password');
    const confirmPassword = formData.get('confirm_password');
    
    // Validate password match if password is provided
    if (password && password !== confirmPassword) {
        showToast(window.getTranslation('admin.passwordsNoMatch', 'Passwords do not match'), 'error');
        return;
    }
    
    // Validate password length if provided
    if (password && password.length < 8) {
        showToast(window.getTranslation('admin.passwordTooShort', 'Password must be at least 8 characters'), 'error');
        return;
    }
    
    const userData = {
        username: formData.get('username'),
        email: formData.get('email'),
        is_admin: formData.get('is_admin') === 'on',
        language: formData.get('language'),
        currency: formData.get('currency')
    };
    
    // Only include password if it was entered
    if (password) {
        userData.password = password;
    }
    
    // Show loading state
    const submitBtn = document.getElementById('edit-user-btn');
    const spinner = document.getElementById('edit-user-spinner');
    submitBtn.disabled = true;
    spinner.classList.remove('hidden');
    
    try {
        const response = await fetch(`/api/admin/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            },
            body: JSON.stringify(userData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(window.getTranslation('admin.userUpdated', 'User updated successfully'), 'success');
            closeEditUserModal();
            loadUsers();
        } else {
            showToast(data.message || window.getTranslation('admin.errorUpdating', 'Error updating user'), 'error');
        }
    } catch (error) {
        console.error('Error updating user:', error);
        showToast(window.getTranslation('admin.errorUpdating', 'Error updating user'), 'error');
    } finally {
        submitBtn.disabled = false;
        spinner.classList.add('hidden');
    }
});

// ==================== Delete User ====================

async function deleteUser(userId, username) {
    if (!confirm(window.getTranslation('admin.confirmDelete', 'Are you sure you want to delete user') + ` "${username}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            }
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

// ==================== Utilities ====================

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
