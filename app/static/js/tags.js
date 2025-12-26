// Tags Management JavaScript
// Handles tag creation, editing, filtering, and display

let allTags = [];
let selectedTags = [];

// Load all tags for current user
async function loadTags() {
    try {
        const response = await apiCall('/api/tags/?sort_by=use_count&order=desc');
        if (response.success) {
            allTags = response.tags;
            return allTags;
        }
    } catch (error) {
        console.error('Failed to load tags:', error);
        return [];
    }
}

// Load popular tags (most used)
async function loadPopularTags(limit = 10) {
    try {
        const response = await apiCall(`/api/tags/popular?limit=${limit}`);
        if (response.success) {
            return response.tags;
        }
    } catch (error) {
        console.error('Failed to load popular tags:', error);
        return [];
    }
}

// Create a new tag
async function createTag(tagData) {
    try {
        const response = await apiCall('/api/tags/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(tagData)
        });
        
        if (response.success) {
            showToast(window.getTranslation('tags.created', 'Tag created successfully'), 'success');
            await loadTags();
            return response.tag;
        } else {
            showToast(response.message || window.getTranslation('tags.errorCreating', 'Error creating tag'), 'error');
            return null;
        }
    } catch (error) {
        console.error('Failed to create tag:', error);
        showToast(window.getTranslation('tags.errorCreating', 'Error creating tag'), 'error');
        return null;
    }
}

