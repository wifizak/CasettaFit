// CasettaFit PWA Registration and Management
(function() {
  'use strict';

  // ============================================
  // Service Worker Registration
  // ============================================
  
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then(registration => {
          console.log('[PWA] Service Worker registered:', registration.scope);
          
          // Check for updates periodically (every 60 seconds)
          setInterval(() => {
            registration.update();
          }, 60000);
        })
        .catch(error => {
          console.error('[PWA] Service Worker registration failed:', error);
        });
    });

    // Listen for service worker updates
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      console.log('[PWA] Service Worker updated');
      // Optionally reload the page to use new service worker
      // window.location.reload();
    });
  } else {
    console.log('[PWA] Service Workers not supported in this browser');
  }

  // ============================================
  // PWA Install Prompt Handling
  // ============================================
  
  let deferredPrompt = null;
  let installButton = null;

  window.addEventListener('beforeinstallprompt', (e) => {
    console.log('[PWA] Install prompt available');
    
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    
    // Show custom install button if it exists
    installButton = document.getElementById('pwa-install-button');
    if (installButton) {
      installButton.style.display = 'block';
      
      // Handle install button click
      installButton.addEventListener('click', async () => {
        if (!deferredPrompt) return;
        
        // Show the install prompt
        deferredPrompt.prompt();
        
        // Wait for the user's response
        const { outcome } = await deferredPrompt.userChoice;
        console.log(`[PWA] User response to install prompt: ${outcome}`);
        
        // Clear the deferred prompt
        deferredPrompt = null;
        installButton.style.display = 'none';
      });
    }
  });

  // Detect when PWA is installed
  window.addEventListener('appinstalled', () => {
    console.log('[PWA] App was installed');
    
    if (installButton) {
      installButton.style.display = 'none';
    }
    
    deferredPrompt = null;
  });

  // Detect if already running as PWA
  if (window.matchMedia('(display-mode: standalone)').matches) {
    console.log('[PWA] Running as installed PWA');
    document.body.classList.add('pwa-mode');
  }

  // ============================================
  // Online/Offline Status Handling
  // ============================================
  
  let offlineIndicator = null;

  function showOfflineIndicator() {
    offlineIndicator = document.getElementById('offline-indicator');
    if (!offlineIndicator) {
      // Create offline indicator if it doesn't exist
      offlineIndicator = document.createElement('div');
      offlineIndicator.id = 'offline-indicator';
      offlineIndicator.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: #ffc107;
        color: #000;
        padding: 10px 20px;
        border-radius: 5px;
        z-index: 9999;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        display: none;
      `;
      offlineIndicator.innerHTML = '⚠️ You are offline';
      document.body.appendChild(offlineIndicator);
    }
  }

  window.addEventListener('online', () => {
    console.log('[PWA] Back online');
    
    if (offlineIndicator) {
      offlineIndicator.style.display = 'none';
    }
    
    // Optionally show a brief "Back online" message
    // or trigger data sync
  });

  window.addEventListener('offline', () => {
    console.log('[PWA] Gone offline');
    
    showOfflineIndicator();
    if (offlineIndicator) {
      offlineIndicator.style.display = 'block';
    }
  });

  // Check initial online/offline status
  if (!navigator.onLine) {
    showOfflineIndicator();
    if (offlineIndicator) {
      offlineIndicator.style.display = 'block';
    }
  }

  // ============================================
  // Helper: Check if PWA is installable
  // ============================================
  
  window.isPWAInstallable = function() {
    return deferredPrompt !== null;
  };

  // ============================================
  // Helper: Check if running as PWA
  // ============================================
  
  window.isRunningAsPWA = function() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true; // iOS
  };

})();
