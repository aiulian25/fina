// Documents Page Functionality
let currentPage = 1;
const itemsPerPage = 10;
let searchQuery = '';
let allDocuments = [];

// Initialize documents page
document.addEventListener('DOMContentLoaded', () => {
    loadDocuments();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // File input change
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    // Drag and drop
    const uploadArea = document.getElementById('upload-area');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('!border-primary', '!bg-primary/5');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('!border-primary', '!bg-primary/5');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('!border-primary', '!bg-primary/5');
            const files = e.dataTransfer.files;
            handleFiles(files);
        });
    }
    
    // Search input
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                searchQuery = e.target.value.toLowerCase();
                currentPage = 1;
                loadDocuments();
            }, 300);
        });
    }
}

// Handle file select from input
function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
}

// Handle file upload
async function handleFiles(files) {
    if (files.length === 0) return;
    
    const allowedTypes = ['pdf', 'csv', 'xlsx', 'xls', 'png', 'jpg', 'jpeg'];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    for (const file of files) {
        const ext = file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(ext)) {
            showNotification('error', `${file.name}: Unsupported file type. Only PDF, CSV, XLS, XLSX, PNG, JPG allowed.`);
            continue;
        }
        
        if (file.size > maxSize) {
            showNotification('error', `${file.name}: File size exceeds 10MB limit.`);
            continue;
        }
        
        await uploadFile(file);
    }
    
    // Reset file input
    const fileInput = document.getElementById('file-input');
    if (fileInput) fileInput.value = '';
    
    // Reload documents list
    loadDocuments();
}

// Upload file to server
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/documents/', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('success', `${file.name} uploaded successfully!`);
        } else {
            showNotification('error', result.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification('error', 'An error occurred during upload');
    }
}

