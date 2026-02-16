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

// Global state variable - will be updated by Socket.IO mpd_status events
window.currentMPDState = null;

// Hook into existing Socket.IO mpd_status updates if available
if (typeof window.addEventListener !== 'undefined') {
    // Store reference to original socket if it exists
    const originalAddEventListener = window.addEventListener;
    let hookInstalled = false;
    
    // Try to hook into Socket.IO when it's available
    const checkForSocket = setInterval(() => {
        if (typeof io !== 'undefined' && !hookInstalled) {
            hookInstalled = true;
            clearInterval(checkForSocket);
        }
    }, 100);
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
    
    // Try to hook into Socket.IO updates for MPD state
    // Wait a moment for socket to be created
    setTimeout(() => {
        hookIntoSocketIO();
    }, 500);
});

function hookIntoSocketIO() {
    // Look for any Socket.IO socket instances in the global scope
    // This handles cases where socket might be global or in window
    const tryHookSocket = () => {
        // The socket is typically created as: const socket = io();
        // We need to find it and hook the mpd_status event
        
        // Try to access through window object
        for (let key in window) {
            if (window[key] && typeof window[key].on === 'function') {
                try {
                    // Try to register our mpd_status listener
                    const originalOn = window[key].on;
                    window[key].on = function(event, callback) {
                        if (event === 'mpd_status') {
                            // Wrap the callback to also update our global state
                            const wrappedCallback = function(data) {
                                window.currentMPDState = data;
                                callback(data);
                            };
                            return originalOn.call(this, event, wrappedCallback);
                        }
                        return originalOn.call(this, event, callback);
                    };
                } catch (e) {
                    // Ignore errors, just try the next one
                }
            }
        }
    };
    
    tryHookSocket();
}

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
    try {
        // Use global state if available, otherwise default to play
        if (window.currentMPDState && window.currentMPDState.state === 'play') {
            // Currently playing - pause
            if (typeof pauseMusic === 'function') {
                pauseMusic();
                showKeyboardToast('⏸️ Paused');
            } else {
                console.warn('[Keyboard Shortcuts] pauseMusic() function not available');
            }
        } else {
            // Stopped, paused, or state unknown - play
            if (typeof playMusic === 'function') {
                playMusic();
                showKeyboardToast('▶️ Playing');
            } else {
                console.warn('[Keyboard Shortcuts] playMusic() function not available');
            }
        }
    } catch (e) {
        console.error('[Keyboard Shortcuts] Error toggling play/pause:', e);
    }
}

/**
 * Next track handler
 */
function handleNextTrack() {
    try {
        if (typeof nextTrack === 'function') {
            nextTrack();
            showKeyboardToast('⏭️ Next track');
        } else {
            console.warn('[Keyboard Shortcuts] nextTrack() function not available');
        }
    } catch (e) {
        console.error('[Keyboard Shortcuts] Error calling nextTrack:', e);
    }
}

/**
 * Previous track handler
 */
function handlePreviousTrack() {
    try {
        if (typeof previousTrack === 'function') {
            previousTrack();
            showKeyboardToast('⏮️ Previous track');
        } else {
            console.warn('[Keyboard Shortcuts] previousTrack() function not available');
        }
    } catch (e) {
        console.error('[Keyboard Shortcuts] Error calling previousTrack:', e);
    }
}

/**
 * Volume increase handler - respects hidden volume setting
 */
function handleVolumeIncrease() {
    try {
        // Check if volume controls are hidden
        const volumeSection = document.querySelector('.volume-controls-simple');
        if (volumeSection && volumeSection.style.display === 'none') {
            // Volume controls are hidden, don't allow volume adjustment
            showKeyboardToast('⚠️ Volume controls hidden', 'warning', 1500);
            return;
        }

        if (typeof adjustVolume === 'function') {
            adjustVolume(2);
            showKeyboardToast('🔊 Volume +2%');
        } else {
            console.warn('[Keyboard Shortcuts] adjustVolume() function not available');
        }
    } catch (e) {
        console.error('[Keyboard Shortcuts] Error adjusting volume:', e);
    }
}

/**
 * Volume decrease handler - respects hidden volume setting
 */
function handleVolumeDecrease() {
    try {
        // Check if volume controls are hidden
        const volumeSection = document.querySelector('.volume-controls-simple');
        if (volumeSection && volumeSection.style.display === 'none') {
            // Volume controls are hidden, don't allow volume adjustment
            showKeyboardToast('⚠️ Volume controls hidden', 'warning', 1500);
            return;
        }

        if (typeof adjustVolume === 'function') {
            adjustVolume(-2);
            showKeyboardToast('🔉 Volume -2%');
        } else {
            console.warn('[Keyboard Shortcuts] adjustVolume() function not available');
        }
    } catch (e) {
        console.error('[Keyboard Shortcuts] Error adjusting volume:', e);
    }
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
