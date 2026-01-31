// Universal Version Loader
// Fetches app version once and stores globally, updates all version-info elements
// Include this script in <head> of all templates

(function() {
    // Fetch version and store in global window object
    fetch('/api/version')
        .then(r => r.json())
        .then(data => {
            // Store globally for all other scripts to use
            window.appVersion = data;
            
            // Update all version-info elements on the page
            const versionElements = document.querySelectorAll('#version-info, .version-info');
            const versionText = `${data.app_name} v${data.version} (${data.build_date})`;
            versionElements.forEach(el => {
                el.textContent = versionText;
            });
            
            console.log('[VERSION-LOADER] App version loaded:', versionText);
        })
        .catch(err => {
            console.error('[VERSION-LOADER] Failed to load version:', err);
            // Fallback
            window.appVersion = {
                app_name: 'MPD Web Control',
                version: 'unknown',
                build_date: 'unknown',
                status: 'error'
            };
            // Update elements with fallback
            const versionElements = document.querySelectorAll('#version-info, .version-info');
            versionElements.forEach(el => {
                el.textContent = 'MPD Web Control';
            });
        });
})();
