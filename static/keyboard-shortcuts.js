/**
 * Keyboard Shortcuts for Maestro MPD Control
 * 
 * Shortcuts:
 * - Spacebar: Toggle play/pause
 * - Right Arrow: Next track
 * - Left Arrow: Previous track
 * - Up Arrow: Volume +2%
 * - Down Arrow: Volume -2%
 * 
 * Disabled on Settings page
 * Skipped when typing in input/textarea fields
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
});

function initializeKeyboardShortcuts() {
    // Check if we're on the settings page - disable shortcuts there
    const isSettingsPage = window.location.pathname.includes('/settings');
    
    if (isSettingsPage) {
        console.log('[Keyboard Shortcuts] Disabled on Settings page');
        return;
    }

    document.addEventListener('keydown', function(event) {
        // Don't trigger shortcuts if user is typing in an input or textarea
        const activeElement = document.activeElement;
        const isTyping = activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA';
        
        if (isTyping) {
            return;
        }

        // Spacebar: Toggle play/pause
        if (event.code === 'Space') {
            event.preventDefault();
            togglePlayPause();
            return;
        }

        // Right Arrow: Next track
        if (event.key === 'ArrowRight') {
            event.preventDefault();
            handleNextTrack();
            return;
        }

        // Left Arrow: Previous track
        if (event.key === 'ArrowLeft') {
            event.preventDefault();
            handlePreviousTrack();
            return;
        }

        // Up Arrow: Volume +2%
        if (event.key === 'ArrowUp') {
            event.preventDefault();
            handleVolumeIncrease();
            return;
        }

        // Down Arrow: Volume -2%
        if (event.key === 'ArrowDown') {
            event.preventDefault();
            handleVolumeDecrease();
            return;
        }
    });
}

/**
 * Toggle play/pause - plays if stopped, pauses if playing
 */
function togglePlayPause() {
    // Get current MPD status to determine if we should play or pause
    fetch('/get_mpd_status')
        .then(response => response.json())
        .then(data => {
            if (data.state === 'play') {
                // Currently playing - pause
                pauseMusic();
            } else {
                // Stopped or paused - play
                playMusic();
            }
        })
        .catch(error => {
            console.error('Error checking MPD status:', error);
            // Fallback: try to play
            playMusic();
        });
}

/**
 * Next track handler
 */
function handleNextTrack() {
    nextTrack();
    showKeyboardToast('⏭️ Next track');
}

/**
 * Previous track handler
 */
function handlePreviousTrack() {
    previousTrack();
    showKeyboardToast('⏮️ Previous track');
}

/**
 * Volume increase handler - respects hidden volume setting
 */
function handleVolumeIncrease() {
    // Check if volume controls are hidden
    const volumeSection = document.querySelector('.volume-controls-simple');
    if (volumeSection && volumeSection.style.display === 'none') {
        // Volume controls are hidden, don't allow volume adjustment
        showKeyboardToast('⚠️ Volume controls hidden', 'warning', 1500);
        return;
    }

    adjustVolume(2);
    showKeyboardToast('🔊 Volume +2%');
}

/**
 * Volume decrease handler - respects hidden volume setting
 */
function handleVolumeDecrease() {
    // Check if volume controls are hidden
    const volumeSection = document.querySelector('.volume-controls-simple');
    if (volumeSection && volumeSection.style.display === 'none') {
        // Volume controls are hidden, don't allow volume adjustment
        showKeyboardToast('⚠️ Volume controls hidden', 'warning', 1500);
        return;
    }

    adjustVolume(-2);
    showKeyboardToast('🔉 Volume -2%');
}

/**
 * Show a toast notification for keyboard shortcuts
 * @param {string} message - The message to display
 * @param {string} type - Type of toast (success, info, warning, error)
 * @param {number} duration - How long to show (ms)
 */
function showKeyboardToast(message, type = 'info', duration = 1500) {
    // Try to use existing showMessage function if available
    if (typeof showMessage === 'function') {
        showMessage(message, type);
        return;
    }

    // Fallback: create a simple toast if showMessage isn't available
    const container = document.getElementById('toast-container');
    if (container) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${message}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('removing');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    } else {
        // Last resort: log to console
        console.log(`[Keyboard Shortcut] ${message}`);
    }
}
