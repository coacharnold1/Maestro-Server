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

console.log('[Keyboard Shortcuts] Script loaded!');

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
        // Check for our shortcut keys FIRST before checking if we're typing
        const isShortcutKey = event.code === 'Space' || 
                             event.key === 'ArrowRight' || 
                             event.key === 'ArrowLeft' || 
                             event.key === 'ArrowUp' || 
                             event.key === 'ArrowDown';
        
        // If it's not one of our shortcuts, don't interfere
        if (!isShortcutKey) {
            return;
        }

        console.log('[Keyboard Shortcuts] Shortcut detected:', event.code || event.key);

        // Don't trigger shortcuts if user is typing in an input or textarea
        const activeElement = document.activeElement;
        const isTyping = activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA';
        
        if (isTyping) {
            console.log('[Keyboard Shortcuts] Skipping - typing in input');
            return;
        }

        // PREVENT DEFAULT FIRST - this stops scrolling/jumping
        event.preventDefault();
        event.stopPropagation();
        console.log('[Keyboard Shortcuts] preventDefault called');

        // Spacebar: Toggle play/pause
        if (event.code === 'Space') {
            console.log('[Keyboard Shortcuts] Spacebar pressed');
            togglePlayPause();
            return;
        }

        // Right Arrow: Next track
        if (event.key === 'ArrowRight') {
            console.log('[Keyboard Shortcuts] Right arrow pressed');
            handleNextTrack();
            return;
        }

        // Left Arrow: Previous track
        if (event.key === 'ArrowLeft') {
            console.log('[Keyboard Shortcuts] Left arrow pressed');
            handlePreviousTrack();
            return;
        }

        // Up Arrow: Volume +2%
        if (event.key === 'ArrowUp') {
            console.log('[Keyboard Shortcuts] Up arrow pressed');
            handleVolumeIncrease();
            return;
        }

        // Down Arrow: Volume -2%
        if (event.key === 'ArrowDown') {
            console.log('[Keyboard Shortcuts] Down arrow pressed');
            handleVolumeDecrease();
            return;
        }
    }, { passive: false });  // Important: passive: false allows preventDefault to work
}

/**
 * Toggle play/pause - plays if stopped, pauses if playing
 */
function togglePlayPause() {
    try {
        // Look for pause button and check if it's actually visible using computed styles
        let pauseButtonVisible = false;
        const allButtons = document.querySelectorAll('button');
        
        for (const btn of allButtons) {
            const hasIcon = btn.textContent.includes('⏸');
            const hasAttr = btn.getAttribute('data-i18n') === 'pause';
            
            if (hasIcon || hasAttr) {
                // Found a pause button - check if it's visible using computed styles
                const computedStyle = window.getComputedStyle(btn);
                const isVisible = computedStyle.display !== 'none' && 
                                 computedStyle.visibility !== 'hidden' && 
                                 btn.offsetParent !== null;
                
                if (isVisible) {
                    pauseButtonVisible = true;
                    break;
                }
            }
        }
        
        if (pauseButtonVisible) {
            // Pause button IS visible → music IS playing → PAUSE it
            if (typeof pauseMusic === 'function') {
                pauseMusic();
            }
        } else {
            // Pause button NOT visible → music is NOT playing → PLAY it
            if (typeof playMusic === 'function') {
                playMusic();
            }
        }
        // Let pauseMusic/playMusic functions handle their own toast messages
        
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
