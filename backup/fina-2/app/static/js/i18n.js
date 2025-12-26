// Multi-language support

const translations = {
    en: {
        // Navigation
        'nav.dashboard': 'Dashboard',
        'nav.transactions': 'Transactions',
        'nav.reports': 'Reports',
        'nav.admin': 'Admin',
        'nav.settings': 'Settings',
        'nav.logout': 'Log out',
        
        // Dashboard
        'dashboard.total_spent': 'Total Spent This Month',
        'dashboard.active_categories': 'Active Categories',
        'dashboard.total_transactions': 'Total Transactions',
        'dashboard.vs_last_month': 'vs last month',
        'dashboard.categories_in_use': 'categories in use',
        'dashboard.this_month': 'current month',
        'dashboard.spending_by_category': 'Spending by Category',
        'dashboard.monthly_trend': 'Monthly Trend',
        'dashboard.recent_transactions': 'Recent Transactions',
        'dashboard.view_all': 'View All',
        'dashboard.search': 'Search expenses...',
        'dashboard.selectCategory': 'Select category...',
        'dashboard.noTransactions': 'No transactions yet',
        'dashboard.noData': 'No data available',
        'dashboard.total': 'Total',
        'dashboard.totalThisYear': 'Total This Year',
        'dashboard.spending': 'Spending',
        'dashboard.categoryBreakdownDesc': 'Breakdown by category',
        'dashboard.lightMode': 'Light Mode',
        'dashboard.darkMode': 'Dark Mode',
        'dashboard.expenseAdded': 'Expense added successfully!',
        
        // Login
        'login.title': 'Welcome Back',
        'login.tagline': 'Track your expenses, manage your finances',
        'login.remember_me': 'Remember me',
        'login.sign_in': 'Sign In',
        'login.no_account': "Don't have an account?",
        'login.register': 'Register',
        
        // Register
        'register.title': 'Create Account',
        'register.tagline': 'Start managing your finances today',
        'register.create_account': 'Create Account',
        'register.have_account': 'Already have an account?',
        'register.login': 'Login',
        
        // Forms
        'form.email': 'Email',
        'form.password': 'Password',
        'form.username': 'Username',
        'form.language': 'Language',
        'form.currency': 'Currency',
        'form.monthlyBudget': 'Monthly Budget',
        'form.amount': 'Amount',
        'form.description': 'Description',
        'form.category': 'Category',
        'form.date': 'Date',
        'form.tags': 'Tags (comma separated)',
        'form.receipt': 'Receipt (optional)',
        'form.2fa_code': '2FA Code',
        'form.chooseFile': 'Choose File',
        'form.noFileChosen': 'No file chosen',
        
        // Transactions
        'transactions.title': 'Transactions',
        'transactions.export': 'Export CSV',
        'transactions.import': 'Import CSV',
        'transactions.addExpense': 'Add Expense',
        'transactions.search': 'Search transactions...',
        'transactions.date': 'Date',
        'transactions.filters': 'Filters',
        'transactions.category': 'Category',
        'transactions.allCategories': 'Category',
        'transactions.startDate': 'Start Date',
        'transactions.endDate': 'End Date',
        'transactions.tableTransaction': 'Transaction',
        'transactions.tableCategory': 'Category',
        'transactions.tableDate': 'Date',
        'transactions.tablePayment': 'Payment',
        'transactions.tableAmount': 'Amount',
        'transactions.tableStatus': 'Status',
        'transactions.tableActions': 'Actions',
        'transactions.showing': 'Showing',
        'transactions.to': 'to',
        'transactions.of': 'of',
        'transactions.results': 'results',
        'transactions.previous': 'Previous',
        'transactions.next': 'Next',
        'transactions.noTransactions': 'No transactions found',
        'transactions.expense': 'Expense',
        'transactions.completed': 'Completed',
        'transactions.pending': 'Pending',
        'transactions.edit': 'Edit',
        'transactions.delete': 'Delete',
        'transactions.updated': 'Transaction updated successfully!',
        'transactions.notFound': 'Transaction not found',
        'modal.edit_expense': 'Edit Expense',
        'actions.update': 'Update Expense',
        'form.currentReceipt': 'Current receipt attached',
        'form.receiptHelp': 'Upload a new file to replace existing receipt',
        'transactions.viewReceipt': 'View Receipt',
        'transactions.downloadReceipt': 'Download Receipt',
        'transactions.transaction': 'transaction',
        'transactions.transactions': 'transactions',
        'transactions.deleteConfirm': 'Are you sure you want to delete this transaction?',
        'transactions.deleted': 'Transaction deleted',
        'transactions.imported': 'Imported',
        'transactions.importSuccess': 'transactions',
        
        // Actions
        'actions.add_expense': 'Add Expense',
        'actions.save': 'Save Expense',
        
        // Modal
        'modal.add_expense': 'Add Expense',
        
        // Reports
        'reports.title': 'Financial Reports',
        'reports.export': 'Export CSV',
        'reports.analysisPeriod': 'Analysis Period:',
        'reports.last30Days': 'Last 30 Days',
        'reports.quarter': 'Quarter',
        'reports.ytd': 'YTD',
        'reports.allCategories': 'All Categories',
        'reports.generate': 'Generate Report',
        'reports.totalSpent': 'Total Spent',
        'reports.topCategory': 'Top Category',
        'reports.avgDaily': 'Avg. Daily',
        'reports.savingsRate': 'Savings Rate',
        'reports.vsLastMonth': 'vs last period',
        'reports.spentThisPeriod': 'spent this period',
        'reports.placeholder': 'Placeholder',
        'reports.spendingTrend': 'Spending Trend',
        'reports.categoryBreakdown': 'Category Breakdown',
        'reports.monthlySpending': 'Monthly Spending',
        'reports.smartRecommendations': 'Smart Recommendations',
        'reports.noRecommendations': 'No recommendations at this time',
        
        // User
        'user.admin': 'Admin',
        'user.user': 'User',
        
        // Documents
        'nav.documents': 'Documents',
        'documents.title': 'Documents',
        'documents.uploadTitle': 'Upload Documents',
        'documents.dragDrop': 'Drag & drop files here or click to browse',
        'documents.uploadDesc': 'Upload bank statements, invoices, or receipts.',
        'documents.supportedFormats': 'Supported formats: CSV, PDF, XLS, XLSX, PNG, JPG (Max 10MB)',
        'documents.yourFiles': 'Your Files',
        'documents.searchPlaceholder': 'Search by name...',
        'documents.tableDocName': 'Document Name',
        'documents.tableUploadDate': 'Upload Date',
        'documents.tableType': 'Type',
        'documents.tableStatus': 'Status',
        'documents.tableActions': 'Actions',
        'documents.statusUploaded': 'Uploaded',
        'documents.statusProcessing': 'Processing',
        'documents.statusAnalyzed': 'Analyzed',
        'documents.statusError': 'Error',
        'documents.showing': 'Showing',
        'documents.of': 'of',
        'documents.documents': 'documents',
        'documents.noDocuments': 'No documents found. Upload your first document!',
        'documents.errorLoading': 'Failed to load documents. Please try again.',
        
        // Settings
        'settings.title': 'Settings',
        'settings.avatar': 'Profile Avatar',
        'settings.uploadAvatar': 'Upload Custom',
        'settings.avatarDesc': 'PNG, JPG, GIF, WEBP. Max 20MB',
        'settings.defaultAvatars': 'Or choose a default avatar:',
        'settings.profile': 'Profile Information',
        'settings.saveProfile': 'Save Profile',
        'settings.changePassword': 'Change Password',
        'settings.currentPassword': 'Current Password',
        'settings.newPassword': 'New Password',
        'settings.confirmPassword': 'Confirm New Password',
        'settings.updatePassword': 'Update Password',
        'settings.twoFactor': 'Two-Factor Authentication',
        'settings.twoFactorEnabled': '2FA is currently enabled for your account',
        'settings.twoFactorDisabled': 'Add an extra layer of security to your account',
        'settings.enabled': 'Enabled',
        'settings.disabled': 'Disabled',
        'settings.regenerateCodes': 'Regenerate Backup Codes',
        'settings.enable2FA': 'Enable 2FA',
        'settings.disable2FA': 'Disable 2FA',
        
        // Two-Factor Authentication
        'twofa.setupTitle': 'Setup Two-Factor Authentication',
        'twofa.setupDesc': 'Scan the QR code with your authenticator app',
        'twofa.step1': 'Step 1: Scan QR Code',
        'twofa.step1Desc': 'Open your authenticator app (Google Authenticator, Authy, etc.) and scan this QR code:',
        'twofa.manualEntry': "Can't scan? Enter code manually",
        'twofa.enterManually': 'Enter this code in your authenticator app:',
        'twofa.step2': 'Step 2: Verify Code',
        'twofa.step2Desc': 'Enter the 6-digit code from your authenticator app:',
        'twofa.enable': 'Enable 2FA',
        'twofa.infoText': "After enabling 2FA, you'll receive backup codes that you can use if you lose access to your authenticator app. Keep them in a safe place!",
        'twofa.setupSuccess': 'Two-Factor Authentication Enabled!',
        'twofa.backupCodesDesc': 'Save these backup codes in a secure location',
        'twofa.important': 'Important!',
        'twofa.backupCodesWarning': "Each backup code can only be used once. Store them securely - you'll need them if you lose access to your authenticator app.",
        'twofa.yourBackupCodes': 'Your Backup Codes',
        'twofa.downloadPDF': 'Download as PDF',
        'twofa.print': 'Print Codes',
        'twofa.continueToSettings': 'Continue to Settings',
        'twofa.howToUse': 'How to use backup codes:',
        'twofa.useWhen': "Use a backup code when you can't access your authenticator app",
        'twofa.enterCode': 'Enter the code in the 2FA field when logging in',
        'twofa.oneTimeUse': 'Each code works only once - it will be deleted after use',
        'twofa.regenerate': 'You can regenerate codes anytime from Settings',
        
        // Admin
        'admin.title': 'Admin Panel',
        'admin.subtitle': 'Manage users and system settings',
        'admin.totalUsers': 'Total Users',
        'admin.adminUsers': 'Admin Users',
        'admin.twoFAEnabled': '2FA Enabled',
        'admin.users': 'Users',
        'admin.createUser': 'Create User',
        'admin.username': 'Username',
        'admin.email': 'Email',
        'admin.role': 'Role',
        'admin.twoFA': '2FA',
        'admin.language': 'Language',
        'admin.currency': 'Currency',
        'admin.joined': 'Joined',
        'admin.actions': 'Actions',
        'admin.admin': 'Admin',
        'admin.user': 'User',
        'admin.createNewUser': 'Create New User',
        'admin.makeAdmin': 'Make admin',
        'admin.create': 'Create',
        'admin.noUsers': 'No users found',
        'admin.errorLoading': 'Error loading users',
        'admin.userCreated': 'User created successfully',
        'admin.errorCreating': 'Error creating user',
        'admin.confirmDelete': 'Are you sure you want to delete user',
        'admin.userDeleted': 'User deleted successfully',
        'admin.errorDeleting': 'Error deleting user',
        'admin.editNotImplemented': 'Edit functionality coming soon',
        
        // Categories
        'categories.foodDining': 'Food & Dining',
        'categories.transportation': 'Transportation',
        'categories.shopping': 'Shopping',
        'categories.entertainment': 'Entertainment',
        'categories.billsUtilities': 'Bills & Utilities',
        'categories.healthcare': 'Healthcare',
        'categories.education': 'Education',
        'categories.other': 'Other',
        'categories.manageTitle': 'Manage Categories',
        'categories.addNew': 'Add New Category',
        'categories.add': 'Add',
        'categories.yourCategories': 'Your Categories',
        'categories.dragToReorder': 'Drag to reorder',
        'categories.created': 'Category created successfully',
        'categories.updated': 'Category updated successfully',
        'categories.deleted': 'Category deleted successfully',
        'categories.hasExpenses': 'Cannot delete category with expenses',
        'categories.reordered': 'Categories reordered successfully',
        
        // Dashboard
        'dashboard.expenseCategories': 'Expense Categories',
        'dashboard.manageCategories': 'Manage',
        
        // Date formatting
        'date.today': 'Today',
        'date.yesterday': 'Yesterday',
        'date.daysAgo': 'days ago',
        
        // Form
        'form.name': 'Name',
        'form.color': 'Color',
        'form.icon': 'Icon',
        
        // Common
        'common.cancel': 'Cancel',
        'common.edit': 'Edit',
        'common.delete': 'Delete',
        'common.error': 'An error occurred. Please try again.',
        'common.success': 'Operation completed successfully!',
        'common.missingFields': 'Missing required fields',
        'common.invalidCategory': 'Invalid category',
        
        // Actions
        'actions.cancel': 'Cancel'
    },
    ro: {
        // Navigation
        'nav.dashboard': 'Tablou de bord',
        'nav.transactions': 'Tranzacții',
        'nav.reports': 'Rapoarte',
        'nav.admin': 'Admin',
        'nav.settings': 'Setări',
        'nav.logout': 'Deconectare',
        
        // Dashboard
        'dashboard.total_spent': 'Total Cheltuit Luna Aceasta',
        'dashboard.active_categories': 'Categorii Active',
        'dashboard.total_transactions': 'Total Tranzacții',
        'dashboard.vs_last_month': 'față de luna trecută',
        'dashboard.categories_in_use': 'categorii în uz',
        'dashboard.this_month': 'luna curentă',
        'dashboard.spending_by_category': 'Cheltuieli pe Categorii',
        'dashboard.monthly_trend': 'Tendință Lunară',
        'dashboard.recent_transactions': 'Tranzacții Recente',
        'dashboard.view_all': 'Vezi Toate',
        'dashboard.search': 'Caută cheltuieli...',
        'dashboard.selectCategory': 'Selectează categoria...',
        'dashboard.noTransactions': 'Nicio tranzacție încă',
        'dashboard.noData': 'Nu există date disponibile',
        'dashboard.total': 'Total',
        'dashboard.totalThisYear': 'Total Anul Acesta',
        'dashboard.spending': 'Cheltuieli',
        'dashboard.categoryBreakdownDesc': 'Defalcare pe categorii',
        'dashboard.lightMode': 'Mod Luminos',
        'dashboard.darkMode': 'Mod Întunecat',
        'dashboard.expenseAdded': 'Cheltuială adăugată cu succes!',
        
        // Login
        'login.title': 'Bine ai revenit',
        'login.tagline': 'Urmărește-ți cheltuielile, gestionează-ți finanțele',
        'login.remember_me': 'Ține-mă minte',
        'login.sign_in': 'Conectare',
        'login.no_account': 'Nu ai un cont?',
        'login.register': 'Înregistrare',
        
        // Register
        'register.title': 'Creare Cont',
        'register.tagline': 'Începe să îți gestionezi finanțele astăzi',
        'register.create_account': 'Creează Cont',
        'register.have_account': 'Ai deja un cont?',
        'register.login': 'Conectare',
        
        // Forms
        'form.email': 'Email',
        'form.password': 'Parolă',
        'form.username': 'Nume utilizator',
        'form.language': 'Limbă',
        'form.currency': 'Monedă',
        'form.monthlyBudget': 'Buget Lunar',
        'form.amount': 'Sumă',
        'form.description': 'Descriere',
        'form.category': 'Categorie',
        'form.date': 'Dată',
        'form.tags': 'Etichete (separate prin virgulă)',
        'form.receipt': 'Chitanță (opțional)',
        'form.2fa_code': 'Cod 2FA',
        'form.chooseFile': 'Alege Fișier',
        'form.noFileChosen': 'Niciun fișier ales',
        
        // Transactions
        'transactions.title': 'Tranzacții',
        'transactions.export': 'Exportă CSV',
        'transactions.import': 'Importă CSV',
        'transactions.addExpense': 'Adaugă Cheltuială',
        'transactions.search': 'Caută tranzacții...',
        'transactions.date': 'Dată',
        'transactions.filters': 'Filtre',
        'transactions.category': 'Categorie',
        'transactions.allCategories': 'Categorie',
        'transactions.startDate': 'Data Început',
        'transactions.endDate': 'Data Sfârșit',
        'transactions.tableTransaction': 'Tranzacție',
        'transactions.tableCategory': 'Categorie',
        'transactions.tableDate': 'Dată',
        'transactions.tablePayment': 'Plată',
        'transactions.tableAmount': 'Sumă',
        'transactions.tableStatus': 'Stare',
        'transactions.tableActions': 'Acțiuni',
        'transactions.showing': 'Afișare',
        'transactions.to': 'până la',
        'transactions.of': 'din',
        'transactions.results': 'rezultate',
        'transactions.previous': 'Anterior',
        'transactions.next': 'Următorul',
        'transactions.noTransactions': 'Nu s-au găsit tranzacții',
        'transactions.expense': 'Cheltuială',
        'transactions.completed': 'Finalizat',
        'transactions.pending': 'În așteptare',
        'transactions.edit': 'Editează',
        'transactions.delete': 'Șterge',
        'transactions.updated': 'Tranzacție actualizată cu succes!',
        'transactions.notFound': 'Tranzacție negăsită',
        'modal.edit_expense': 'Editează Cheltuială',
        'actions.update': 'Actualizează Cheltuială',
        'form.currentReceipt': 'Chitanță curentă atașată',
        'form.receiptHelp': 'Încarcă un fișier nou pentru a înlocui chitanța existentă',
        'transactions.viewReceipt': 'Vezi Chitanța',
        'transactions.downloadReceipt': 'Descarcă Chitanța',
        'transactions.transaction': 'tranzacție',
        'transactions.transactions': 'tranzacții',
        'transactions.deleteConfirm': 'Ești sigur că vrei să ștergi această tranzacție?',
        'transactions.deleted': 'Tranzacție ștearsă',
        'transactions.imported': 'Importate',
        'transactions.importSuccess': 'tranzacții',
        
        // Actions
        'actions.add_expense': 'Adaugă Cheltuială',
        'actions.save': 'Salvează Cheltuiala',
        
        // Modal
        'modal.add_expense': 'Adaugă Cheltuială',
        
        // Reports
        'reports.title': 'Rapoarte Financiare',
        'reports.export': 'Exportă CSV',
        'reports.analysisPeriod': 'Perioadă de Analiză:',
        'reports.last30Days': 'Ultimele 30 Zile',
        'reports.quarter': 'Trimestru',
        'reports.ytd': 'An Curent',
        'reports.allCategories': 'Toate Categoriile',
        'reports.generate': 'Generează Raport',
        'reports.totalSpent': 'Total Cheltuit',
        'reports.topCategory': 'Categorie Principală',
        'reports.avgDaily': 'Medie Zilnică',
        'reports.savingsRate': 'Rată Economii',
        'reports.vsLastMonth': 'față de perioada anterioară',
        'reports.spentThisPeriod': 'cheltuit în această perioadă',
        'reports.placeholder': 'Substituent',
        'reports.spendingTrend': 'Tendință Cheltuieli',
        'reports.categoryBreakdown': 'Defalcare pe Categorii',
        'reports.monthlySpending': 'Cheltuieli Lunare',
        'reports.smartRecommendations': 'Recomandări Inteligente',
        'reports.noRecommendations': 'Nicio recomandare momentan',
        
        // User
        'user.admin': 'Administrator',
        'user.user': 'Utilizator',
        
        // Documents
        'nav.documents': 'Documente',
        'documents.title': 'Documente',
        'documents.uploadTitle': 'Încarcă Documente',
        'documents.dragDrop': 'Trage și plasează fișiere aici sau click pentru a căuta',
        'documents.uploadDesc': 'Încarcă extrase de cont, facturi sau chitanțe.',
        'documents.supportedFormats': 'Formate suportate: CSV, PDF, XLS, XLSX, PNG, JPG (Max 10MB)',
        'documents.yourFiles': 'Fișierele Tale',
        'documents.searchPlaceholder': 'Caută după nume...',
        'documents.tableDocName': 'Nume Document',
        'documents.tableUploadDate': 'Data Încărcării',
        'documents.tableType': 'Tip',
        'documents.tableStatus': 'Stare',
        'documents.tableActions': 'Acțiuni',
        'documents.statusUploaded': 'Încărcat',
        'documents.statusProcessing': 'În procesare',
        'documents.statusAnalyzed': 'Analizat',
        'documents.statusError': 'Eroare',
        'documents.showing': 'Afișare',
        'documents.of': 'din',
        'documents.documents': 'documente',
        'documents.noDocuments': 'Nu s-au găsit documente. Încarcă primul tău document!',
        'documents.errorLoading': 'Eroare la încărcarea documentelor. Te rugăm încearcă din nou.',
        
        // Settings
        'settings.title': 'Setări',
        'settings.avatar': 'Avatar Profil',
        'settings.uploadAvatar': 'Încarcă Personalizat',
        'settings.avatarDesc': 'PNG, JPG, GIF, WEBP. Max 20MB',
        'settings.defaultAvatars': 'Sau alege un avatar prestabilit:',
        'settings.profile': 'Informații Profil',
        'settings.saveProfile': 'Salvează Profil',
        'settings.changePassword': 'Schimbă Parola',
        'settings.currentPassword': 'Parola Curentă',
        'settings.newPassword': 'Parolă Nouă',
        'settings.confirmPassword': 'Confirmă Parola Nouă',
        'settings.updatePassword': 'Actualizează Parola',
        'settings.twoFactor': 'Autentificare Doi Factori',
        'settings.twoFactorEnabled': '2FA este activată pentru contul tău',
        'settings.twoFactorDisabled': 'Adaugă un nivel suplimentar de securitate contului tău',
        'settings.enabled': 'Activat',
        'settings.disabled': 'Dezactivat',
        'settings.regenerateCodes': 'Regenerează Coduri Backup',
        'settings.enable2FA': 'Activează 2FA',
        'settings.disable2FA': 'Dezactivează 2FA',
        
        // Two-Factor Authentication
        'twofa.setupTitle': 'Configurare Autentificare Doi Factori',
        'twofa.setupDesc': 'Scanează codul QR cu aplicația ta de autentificare',
        'twofa.step1': 'Pasul 1: Scanează Codul QR',
        'twofa.step1Desc': 'Deschide aplicația ta de autentificare (Google Authenticator, Authy, etc.) și scanează acest cod QR:',
        'twofa.manualEntry': 'Nu poți scana? Introdu codul manual',
        'twofa.enterManually': 'Introdu acest cod în aplicația ta de autentificare:',
        'twofa.step2': 'Pasul 2: Verifică Codul',
        'twofa.step2Desc': 'Introdu codul de 6 cifre din aplicația ta de autentificare:',
        'twofa.enable': 'Activează 2FA',
        'twofa.infoText': 'După activarea 2FA, vei primi coduri de backup pe care le poți folosi dacă pierzi accesul la aplicația ta de autentificare. Păstrează-le într-un loc sigur!',
        'twofa.setupSuccess': 'Autentificare Doi Factori Activată!',
        'twofa.backupCodesDesc': 'Salvează aceste coduri de backup într-o locație sigură',
        'twofa.important': 'Important!',
        'twofa.backupCodesWarning': 'Fiecare cod de backup poate fi folosit o singură dată. Păstrează-le în siguranță - vei avea nevoie de ele dacă pierzi accesul la aplicația ta de autentificare.',
        'twofa.yourBackupCodes': 'Codurile Tale de Backup',
        'twofa.downloadPDF': 'Descarcă ca PDF',
        'twofa.print': 'Tipărește Coduri',
        'twofa.continueToSettings': 'Continuă la Setări',
        'twofa.howToUse': 'Cum să folosești codurile de backup:',
        'twofa.useWhen': 'Folosește un cod de backup când nu poți accesa aplicația ta de autentificare',
        'twofa.enterCode': 'Introdu codul în câmpul 2FA când te autentifici',
        'twofa.oneTimeUse': 'Fiecare cod funcționează o singură dată - va fi șters după folosire',
        'twofa.regenerate': 'Poți regenera coduri oricând din Setări',
        
        // Admin
        'admin.title': 'Panou Administrare',
        'admin.subtitle': 'Gestionează utilizatori și setări sistem',
        'admin.totalUsers': 'Total Utilizatori',
        'admin.adminUsers': 'Administratori',
        'admin.twoFAEnabled': '2FA Activat',
        'admin.users': 'Utilizatori',
        'admin.createUser': 'Creează Utilizator',
        'admin.username': 'Nume Utilizator',
        'admin.email': 'Email',
        'admin.role': 'Rol',
        'admin.twoFA': '2FA',
        'admin.language': 'Limbă',
        'admin.currency': 'Monedă',
        'admin.joined': 'Înregistrat',
        'admin.actions': 'Acțiuni',
        'admin.admin': 'Admin',
        'admin.user': 'Utilizator',
        'admin.createNewUser': 'Creează Utilizator Nou',
        'admin.makeAdmin': 'Fă administrator',
        'admin.create': 'Creează',
        'admin.noUsers': 'Niciun utilizator găsit',
        'admin.errorLoading': 'Eroare la încărcarea utilizatorilor',
        'admin.userCreated': 'Utilizator creat cu succes',
        'admin.errorCreating': 'Eroare la crearea utilizatorului',
        'admin.confirmDelete': 'Sigur vrei să ștergi utilizatorul',
        'admin.userDeleted': 'Utilizator șters cu succes',
        'admin.errorDeleting': 'Eroare la ștergerea utilizatorului',
        'admin.editNotImplemented': 'Funcționalitatea de editare va fi disponibilă în curând',
        
        // Common
        'common.cancel': 'Anulează',
        'common.edit': 'Editează',
        'common.delete': 'Șterge',
                // Categorii
        'categories.foodDining': 'Mâncare & Restaurant',
        'categories.transportation': 'Transport',
        'categories.shopping': 'Cumpărături',
        'categories.entertainment': 'Divertisment',
        'categories.billsUtilities': 'Facturi & Utilități',
        'categories.healthcare': 'Sănătate',
        'categories.education': 'Educație',
        'categories.other': 'Altele',
        'categories.manageTitle': 'Gestionează Categorii',
        'categories.addNew': 'Adaugă Categorie Nouă',
        'categories.add': 'Adaugă',
        'categories.yourCategories': 'Categoriile Tale',
        'categories.dragToReorder': 'Trage pentru a reordona',
        'categories.created': 'Categorie creată cu succes',
        'categories.updated': 'Categorie actualizată cu succes',
        'categories.deleted': 'Categorie ștearsă cu succes',
        'categories.hasExpenses': 'Nu se poate șterge categoria cu cheltuieli',
        'categories.reordered': 'Categorii reordonate cu succes',
        
        // Tablou de bord
        'dashboard.expenseCategories': 'Categorii de Cheltuieli',
        'dashboard.manageCategories': 'Gestionează',
        
        // Formatare dată
        'date.today': 'Astăzi',
        'date.yesterday': 'Ieri',
        'date.daysAgo': 'zile în urmă',
        
        // Formular
        'form.name': 'Nume',
        'form.color': 'Culoare',
        'form.icon': 'Iconă',
        
        // Comune
        'common.cancel': 'Anulează',
        'common.edit': 'Editează',
        'common.delete': 'Șterge',
        'common.error': 'A apărut o eroare. Te rugăm încearcă din nou.',
        'common.success': 'Operațiune finalizată cu succes!',
        'common.missingFields': 'Câmpuri obligatorii lipsă',
        'common.invalidCategory': 'Categorie invalidă',
                // Actions
        'actions.cancel': 'Anulează'
    }
};

// Get current language from localStorage or default to 'en'
function getCurrentLanguage() {
    return localStorage.getItem('language') || 'en';
}

// Set language
function setLanguage(lang) {
    if (translations[lang]) {
        localStorage.setItem('language', lang);
        translatePage(lang);
    }
}

// Translate all elements on page
function translatePage(lang) {
    const elements = document.querySelectorAll('[data-translate]');
    
    elements.forEach(element => {
        const key = element.getAttribute('data-translate');
        const translation = translations[lang][key];
        
        if (translation) {
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        }
    });
}

// Initialize translations on page load
document.addEventListener('DOMContentLoaded', () => {
    const currentLang = getCurrentLanguage();
    translatePage(currentLang);
});

// Helper function to get translated text
function getTranslation(key, fallback = '') {
    const lang = getCurrentLanguage();
    return translations[lang]?.[key] || fallback || key;
}

// Make functions and translations globally accessible for other scripts
window.getCurrentLanguage = getCurrentLanguage;
window.setLanguage = setLanguage;
window.translatePage = translatePage;
window.translations = translations;
window.getTranslation = getTranslation;

// Export functions for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { getCurrentLanguage, setLanguage, translatePage, translations };
}
