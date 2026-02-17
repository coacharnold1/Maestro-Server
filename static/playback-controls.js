/**
 * Global Playback Control Functions
 * These functions are available on all pages
 */

function playMusic() {
    fetch('/play?ajax=1', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (typeof displayMessage === 'function') {
                displayMessage('info', '▶️ Play/Pause toggled');
            } else if (typeof showToast === 'function') {
                showToast('▶️ Play/Pause toggled', 'success', 2000);
            }
        })
        .catch(error => {
            console.error('Play error:', error);
        });
}

function pauseMusic() {
    fetch('/pause?ajax=1', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (typeof displayMessage === 'function') {
                displayMessage('info', '⏸️ Play/Pause toggled');
            } else if (typeof showToast === 'function') {
                showToast('⏸️ Play/Pause toggled', 'info', 2000);
            }
        })
        .catch(error => {
            console.error('Pause error:', error);
        });
}

function nextTrack() {
    fetch('/next?ajax=1', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (typeof displayMessage === 'function') {
                displayMessage('info', '⏭️ Next track');
            } else if (typeof showToast === 'function') {
                showToast('⏭️ Next track', 'success', 2000);
            }
        })
        .catch(error => {
            console.error('Next track error:', error);
        });
}

function previousTrack() {
    fetch('/previous?ajax=1', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (typeof displayMessage === 'function') {
                displayMessage('info', '⏮️ Previous track');
            } else if (typeof showToast === 'function') {
                showToast('⏮️ Previous track', 'success', 2000);
            }
        })
        .catch(error => {
            console.error('Previous track error:', error);
        });
}

function adjustVolume(change) {
    // Get current volume from the display
    const volumeDisplay = document.getElementById('volume-percentage-display');
    if (!volumeDisplay) {
        console.warn('Volume display element not found');
        return;
    }
    
    let currentVolume = parseInt(volumeDisplay.textContent) || 0;
    let newVolume = currentVolume + change;
    
    // Clamp between 0 and 100
    newVolume = Math.max(0, Math.min(100, newVolume));
    
    // Send as form data (not JSON) to match backend expectations
    const formData = new FormData();
    formData.append('volume', newVolume);
    
    fetch('/set_volume', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            // Volume adjustment is silent - no toast
            console.log('Volume adjusted to:', newVolume);
        })
        .catch(error => {
            console.error('Volume error:', error);
        });
}
