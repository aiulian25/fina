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
        'dashboard.total_spent': 'Total Spent',
        'dashboard.active_categories': 'Active Categories',
        'dashboard.total_transactions': 'Total Transactions',
        'dashboard.vs_last_month': 'vs last month',
        'dashboard.categories_in_use': 'categories in use',
        'dashboard.this_month': 'this month',
        'dashboard.spending_by_category': 'Spending by Category',
        'dashboard.monthly_trend': 'Monthly Trend',
        'dashboard.recent_transactions': 'Recent Transactions',
        'dashboard.view_all': 'View All',
        
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
        'form.amount': 'Amount',
        'form.description': 'Description',
        'form.category': 'Category',
        'form.date': 'Date',
        'form.tags': 'Tags (comma separated)',
        'form.receipt': 'Receipt (optional)',
        'form.2fa_code': '2FA Code',
        
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
        'dashboard.total_spent': 'Total Cheltuit',
        'dashboard.active_categories': 'Categorii Active',
        'dashboard.total_transactions': 'Total Tranzacții',
        'dashboard.vs_last_month': 'față de luna trecută',
        'dashboard.categories_in_use': 'categorii în uz',
        'dashboard.this_month': 'luna aceasta',
        'dashboard.spending_by_category': 'Cheltuieli pe Categorii',
        'dashboard.monthly_trend': 'Tendință Lunară',
        'dashboard.recent_transactions': 'Tranzacții Recente',
        'dashboard.view_all': 'Vezi Toate',
        
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
        'form.amount': 'Sumă',
        'form.description': 'Descriere',
        'form.category': 'Categorie',
        'form.date': 'Dată',
        'form.tags': 'Etichete (separate prin virgulă)',
        'form.receipt': 'Chitanță (opțional)',
        'form.2fa_code': 'Cod 2FA',
        
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

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { getCurrentLanguage, setLanguage, translatePage, translations };
}