// Load documents from API
async function loadDocuments() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            per_page: itemsPerPage
        });
        
        if (searchQuery) {
            params.append('search', searchQuery);
        }
        
        const data = await apiCall(`/api/documents/?${params.toString()}`);
        
        allDocuments = data.documents;
        displayDocuments(data.documents);
        updatePagination(data.pagination);
    } catch (error) {
        console.error('Error loading documents:', error);
        document.getElementById('documents-list').innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-8 text-center text-text-muted dark:text-[#92adc9]">
                    <span data-translate="documents.errorLoading">Failed to load documents. Please try again.</span>
                </td>
            </tr>
        `;
    }
}

// Display documents in table
function displayDocuments(documents) {
    const tbody = document.getElementById('documents-list');
    
    if (documents.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-8 text-center text-text-muted dark:text-[#92adc9]">
                    <span data-translate="documents.noDocuments">No documents found. Upload your first document!</span>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = documents.map(doc => {
        const statusConfig = getStatusConfig(doc.status);
        const fileIcon = getFileIcon(doc.file_type);
        
        return `
            <tr class="hover:bg-slate-50 dark:hover:bg-white/[0.02] transition-colors">
                <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                        <span class="material-symbols-outlined text-[20px] ${fileIcon.color}">${fileIcon.icon}</span>
                        <div class="flex flex-col">
                            <span class="text-text-main dark:text-white font-medium">${escapeHtml(doc.original_filename)}</span>
                            <span class="text-xs text-text-muted dark:text-[#92adc9]">${formatFileSize(doc.file_size)}</span>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 text-text-main dark:text-white">
                    ${formatDate(doc.created_at)}
                </td>
                <td class="px-6 py-4">
                    <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-white/10 text-text-main dark:text-white">
                        ${doc.document_category || 'Other'}
                    </span>
                </td>
                <td class="px-6 py-4">
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusConfig.className}">
                        ${statusConfig.hasIcon ? `<span class="material-symbols-outlined text-[14px]">${statusConfig.icon}</span>` : ''}
                        <span data-translate="documents.status${doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}">${doc.status}</span>
                    </span>
                </td>
                <td class="px-6 py-4">
                    <div class="flex items-center justify-end gap-2">
                        ${['PNG', 'JPG', 'JPEG', 'PDF'].includes(doc.file_type.toUpperCase()) ? 
                            `<button onclick="viewDocument(${doc.id}, '${doc.file_type}', '${escapeHtml(doc.original_filename)}')" class="p-2 text-text-muted dark:text-[#92adc9] hover:text-primary hover:bg-primary/10 rounded-lg transition-colors" title="View">
                                <span class="material-symbols-outlined text-[20px]">visibility</span>
                            </button>` : ''
                        }
                        <button onclick="downloadDocument(${doc.id})" class="p-2 text-text-muted dark:text-[#92adc9] hover:text-primary hover:bg-primary/10 rounded-lg transition-colors" title="Download">
                            <span class="material-symbols-outlined text-[20px]">download</span>
                        </button>
                        <button onclick="deleteDocument(${doc.id})" class="p-2 text-text-muted dark:text-[#92adc9] hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors" title="Delete">
                            <span class="material-symbols-outlined text-[20px]">delete</span>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Get status configuration
function getStatusConfig(status) {
    const configs = {
        uploaded: {
            className: 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400',
            icon: 'upload',
            hasIcon: true
        },
        processing: {
            className: 'bg-purple-100 dark:bg-purple-500/20 text-purple-700 dark:text-purple-400 animate-pulse',
            icon: 'sync',
            hasIcon: true
        },
        analyzed: {
            className: 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400',
            icon: 'verified',
            hasIcon: true
        },
        error: {
            className: 'bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400',
            icon: 'error',
            hasIcon: true
        }
    };
    
    return configs[status] || configs.uploaded;
}

// Get file icon
function getFileIcon(fileType) {
    const icons = {
        pdf: { icon: 'picture_as_pdf', color: 'text-red-500' },
        csv: { icon: 'table_view', color: 'text-green-500' },
        xlsx: { icon: 'table_view', color: 'text-green-600' },
        xls: { icon: 'table_view', color: 'text-green-600' },
        png: { icon: 'image', color: 'text-blue-500' },
        jpg: { icon: 'image', color: 'text-blue-500' },
        jpeg: { icon: 'image', color: 'text-blue-500' }
    };
    
    return icons[fileType?.toLowerCase()] || { icon: 'description', color: 'text-gray-500' };
}

// Update pagination
function updatePagination(pagination) {
    const { page, pages, total, per_page } = pagination;
    
    // Update count display
    const start = (page - 1) * per_page + 1;
    const end = Math.min(page * per_page, total);
    
    document.getElementById('page-start').textContent = total > 0 ? start : 0;
    document.getElementById('page-end').textContent = end;
    document.getElementById('total-count').textContent = total;
    
    // Update pagination buttons
    const paginationDiv = document.getElementById('pagination');
    
    if (pages <= 1) {
        paginationDiv.innerHTML = '';
        return;
    }
    
    let buttons = '';
    
    // Previous button
    buttons += `
        <button onclick="changePage(${page - 1})" 
            class="px-3 py-1.5 rounded-lg text-sm font-medium ${page === 1 ? 'bg-gray-100 dark:bg-white/5 text-text-muted dark:text-[#92adc9]/50 cursor-not-allowed' : 'bg-card-light dark:bg-card-dark text-text-main dark:text-white hover:bg-slate-100 dark:hover:bg-white/10 border border-border-light dark:border-[#233648]'} transition-colors"
            ${page === 1 ? 'disabled' : ''}>
            <span class="material-symbols-outlined text-[18px]">chevron_left</span>
        </button>
    `;
    
    // Page numbers
    const maxButtons = 5;
    let startPage = Math.max(1, page - Math.floor(maxButtons / 2));
    let endPage = Math.min(pages, startPage + maxButtons - 1);
    
    if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        buttons += `
            <button onclick="changePage(${i})" 
                class="px-3 py-1.5 rounded-lg text-sm font-medium ${i === page ? 'bg-primary text-white' : 'bg-card-light dark:bg-card-dark text-text-main dark:text-white hover:bg-slate-100 dark:hover:bg-white/10 border border-border-light dark:border-[#233648]'} transition-colors">
                ${i}
            </button>
        `;
    }
    
    // Next button
    buttons += `
        <button onclick="changePage(${page + 1})" 
            class="px-3 py-1.5 rounded-lg text-sm font-medium ${page === pages ? 'bg-gray-100 dark:bg-white/5 text-text-muted dark:text-[#92adc9]/50 cursor-not-allowed' : 'bg-card-light dark:bg-card-dark text-text-main dark:text-white hover:bg-slate-100 dark:hover:bg-white/10 border border-border-light dark:border-[#233648]'} transition-colors"
            ${page === pages ? 'disabled' : ''}>
            <span class="material-symbols-outlined text-[18px]">chevron_right</span>
        </button>
    `;
    
    paginationDiv.innerHTML = buttons;
}

