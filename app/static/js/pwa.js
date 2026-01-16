// PWA Service Worker Registration

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('ServiceWorker registered:', registration);
                // Check for updates
                registration.update();
            })
            .catch(error => {
                console.log('ServiceWorker registration failed:', error);
            });
    });
}

// Install prompt
let deferredPrompt;
let installBannerDismissed = localStorage.getItem('pwa-install-dismissed');

// Create and show install banner
function createInstallBanner() {
    // Don't show if already dismissed recently (24 hours)
    const dismissedTime = localStorage.getItem('pwa-install-dismissed-time');
    if (dismissedTime && (Date.now() - parseInt(dismissedTime)) < 24 * 60 * 60 * 1000) {
        return null;
    }
    
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
        return null;
    }

    const banner = document.createElement('div');
    banner.id = 'pwa-install-banner';
    banner.className = 'fixed bottom-20 left-4 right-4 md:left-auto md:right-4 md:w-96 bg-gradient-to-r from-primary to-blue-600 text-white rounded-2xl shadow-2xl p-4 z-50 animate-slide-up';
    banner.innerHTML = `
        <div class="flex items-start gap-3">
            <img src="/static/icons/icon-96x96.png" alt="FINA" class="w-12 h-12 rounded-xl shadow-lg">
            <div class="flex-1 min-w-0">
                <h3 class="font-bold text-lg">Install FINA</h3>
                <p class="text-sm text-blue-100 mt-0.5">Add to home screen for a better experience</p>
            </div>
            <button id="pwa-dismiss-btn" class="text-white/70 hover:text-white p-1 -mt-1 -mr-1">
                <span class="material-symbols-outlined text-xl">close</span>
            </button>
        </div>
        <div class="flex gap-2 mt-3">
            <button id="pwa-install-btn" class="flex-1 bg-white text-primary font-semibold py-2.5 px-4 rounded-xl hover:bg-blue-50 transition-colors flex items-center justify-center gap-2">
                <span class="material-symbols-outlined text-xl">download</span>
                Install App
            </button>
            <button id="pwa-later-btn" class="px-4 py-2.5 text-white/90 hover:text-white font-medium transition-colors">
                Later
            </button>
        </div>
    `;
    
    // Add animation styles if not present
    if (!document.getElementById('pwa-styles')) {
        const style = document.createElement('style');
        style.id = 'pwa-styles';
        style.textContent = `
            @keyframes slide-up {
                from { transform: translateY(100%); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            .animate-slide-up { animation: slide-up 0.3s ease-out; }
        `;
        document.head.appendChild(style);
    }
    
    return banner;
}

function showInstallBanner() {
    if (document.getElementById('pwa-install-banner')) return;
    
    const banner = createInstallBanner();
    if (!banner) return;
    
    document.body.appendChild(banner);
    
    // Install button click
    document.getElementById('pwa-install-btn').addEventListener('click', async () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            console.log('User response:', outcome);
            deferredPrompt = null;
        }
        banner.remove();
    });
    
    // Dismiss button click
    document.getElementById('pwa-dismiss-btn').addEventListener('click', () => {
        localStorage.setItem('pwa-install-dismissed-time', Date.now().toString());
        banner.remove();
    });
    
    // Later button click
    document.getElementById('pwa-later-btn').addEventListener('click', () => {
        localStorage.setItem('pwa-install-dismissed-time', Date.now().toString());
        banner.remove();
    });
}

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    console.log('PWA install available');
    
    // Show install banner after a short delay
    setTimeout(() => {
        showInstallBanner();
    }, 2000);
    
    // Also handle existing install button if present
    const installBtn = document.getElementById('install-btn');
    if (installBtn) {
        installBtn.style.display = 'block';
        installBtn.addEventListener('click', async () => {
            installBtn.style.display = 'none';
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                console.log('User response:', outcome);
                deferredPrompt = null;
            }
        });
    }
});

// Check if app is installed
window.addEventListener('appinstalled', () => {
    console.log('FINA has been installed');
    const banner = document.getElementById('pwa-install-banner');
    if (banner) banner.remove();
    if (typeof showToast === 'function') {
        showToast('FINA installed successfully!', 'success');
    }
});

// Online/Offline status
window.addEventListener('online', () => {
    if (typeof showToast === 'function') {
        showToast('You are back online', 'success');
    }
});

window.addEventListener('offline', () => {
    if (typeof showToast === 'function') {
        showToast('You are offline. Some features may be limited.', 'warning');
    }
});

// Expose function to manually trigger install
window.installPWA = async function() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        deferredPrompt = null;
        return outcome === 'accepted';
    }
    return false;
};

// Check if running as PWA
window.isPWA = function() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
};