// Update an existing tag
async function updateTag(tagId, tagData) {
    try {
        const response = await apiCall(`/api/tags/${tagId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(tagData)
        });
        
        if (response.success) {
            showToast(window.getTranslation('tags.updated', 'Tag updated successfully'), 'success');
            await loadTags();
            return response.tag;
        } else {
            showToast(response.message || window.getTranslation('tags.errorUpdating', 'Error updating tag'), 'error');
            return null;
        }
    } catch (error) {
        console.error('Failed to update tag:', error);
        showToast(window.getTranslation('tags.errorUpdating', 'Error updating tag'), 'error');
        return null;
    }
}

// Delete a tag
async function deleteTag(tagId) {
    const confirmMsg = window.getTranslation('tags.deleteConfirm', 'Are you sure you want to delete this tag?');
    if (!confirm(confirmMsg)) {
        return false;
    }
    
    try {
        const response = await apiCall(`/api/tags/${tagId}`, {
            method: 'DELETE'
        });
        
        if (response.success) {
            showToast(window.getTranslation('tags.deleted', 'Tag deleted successfully'), 'success');
            await loadTags();
            return true;
        } else {
            showToast(response.message || window.getTranslation('tags.errorDeleting', 'Error deleting tag'), 'error');
            return false;
        }
    } catch (error) {
        console.error('Failed to delete tag:', error);
        showToast(window.getTranslation('tags.errorDeleting', 'Error deleting tag'), 'error');
        return false;
    }
}

// Get tag suggestions based on text
async function getTagSuggestions(text, maxTags = 5) {
    try {
        const response = await apiCall('/api/tags/suggest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, max_tags: maxTags })
        });
        
        if (response.success) {
            return response.suggested_tags;
        }
        return [];
    } catch (error) {
        console.error('Failed to get tag suggestions:', error);
        return [];
    }
}

// Render a single tag badge
function renderTagBadge(tag, options = {}) {
    const { removable = false, clickable = false, onRemove = null, onClick = null } = options;
    
    const badge = document.createElement('span');
    badge.className = 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all';
    badge.style.backgroundColor = `${tag.color}20`;
    badge.style.borderColor = `${tag.color}40`;
    badge.style.color = tag.color;
    badge.classList.add('border');
    
    if (clickable) {
        badge.classList.add('cursor-pointer', 'hover:brightness-110');
        badge.addEventListener('click', () => onClick && onClick(tag));
    }
    
    // Icon
    const icon = document.createElement('span');
    icon.className = 'material-symbols-outlined';
    icon.style.fontSize = '14px';
    icon.textContent = tag.icon || 'label';
    badge.appendChild(icon);
    
    // Tag name
    const name = document.createElement('span');
    name.textContent = tag.name;
    badge.appendChild(name);
    
    // Use count (optional)
    if (tag.use_count > 0 && !removable) {
        const count = document.createElement('span');
        count.className = 'opacity-60';
        count.textContent = `(${tag.use_count})`;
        badge.appendChild(count);
    }
    
    // Remove button (optional)
    if (removable) {
        const removeBtn = document.createElement('button');
        removeBtn.className = 'ml-1 hover:bg-black hover:bg-opacity-10 rounded-full p-0.5';
        removeBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 14px;">close</span>';
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            onRemove && onRemove(tag);
        });
        badge.appendChild(removeBtn);
    }
    
    return badge;
}

// Render tags list in a container
function renderTagsList(tags, containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    
    if (tags.length === 0) {
        const emptyMsg = document.createElement('p');
        emptyMsg.className = 'text-text-muted dark:text-[#92adc9] text-sm';
        emptyMsg.textContent = window.getTranslation('tags.noTags', 'No tags yet');
        container.appendChild(emptyMsg);
        return;
    }
    
    tags.forEach(tag => {
        const badge = renderTagBadge(tag, options);
        container.appendChild(badge);
    });
}

// Create a tag filter dropdown
function createTagFilterDropdown(containerId, onSelectionChange) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="relative">
            <button id="tagFilterBtn" class="flex items-center gap-2 px-4 py-2 bg-white dark:bg-[#0a1628] border border-gray-200 dark:border-white/10 rounded-lg hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                <span class="material-symbols-outlined text-[20px]">label</span>
                <span data-translate="tags.filterByTags">Filter by Tags</span>
                <span class="material-symbols-outlined text-[16px]">expand_more</span>
            </button>
            
            <div id="tagFilterDropdown" class="absolute top-full left-0 mt-2 w-72 bg-white dark:bg-[#0a1628] border border-gray-200 dark:border-white/10 rounded-lg shadow-lg p-4 hidden z-50">
                <div class="mb-3">
                    <input type="text" id="tagFilterSearch" placeholder="${window.getTranslation('tags.selectTags', 'Select tags...')}" class="w-full px-3 py-2 bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg text-sm">
                </div>
                <div id="tagFilterList" class="max-h-64 overflow-y-auto space-y-2">
                    <!-- Tag checkboxes will be inserted here -->
                </div>
                <div class="mt-3 pt-3 border-t border-gray-200 dark:border-white/10">
                    <button id="clearTagFilters" class="text-sm text-primary hover:underline">Clear all</button>
                </div>
            </div>
        </div>
    `;
    
    const btn = container.querySelector('#tagFilterBtn');
    const dropdown = container.querySelector('#tagFilterDropdown');
    const searchInput = container.querySelector('#tagFilterSearch');
    const listContainer = container.querySelector('#tagFilterList');
    const clearBtn = container.querySelector('#clearTagFilters');
    
    // Toggle dropdown
    btn.addEventListener('click', async () => {
        dropdown.classList.toggle('hidden');
        if (!dropdown.classList.contains('hidden')) {
            await renderTagFilterList(listContainer, searchInput, onSelectionChange);
        }
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!container.contains(e.target)) {
            dropdown.classList.add('hidden');
        }
    });
    
    // Clear filters
    clearBtn.addEventListener('click', () => {
        selectedTags = [];
        renderTagFilterList(listContainer, searchInput, onSelectionChange);
        onSelectionChange(selectedTags);
    });
}

// Render tag filter list with checkboxes
async function renderTagFilterList(listContainer, searchInput, onSelectionChange) {
    const tags = await loadTags();
    
    const renderList = (filteredTags) => {
        listContainer.innerHTML = '';
        
        filteredTags.forEach(tag => {
            const item = document.createElement('label');
            item.className = 'flex items-center gap-2 p-2 hover:bg-gray-50 dark:hover:bg-white/5 rounded cursor-pointer';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = tag.id;
            checkbox.checked = selectedTags.includes(tag.id);
            checkbox.className = 'rounded';
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    selectedTags.push(tag.id);
                } else {
                    selectedTags = selectedTags.filter(id => id !== tag.id);
                }
                onSelectionChange(selectedTags);
            });
            
            const badge = renderTagBadge(tag, {});
            
            item.appendChild(checkbox);
            item.appendChild(badge);
            listContainer.appendChild(item);
        });
    };
    
    // Initial render
    renderList(tags);
    
    // Search functionality
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const filtered = tags.filter(tag => tag.name.toLowerCase().includes(query));
        renderList(filtered);
    });
}

// Make functions globally available
window.loadTags = loadTags;
window.loadPopularTags = loadPopularTags;
window.createTag = createTag;
window.updateTag = updateTag;
window.deleteTag = deleteTag;
window.getTagSuggestions = getTagSuggestions;
window.renderTagBadge = renderTagBadge;
window.renderTagsList = renderTagsList;
window.createTagFilterDropdown = createTagFilterDropdown;
