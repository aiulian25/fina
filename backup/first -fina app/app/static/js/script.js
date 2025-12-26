// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/service-worker.js')
            .then(registration => {
                console.log('[PWA] Service Worker registered successfully:', registration.scope);
                
                // Check for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            console.log('[PWA] New version available! Refresh to update.');
                            // Optionally show a notification to the user
                            if (confirm('A new version of FINA is available. Reload to update?')) {
                                newWorker.postMessage({ type: 'SKIP_WAITING' });
                                window.location.reload();
                            }
                        }
                    });
                });
            })
            .catch(error => {
                console.log('[PWA] Service Worker registration failed:', error);
            });
    });
}

// PWA Install Prompt
let deferredPrompt;
const installPrompt = document.getElementById('pwa-install-prompt');
const installBtn = document.getElementById('pwa-install-btn');
const dismissBtn = document.getElementById('pwa-dismiss-btn');

// Check if already installed (standalone mode)
const isInstalled = () => {
    return window.matchMedia('(display-mode: standalone)').matches || 
           window.navigator.standalone === true || 
           document.referrer.includes('android-app://');
};

// Detect iOS
const isIOS = () => {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
};

// Show iOS install instructions
function showIOSInstallPrompt() {
    if (installPrompt) {
        const promptText = installPrompt.querySelector('.pwa-prompt-text p');
        if (promptText && isIOS() && !window.navigator.standalone) {
            promptText.textContent = 'Tap Share button and then "Add to Home Screen"';
            installBtn.style.display = 'none'; // Hide install button on iOS
        }
    }
}

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the default mini-infobar
    e.preventDefault();
    // Store the event for later use
    deferredPrompt = e;
    
    // Don't show if already installed
    if (isInstalled()) {
        return;
    }
    
    // Show custom install prompt if not dismissed
    const dismissed = localStorage.getItem('pwa-install-dismissed');
    const dismissedUntil = parseInt(dismissed || '0');
    
    if (Date.now() > dismissedUntil && installPrompt) {
        installPrompt.style.display = 'block';
    }
});

// Handle iOS separately
if (isIOS() && !isInstalled()) {
    const dismissed = localStorage.getItem('pwa-install-dismissed');
    const dismissedUntil = parseInt(dismissed || '0');
    
    if (Date.now() > dismissedUntil && installPrompt) {
        setTimeout(() => {
            installPrompt.style.display = 'block';
            showIOSInstallPrompt();
        }, 2000); // Show after 2 seconds
    }
}

if (installBtn) {
    installBtn.addEventListener('click', async () => {
        if (!deferredPrompt) {
            return;
        }
        
        // Show the install prompt
        deferredPrompt.prompt();
        
        // Wait for the user's response
        const { outcome } = await deferredPrompt.userChoice;
        console.log(`[PWA] User response: ${outcome}`);
        
        // Clear the saved prompt since it can't be used again
        deferredPrompt = null;
        
        // Hide the prompt
        installPrompt.style.display = 'none';
    });
}

if (dismissBtn) {
    dismissBtn.addEventListener('click', () => {
        installPrompt.style.display = 'none';
        // Remember dismissal for 7 days
        localStorage.setItem('pwa-install-dismissed', Date.now() + (7 * 24 * 60 * 60 * 1000));
    });
}

// Check if app is installed
window.addEventListener('appinstalled', () => {
    console.log('[PWA] App installed successfully');
    if (installPrompt) {
        installPrompt.style.display = 'none';
    }
    localStorage.removeItem('pwa-install-dismissed');
});

// Online/Offline status
window.addEventListener('online', () => {
    console.log('[PWA] Back online');
    // Show notification or update UI
    showToast('Connection restored', 'success');
});

window.addEventListener('offline', () => {
    console.log('[PWA] Gone offline');
    showToast('You are offline. Some features may be limited.', 'info');
});

// Toast notification function
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} glass-card`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Language menu toggle
function toggleLanguageMenu() {
    const menu = document.getElementById('language-menu');
    menu.classList.toggle('show');
}

// Close language menu when clicking outside
document.addEventListener('click', function(event) {
    const switcher = document.querySelector('.language-switcher');
    const menu = document.getElementById('language-menu');
    
    if (menu && switcher && !switcher.contains(event.target)) {
        menu.classList.remove('show');
    }
});

document.addEventListener('DOMContentLoaded', function() {
    console.log('Finance Tracker loaded');
    
    // Auto-hide flash messages after 2 seconds
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(function(alert) {
        // Add hiding animation after 2 seconds
        setTimeout(function() {
            alert.classList.add('hiding');
            
            // Remove from DOM after animation completes
            setTimeout(function() {
                alert.remove();
            }, 300); // Wait for animation to finish
        }, 2000); // Show for 2 seconds
    });
});
