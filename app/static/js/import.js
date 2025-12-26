/**
 * CSV/Bank Statement Import Module for FINA PWA
 * Handles file upload, parsing, duplicate detection, and category mapping
 */

class CSVImporter {
    constructor() {
        this.parsedTransactions = [];
        this.duplicates = [];
        this.categoryMapping = {};
        this.userCategories = [];
        this.currentStep = 1;
    }

    /**
     * Initialize the importer
     */
    async init() {
        await this.loadUserProfile();
        await this.loadUserCategories();
        this.renderImportUI();
        this.setupEventListeners();
    }

    /**
     * Load user profile to get currency
     */
    async loadUserProfile() {
        try {
            const response = await window.apiCall('/api/settings/profile');
            window.userCurrency = response.profile?.currency || 'USD';
        } catch (error) {
            console.error('Failed to load user profile:', error);
            window.userCurrency = 'USD';
        }
    }

    /**
     * Load user's categories from API
     */
    async loadUserCategories() {
        try {
            const response = await window.apiCall('/api/expenses/categories');
            this.userCategories = response.categories || [];
        } catch (error) {
            console.error('Failed to load categories:', error);
            this.userCategories = [];
            window.showToast(window.getTranslation('import.errorLoadingCategories', 'Failed to load categories'), 'error');
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // File input change
        const fileInput = document.getElementById('csvFileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }

        // Drag and drop
        const dropZone = document.getElementById('csvDropZone');
        if (dropZone) {
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('border-primary', 'bg-primary/5');
            });

            dropZone.addEventListener('dragleave', () => {
                dropZone.classList.remove('border-primary', 'bg-primary/5');
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('border-primary', 'bg-primary/5');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFile(files[0]);
                }
            });
        }
    }

    /**
     * Render the import UI
     */
    renderImportUI() {
        const container = document.getElementById('importContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="max-w-4xl mx-auto">
                <!-- Progress Steps -->
                <div class="mb-8">
                    <div class="flex items-center justify-between">
                        ${this.renderStep(1, 'import.stepUpload', 'Upload CSV')}
                        ${this.renderStep(2, 'import.stepReview', 'Review')}
                        ${this.renderStep(3, 'import.stepMap', 'Map Categories')}
                        ${this.renderStep(4, 'import.stepImport', 'Import')}
                    </div>
                </div>

                <!-- Step Content -->
                <div id="stepContent" class="bg-white dark:bg-[#0f1921] rounded-xl p-6 border border-border-light dark:border-[#233648]">
                    ${this.renderCurrentStep()}
                </div>
            </div>
        `;
    }

    /**
     * Render a progress step
     */
    renderStep(stepNum, translationKey, fallback) {
        const isActive = this.currentStep === stepNum;
        const isComplete = this.currentStep > stepNum;
        
        return `
            <div class="flex items-center ${stepNum < 4 ? 'flex-1' : ''}">
                <div class="flex items-center">
                    <div class="w-10 h-10 rounded-full flex items-center justify-center font-semibold
                                ${isComplete ? 'bg-green-500 text-white' : ''}
                                ${isActive ? 'bg-primary text-white' : ''}
                                ${!isActive && !isComplete ? 'bg-slate-200 dark:bg-[#233648] text-text-muted' : ''}">
                        ${isComplete ? '<span class="material-symbols-outlined text-[20px]">check</span>' : stepNum}
                    </div>
                    <span class="ml-2 text-sm font-medium ${isActive ? 'text-primary' : 'text-text-muted dark:text-[#92adc9]'}">
                        ${window.getTranslation(translationKey, fallback)}
                    </span>
                </div>
                ${stepNum < 4 ? '<div class="flex-1 h-0.5 bg-slate-200 dark:bg-[#233648] mx-4"></div>' : ''}
            </div>
        `;
    }

    /**
     * Render content for current step
     */
    renderCurrentStep() {
        switch (this.currentStep) {
            case 1:
                return this.renderUploadStep();
            case 2:
                return this.renderReviewStep();
            case 3:
                return this.renderMappingStep();
            case 4:
                return this.renderImportStep();
            default:
                return '';
        }
    }

    /**
     * Render upload step
     */
    renderUploadStep() {
        return `
            <div class="text-center">
                <h2 class="text-2xl font-bold mb-4 text-text-main dark:text-white">
                    ${window.getTranslation('import.uploadTitle', 'Upload CSV File')}
                </h2>
                <p class="text-text-muted dark:text-[#92adc9] mb-6">
                    ${window.getTranslation('import.uploadDesc', 'Upload your bank statement or expense CSV file')}
                </p>

                <!-- Drop Zone -->
                <div id="csvDropZone" 
                     class="border-2 border-dashed border-border-light dark:border-[#233648] rounded-xl p-12 cursor-pointer hover:border-primary/50 transition-colors"
                     onclick="document.getElementById('csvFileInput').click()">
                    <span class="material-symbols-outlined text-6xl text-text-muted dark:text-[#92adc9] mb-4">cloud_upload</span>
                    <p class="text-lg font-medium text-text-main dark:text-white mb-2">
                        ${window.getTranslation('import.dragDrop', 'Drag and drop your CSV file here')}
                    </p>
                    <p class="text-sm text-text-muted dark:text-[#92adc9] mb-4">
                        ${window.getTranslation('import.orClick', 'or click to browse')}
                    </p>
                    <input type="file" 
                           id="csvFileInput" 
                           accept=".csv" 
                           class="hidden">
                </div>

                <!-- Format Info -->
                <div class="mt-8 text-left bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                    <h3 class="font-semibold text-text-main dark:text-white mb-2 flex items-center">
                        <span class="material-symbols-outlined text-[20px] mr-2">info</span>
                        ${window.getTranslation('import.supportedFormats', 'Supported Formats')}
                    </h3>
                    <ul class="text-sm text-text-muted dark:text-[#92adc9] space-y-1">
                        <li>• ${window.getTranslation('import.formatRequirement1', 'CSV files with Date, Description, and Amount columns')}</li>
                        <li>• ${window.getTranslation('import.formatRequirement2', 'Supports comma, semicolon, or tab delimiters')}</li>
                        <li>• ${window.getTranslation('import.formatRequirement3', 'Date formats: DD/MM/YYYY, YYYY-MM-DD, etc.')}</li>
                        <li>• ${window.getTranslation('import.formatRequirement4', 'Maximum file size: 10MB')}</li>
                    </ul>
                </div>
            </div>
        `;
    }

    /**
     * Handle file selection
     */
    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            await this.handleFile(file);
        }
    }

    /**
     * Handle file upload and parsing
     */
    async handleFile(file) {
        // Validate file
        if (!file.name.toLowerCase().endsWith('.csv')) {
            window.showToast(window.getTranslation('import.errorInvalidFile', 'Please select a CSV file'), 'error');
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            window.showToast(window.getTranslation('import.errorFileTooLarge', 'File too large. Maximum 10MB'), 'error');
            return;
        }

        // Show loading
        const stepContent = document.getElementById('stepContent');
        stepContent.innerHTML = `
            <div class="text-center py-12">
                <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
                <p class="text-text-muted dark:text-[#92adc9]">${window.getTranslation('import.parsing', 'Parsing CSV file...')}</p>
            </div>
        `;

        try {
            // Upload and parse
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/import/parse-csv', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || 'Failed to parse CSV');
            }

            this.parsedTransactions = result.transactions;

            // Check for duplicates
            await this.checkDuplicates();

            // Move to review step
            this.currentStep = 2;
            this.renderImportUI();

        } catch (error) {
            console.error('Failed to parse CSV:', error);
            window.showToast(error.message || window.getTranslation('import.errorParsing', 'Failed to parse CSV file'), 'error');
            this.currentStep = 1;
            this.renderImportUI();
        }
    }

    /**
     * Check for duplicate transactions
     */
    async checkDuplicates() {
        try {
            const response = await fetch('/api/import/detect-duplicates', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    transactions: this.parsedTransactions
                })
            });

            const result = await response.json();

            if (result.success) {
                this.duplicates = result.duplicates || [];
                
                // Mark transactions as duplicates
                this.parsedTransactions.forEach((trans, idx) => {
                    const isDuplicate = this.duplicates.some(d => 
                        d.transaction.date === trans.date && 
                        d.transaction.amount === trans.amount &&
                        d.transaction.description === trans.description
                    );
                    this.parsedTransactions[idx].is_duplicate = isDuplicate;
                });
            }
        } catch (error) {
            console.error('Failed to check duplicates:', error);
        }
    }

    /**
     * Render review step
     */
    renderReviewStep() {
        const duplicateCount = this.parsedTransactions.filter(t => t.is_duplicate).length;
        const newCount = this.parsedTransactions.length - duplicateCount;

        return `
            <div>
                <h2 class="text-2xl font-bold mb-4 text-text-main dark:text-white">
                    ${window.getTranslation('import.reviewTitle', 'Review Transactions')}
                </h2>
                
                <!-- Summary -->
                <div class="grid grid-cols-3 gap-4 mb-6">
                    <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                        <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">${this.parsedTransactions.length}</div>
                        <div class="text-sm text-text-muted dark:text-[#92adc9]">${window.getTranslation('import.totalFound', 'Total Found')}</div>
                    </div>
                    <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                        <div class="text-2xl font-bold text-green-600 dark:text-green-400">${newCount}</div>
                        <div class="text-sm text-text-muted dark:text-[#92adc9]">${window.getTranslation('import.newTransactions', 'New')}</div>
                    </div>
                    <div class="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
                        <div class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">${duplicateCount}</div>
                        <div class="text-sm text-text-muted dark:text-[#92adc9]">${window.getTranslation('import.duplicates', 'Duplicates')}</div>
                    </div>
                </div>

                <!-- Transactions List -->
                <div class="mb-6 max-h-96 overflow-y-auto">
                    ${this.parsedTransactions.map((trans, idx) => this.renderTransactionRow(trans, idx)).join('')}
                </div>

                <!-- Actions -->
                <div class="flex justify-between">
                    <button onclick="csvImporter.goToStep(1)" 
                            class="px-6 py-2 border border-border-light dark:border-[#233648] rounded-lg text-text-main dark:text-white hover:bg-slate-100 dark:hover:bg-[#111a22]">
                        ${window.getTranslation('common.back', 'Back')}
                    </button>
                    <button onclick="csvImporter.goToStep(3)" 
                            class="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
                        ${window.getTranslation('import.nextMapCategories', 'Next: Map Categories')}
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Render a transaction row
     */
    renderTransactionRow(trans, idx) {
        const isDuplicate = trans.is_duplicate;
        
        return `
            <div class="flex items-center justify-between p-3 border-b border-border-light dark:border-[#233648] ${isDuplicate ? 'bg-yellow-50/50 dark:bg-yellow-900/10' : ''}">
                <div class="flex items-center gap-4 flex-1">
                    <input type="checkbox" 
                           id="trans_${idx}" 
                           ${isDuplicate ? '' : 'checked'}
                           onchange="csvImporter.toggleTransaction(${idx})"
                           class="w-5 h-5 rounded border-border-light dark:border-[#233648]">
                    <div class="flex-1">
                        <div class="flex items-center gap-2">
                            <span class="font-medium text-text-main dark:text-white">${trans.description}</span>
                            ${isDuplicate ? '<span class="px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 text-xs rounded-full">' + window.getTranslation('import.duplicate', 'Duplicate') + '</span>' : ''}
                        </div>
                        <div class="text-sm text-text-muted dark:text-[#92adc9]">${trans.date}</div>
                    </div>
                </div>
                <div class="font-semibold text-text-main dark:text-white">${window.formatCurrency(trans.amount, trans.currency || window.userCurrency || 'GBP')}</div>
            </div>
        `;
    }

    /**
     * Check for missing categories and offer to create them
     */
    async checkAndCreateCategories() {
        const selectedTransactions = this.parsedTransactions.filter(t => {
            const checkbox = document.getElementById(`trans_${this.parsedTransactions.indexOf(t)}`);
            return !checkbox || checkbox.checked;
        });

        // Get unique bank categories (skip generic payment types)
        const paymentTypes = ['pot transfer', 'card payment', 'direct debit', 'monzo_paid', 
                             'faster payment', 'bacs (direct credit)', 'bacs', 'standing order'];
        const bankCategories = new Set();
        selectedTransactions.forEach(trans => {
            if (trans.bank_category && trans.bank_category.trim()) {
                const catLower = trans.bank_category.trim().toLowerCase();
                // Skip if it's a generic payment type
                if (!paymentTypes.includes(catLower)) {
                    bankCategories.add(trans.bank_category.trim());
                }
            }
        });

        if (bankCategories.size === 0) {
            return; // No bank categories to create
        }

        // Find which categories don't exist
        const existingCatNames = new Set(this.userCategories.map(c => c.name.toLowerCase()));
        const missingCategories = Array.from(bankCategories).filter(
            cat => !existingCatNames.has(cat.toLowerCase())
        );

        if (missingCategories.length > 0) {
            // Show confirmation dialog
            const confirmCreate = confirm(
                window.getTranslation(
                    'import.createMissingCategories',
                    `Found ${missingCategories.length} new categories from your CSV:\n\n${missingCategories.join('\n')}\n\nWould you like to create these categories automatically?`
                )
            );

            if (confirmCreate) {
                try {
                    const response = await window.apiCall('/api/import/create-categories', {
                        method: 'POST',
                        body: JSON.stringify({
                            bank_categories: missingCategories
                        })
                    });

                    if (response.success) {
                        window.showToast(
                            window.getTranslation(
                                'import.categoriesCreated',
                                `Created ${response.created.length} new categories`
                            ),
                            'success'
                        );

                        // Update category mapping with new categories
                        Object.assign(this.categoryMapping, response.mapping);

                        // Reload categories
                        await this.loadUserCategories();
                        this.renderImportUI();
                        this.setupEventListeners();
                    }
                } catch (error) {
                    console.error('Failed to create categories:', error);
                    window.showToast(
                        window.getTranslation('import.errorCreatingCategories', 'Failed to create categories'),
                        'error'
                    );
                }
            }
        }
    }

    /**
     * Toggle transaction selection
     */
    toggleTransaction(idx) {
        const checkbox = document.getElementById(`trans_${idx}`);
        this.parsedTransactions[idx].selected = checkbox.checked;
    }

    /**
     * Render mapping step
     */
    renderMappingStep() {
        const selectedTransactions = this.parsedTransactions.filter(t => {
            const checkbox = document.getElementById(`trans_${this.parsedTransactions.indexOf(t)}`);
            return !checkbox || checkbox.checked;
        });

        // Get unique bank categories or descriptions for mapping (skip payment types)
        const paymentTypes = ['pot transfer', 'card payment', 'direct debit', 'monzo_paid', 
                             'faster payment', 'bacs (direct credit)', 'bacs', 'standing order'];
        const needsMapping = new Set();
        selectedTransactions.forEach(trans => {
            if (trans.bank_category) {
                const catLower = trans.bank_category.toLowerCase();
                // Skip generic payment types
                if (!paymentTypes.includes(catLower)) {
                    needsMapping.add(trans.bank_category);
                }
            }
        });

        return `
            <div>
                <h2 class="text-2xl font-bold mb-4 text-text-main dark:text-white">
                    ${window.getTranslation('import.mapCategories', 'Map Categories')}
                </h2>
                <p class="text-text-muted dark:text-[#92adc9] mb-6">
                    ${window.getTranslation('import.mapCategoriesDesc', 'Assign categories to your transactions')}
                </p>

                ${needsMapping.size > 0 ? `
                    <div class="mb-6">
                        <h3 class="font-semibold mb-4 text-text-main dark:text-white">${window.getTranslation('import.bankCategoryMapping', 'Bank Category Mapping')}</h3>
                        ${Array.from(needsMapping).map(bankCat => this.renderCategoryMapping(bankCat)).join('')}
                    </div>
                ` : ''}

                <div class="mb-6">
                    <h3 class="font-semibold mb-4 text-text-main dark:text-white">${window.getTranslation('import.defaultCategory', 'Default Category')}</h3>
                    <select id="defaultCategory" class="w-full px-4 py-2 border border-border-light dark:border-[#233648] rounded-lg bg-white dark:bg-[#111a22] text-text-main dark:text-white">
                        ${this.userCategories.map(cat => `
                            <option value="${cat.id}">${cat.name}</option>
                        `).join('')}
                    </select>
                    <p class="text-xs text-text-muted dark:text-[#92adc9] mt-2">
                        ${window.getTranslation('import.defaultCategoryDesc', 'Used for transactions without bank category')}
                    </p>
                </div>

                <!-- Actions -->
                <div class="flex justify-between">
                    <button onclick="csvImporter.goToStep(2)" 
                            class="px-6 py-2 border border-border-light dark:border-[#233648] rounded-lg text-text-main dark:text-white hover:bg-slate-100 dark:hover:bg-[#111a22]">
                        ${window.getTranslation('common.back', 'Back')}
                    </button>
                    <button onclick="csvImporter.startImport()" 
                            class="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 flex items-center gap-2">
                        <span class="material-symbols-outlined text-[20px]">download</span>
                        ${window.getTranslation('import.startImport', 'Import Transactions')}
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Render category mapping dropdown
     */
    renderCategoryMapping(bankCategory) {
        return `
            <div class="mb-4 flex items-center gap-4">
                <div class="flex-1">
                    <div class="font-medium text-text-main dark:text-white mb-1">${bankCategory}</div>
                    <div class="text-sm text-text-muted dark:text-[#92adc9]">${window.getTranslation('import.bankCategory', 'Bank Category')}</div>
                </div>
                <span class="text-text-muted">→</span>
                <select id="mapping_${bankCategory.replace(/[^a-zA-Z0-9]/g, '_')}" 
                        onchange="csvImporter.setMapping('${bankCategory}', this.value)"
                        class="flex-1 px-4 py-2 border border-border-light dark:border-[#233648] rounded-lg bg-white dark:bg-[#111a22] text-text-main dark:text-white">
                    ${this.userCategories.map(cat => `
                        <option value="${cat.id}">${cat.name}</option>
                    `).join('')}
                </select>
            </div>
        `;
    }

    /**
     * Set category mapping
     */
    setMapping(bankCategory, categoryId) {
        this.categoryMapping[bankCategory] = parseInt(categoryId);
    }

    /**
     * Start import process
     */
    async startImport() {
        const selectedTransactions = this.parsedTransactions.filter((t, idx) => {
            const checkbox = document.getElementById(`trans_${idx}`);
            return !checkbox || checkbox.checked;
        });

        if (selectedTransactions.length === 0) {
            window.showToast(window.getTranslation('import.noTransactionsSelected', 'No transactions selected'), 'error');
            return;
        }

        // Show loading
        this.currentStep = 4;
        this.renderImportUI();

        try {
            const response = await window.apiCall('/api/import/import', {
                method: 'POST',
                body: JSON.stringify({
                    transactions: selectedTransactions,
                    category_mapping: this.categoryMapping,
                    skip_duplicates: true
                })
            });

            if (response.success) {
                this.renderImportComplete(response);
            } else {
                throw new Error(response.error || 'Import failed');
            }
        } catch (error) {
            console.error('Import failed:', error);
            window.showToast(error.message || window.getTranslation('import.errorImporting', 'Failed to import transactions'), 'error');
            this.goToStep(3);
        }
    }

    /**
     * Render import complete step
     */
    renderImportStep() {
        return `
            <div class="text-center py-12">
                <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
                <p class="text-text-muted dark:text-[#92adc9]">${window.getTranslation('import.importing', 'Importing transactions...')}</p>
            </div>
        `;
    }

    /**
     * Render import complete
     */
    renderImportComplete(result) {
        const stepContent = document.getElementById('stepContent');
        const hasErrors = result.errors && result.errors.length > 0;
        
        stepContent.innerHTML = `
            <div class="text-center">
                <div class="inline-block w-20 h-20 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-6">
                    <span class="material-symbols-outlined text-5xl text-green-600 dark:text-green-400">check_circle</span>
                </div>
                
                <h2 class="text-2xl font-bold mb-4 text-text-main dark:text-white">
                    ${window.getTranslation('import.importComplete', 'Import Complete!')}
                </h2>
                
                <div class="grid grid-cols-3 gap-4 mb-8 max-w-2xl mx-auto">
                    <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                        <div class="text-2xl font-bold text-green-600 dark:text-green-400">${result.imported_count}</div>
                        <div class="text-sm text-text-muted dark:text-[#92adc9]">${window.getTranslation('import.imported', 'Imported')}</div>
                    </div>
                    <div class="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
                        <div class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">${result.skipped_count}</div>
                        <div class="text-sm text-text-muted dark:text-[#92adc9]">${window.getTranslation('import.skipped', 'Skipped')}</div>
                    </div>
                    <div class="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                        <div class="text-2xl font-bold text-red-600 dark:text-red-400">${result.error_count}</div>
                        <div class="text-sm text-text-muted dark:text-[#92adc9]">${window.getTranslation('import.errors', 'Errors')}</div>
                    </div>
                </div>

                ${hasErrors ? `
                    <div class="mb-6 text-left max-w-2xl mx-auto">
                        <details class="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-900/20 rounded-lg p-4">
                            <summary class="cursor-pointer font-semibold text-red-600 dark:text-red-400 mb-2">
                                ${window.getTranslation('import.viewErrors', 'View Error Details')} (${result.error_count})
                            </summary>
                            <div class="mt-4 space-y-2 max-h-64 overflow-y-auto">
                                ${result.errors.slice(0, 20).map((err, idx) => `
                                    <div class="text-sm p-3 bg-white dark:bg-[#111a22] border border-red-100 dark:border-red-900/30 rounded">
                                        <div class="font-medium text-text-main dark:text-white mb-1">
                                            ${err.transaction?.description || 'Transaction ' + (idx + 1)}
                                        </div>
                                        <div class="text-red-600 dark:text-red-400 text-xs">${err.error}</div>
                                    </div>
                                `).join('')}
                                ${result.errors.length > 20 ? `
                                    <div class="text-sm text-text-muted dark:text-[#92adc9] italic p-2">
                                        ... and ${result.errors.length - 20} more errors
                                    </div>
                                ` : ''}
                            </div>
                        </details>
                    </div>
                ` : ''}

                <div class="flex gap-4 justify-center">
                    <button onclick="window.location.href='/transactions'" 
                            class="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
                        ${window.getTranslation('import.viewTransactions', 'View Transactions')}
                    </button>
                    <button onclick="csvImporter.reset()" 
                            class="px-6 py-2 border border-border-light dark:border-[#233648] rounded-lg text-text-main dark:text-white hover:bg-slate-100 dark:hover:bg-[#111a22]">
                        ${window.getTranslation('import.importAnother', 'Import Another File')}
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Go to a specific step
     */
    async goToStep(step) {
        this.currentStep = step;
        
        // If going to mapping step, check for missing categories
        if (step === 3) {
            await this.checkAndCreateCategories();
        }
        
        this.renderImportUI();
        this.setupEventListeners();
    }

    /**
     * Reset importer
     */
    reset() {
        this.parsedTransactions = [];
        this.duplicates = [];
        this.categoryMapping = {};
        this.currentStep = 1;
        this.renderImportUI();
    }
}

// Create global instance
window.csvImporter = new CSVImporter();

// Initialize on import page
if (window.location.pathname === '/import' || window.location.pathname.includes('import')) {
    document.addEventListener('DOMContentLoaded', () => {
        window.csvImporter.init();
    });
}
