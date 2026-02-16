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
    fetch('/set_volume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ change: change })
    })
        .then(response => response.json())
        .then(data => {
            // Volume adjustment is silent - no toast
            console.log('Volume adjusted:', change);
        })
        .catch(error => {
            console.error('Volume error:', error);
        });
}
