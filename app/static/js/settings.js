// Settings Page Functionality

document.addEventListener('DOMContentLoaded', () => {
    setupAvatarHandlers();
    setupProfileHandlers();
    setupPasswordHandlers();
});

// Avatar upload and selection
function setupAvatarHandlers() {
    const uploadBtn = document.getElementById('upload-avatar-btn');
    const avatarInput = document.getElementById('avatar-upload');
    const currentAvatar = document.getElementById('current-avatar');
    const sidebarAvatar = document.getElementById('sidebar-avatar');
    const defaultAvatarBtns = document.querySelectorAll('.default-avatar-btn');
    
    // Trigger file input when upload button clicked
    if (uploadBtn && avatarInput) {
        uploadBtn.addEventListener('click', () => {
            avatarInput.click();
        });
        
        // Handle file selection
        avatarInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            // Validate file type
            const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
            if (!allowedTypes.includes(file.type)) {
                showNotification('error', 'Invalid file type. Please use PNG, JPG, GIF, or WEBP.');
                return;
            }
            
            // Validate file size (20MB)
            if (file.size > 20 * 1024 * 1024) {
                showNotification('error', 'File too large. Maximum size is 20MB.');
                return;
            }
            
            // Upload avatar
            const formData = new FormData();
            formData.append('avatar', file);
            
            try {
                const response = await fetch('/api/settings/avatar', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    // Update avatar displays
                    const avatarUrl = result.avatar.startsWith('icons/') 
                        ? `/static/${result.avatar}?t=${Date.now()}`
                        : `/${result.avatar}?t=${Date.now()}`;
                    currentAvatar.src = avatarUrl;
                    if (sidebarAvatar) sidebarAvatar.src = avatarUrl;
                    
                    showNotification('success', result.message || 'Avatar updated successfully!');
                } else {
                    showNotification('error', result.error || 'Failed to upload avatar');
                }
            } catch (error) {
                console.error('Upload error:', error);
                showNotification('error', 'An error occurred during upload');
            }
            
            // Reset input
            avatarInput.value = '';
        });
    }
    
    // Handle default avatar selection
    defaultAvatarBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            const avatarPath = btn.getAttribute('data-avatar');
            
            try {
                const response = await fetch('/api/settings/avatar/default', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ avatar: avatarPath })
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    // Update avatar displays
                    const avatarUrl = result.avatar.startsWith('icons/') 
                        ? `/static/${result.avatar}?t=${Date.now()}`
                        : `/${result.avatar}?t=${Date.now()}`;
                    currentAvatar.src = avatarUrl;
                    if (sidebarAvatar) sidebarAvatar.src = avatarUrl;
                    
                    // Update active state
                    defaultAvatarBtns.forEach(b => b.classList.remove('border-primary'));
                    btn.classList.add('border-primary');
                    
                    showNotification('success', result.message || 'Avatar updated successfully!');
                } else {
                    showNotification('error', result.error || 'Failed to update avatar');
                }
            } catch (error) {
                console.error('Update error:', error);
                showNotification('error', 'An error occurred');
            }
        });
    });
}

// Profile update handlers
function setupProfileHandlers() {
    const saveBtn = document.getElementById('save-profile-btn');
    
    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            const username = document.getElementById('username').value.trim();
            const email = document.getElementById('email').value.trim();
            const language = document.getElementById('language').value;
            const currency = document.getElementById('currency').value;
            const monthlyBudget = document.getElementById('monthly-budget').value;
            
            if (!username || !email) {
                showNotification('error', 'Username and email are required');
                return;
            }
            
            // Email validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                showNotification('error', 'Please enter a valid email address');
                return;
            }
            
            // Budget validation
            const budget = parseFloat(monthlyBudget);
            if (isNaN(budget) || budget < 0) {
                showNotification('error', 'Please enter a valid budget amount');
                return;
            }
            
            try {
                const response = await fetch('/api/settings/profile', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username,
                        email,
                        language,
                        currency,
                        monthly_budget: budget
                    })
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    showNotification('success', result.message || 'Profile updated successfully!');
                    
                    // Update language if changed
                    const currentLang = getCurrentLanguage();
                    if (language !== currentLang) {
                        setLanguage(language);
                        // Reload page to apply translations
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    }
                } else {
                    showNotification('error', result.error || 'Failed to update profile');
                }
            } catch (error) {
                console.error('Update error:', error);
                showNotification('error', 'An error occurred');
            }
        });
    }
}

// Password change handlers
function setupPasswordHandlers() {
    const changeBtn = document.getElementById('change-password-btn');
    
    if (changeBtn) {
        changeBtn.addEventListener('click', async () => {
            const currentPassword = document.getElementById('current-password').value;
            const newPassword = document.getElementById('new-password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            if (!currentPassword || !newPassword || !confirmPassword) {
                showNotification('error', 'All password fields are required');
                return;
            }
            
            if (newPassword.length < 6) {
                showNotification('error', 'New password must be at least 6 characters');
                return;
            }
            
            if (newPassword !== confirmPassword) {
                showNotification('error', 'New passwords do not match');
                return;
            }
            
            try {
                const response = await fetch('/api/settings/password', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        current_password: currentPassword,
                        new_password: newPassword
                    })
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    showNotification('success', result.message || 'Password changed successfully!');
                    
                    // Clear form
                    document.getElementById('current-password').value = '';
                    document.getElementById('new-password').value = '';
                    document.getElementById('confirm-password').value = '';
                } else {
                    showNotification('error', result.error || 'Failed to change password');
                }
            } catch (error) {
                console.error('Change password error:', error);
                showNotification('error', 'An error occurred');
            }
        });
    }
}

// Show notification
function showNotification(type, message) {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-slideIn ${
        type === 'success' 
            ? 'bg-green-500 text-white' 
            : 'bg-red-500 text-white'
    }`;
    
    notification.innerHTML = `
        <span class="material-symbols-outlined text-[20px]">
            ${type === 'success' ? 'check_circle' : 'error'}
        </span>
        <span class="text-sm font-medium">${escapeHtml(message)}</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('animate-slideOut');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