// Change page
function changePage(page) {
    currentPage = page;
    loadDocuments();
}

// View document (preview in modal)
function viewDocument(id, fileType, filename) {
    const modalHtml = `
        <div id="document-preview-modal" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" onclick="closePreviewModal(event)">
            <div class="bg-card-light dark:bg-card-dark rounded-xl max-w-5xl w-full max-h-[90vh] overflow-hidden shadow-2xl" onclick="event.stopPropagation()">
                <div class="flex items-center justify-between p-4 border-b border-border-light dark:border-[#233648]">
                    <h3 class="text-lg font-semibold text-text-main dark:text-white truncate">${escapeHtml(filename)}</h3>
                    <button onclick="closePreviewModal()" class="p-2 text-text-muted dark:text-[#92adc9] hover:text-text-main dark:hover:text-white rounded-lg transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="p-4 overflow-auto max-h-[calc(90vh-80px)]">
                    ${fileType.toUpperCase() === 'PDF' 
                        ? `<iframe src="/api/documents/${id}/view" class="w-full h-[70vh] border-0 rounded-lg"></iframe>`
                        : `<img src="/api/documents/${id}/view" alt="${escapeHtml(filename)}" class="max-w-full h-auto mx-auto rounded-lg">`
                    }
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

// Close preview modal
function closePreviewModal(event) {
    if (!event || event.target.id === 'document-preview-modal' || !event.target.closest) {
        const modal = document.getElementById('document-preview-modal');
        if (modal) {
            modal.remove();
        }
    }
}

// Download document
async function downloadDocument(id) {
    try {
        const response = await fetch(`/api/documents/${id}/download`);
        
        if (!response.ok) {
            throw new Error('Download failed');
        }
        
        const blob = await response.blob();
        const contentDisposition = response.headers.get('Content-Disposition');
        const filename = contentDisposition 
            ? contentDisposition.split('filename=')[1].replace(/"/g, '')
            : `document_${id}`;
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showNotification('success', 'Document downloaded successfully!');
    } catch (error) {
        console.error('Download error:', error);
        showNotification('error', 'Failed to download document');
    }
}

// Delete document
async function deleteDocument(id) {
    const confirmMsg = getCurrentLanguage() === 'ro' 
        ? 'Ești sigur că vrei să ștergi acest document? Această acțiune nu poate fi anulată.'
        : 'Are you sure you want to delete this document? This action cannot be undone.';
    
    if (!confirm(confirmMsg)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/documents/${id}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('success', 'Document deleted successfully!');
            loadDocuments();
        } else {
            showNotification('error', result.error || 'Failed to delete document');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('error', 'An error occurred while deleting');
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) {
        const hours = Math.floor(diff / (1000 * 60 * 60));
        if (hours === 0) {
            const minutes = Math.floor(diff / (1000 * 60));
            return minutes <= 1 ? 'Just now' : `${minutes}m ago`;
        }
        return `${hours}h ago`;
    } else if (days === 1) {
        return 'Yesterday';
    } else if (days < 7) {
        return `${days}d ago`;
    } else {
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show notification
function showNotification(type, message) {
    // Create notification element
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
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.add('animate-slideOut');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}
