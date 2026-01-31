// Browse Albums JavaScript - External Script
// This must be external to work around inline script issues

// Get parameters from URL
const urlParams = new URLSearchParams(window.location.search);
const artistName = urlParams.get('artist');
const genreName = urlParams.get('genre');

console.log('[DEBUG] browse_albums.js - artistName from URL:', artistName);
console.log('[DEBUG] browse_albums.js - genreName from URL:', genreName);

// Change loading div IMMEDIATELY to prove top-level script runs
const loadingDiv = document.getElementById('loading');
if (loadingDiv) {
    loadingDiv.innerHTML = '<div style="color: #3498db; font-weight: bold;">🔄 Loading... (external script fired)</div>';
}

document.addEventListener('DOMContentLoaded', function () {
    // Check if Bandcamp is configured
    fetch('/api/settings')
        .then(r => r.json())
        .then(data => {
            if (data.bandcamp_enabled && data.bandcamp_username && data.bandcamp_identity_token) {
                document.getElementById('bandcamp-link').style.display = 'inline-block';
            }
        })
        .catch(e => console.log('Could not check Bandcamp settings'));
    
    // SocketIO setup for now playing bar (removed - not available on test server)
    const nowPlayingBar = document.getElementById('now-playing-bar');
    const npArtist = document.getElementById('np-artist');
    const npAlbum = document.getElementById('np-album');
    const npTrack = document.getElementById('np-track');

    // Fetch initial state to set logo correctly on page load
    fetch('/api/version')
        .then(() => fetch('/get_mpd_status'))
        .then(r => r.json())
        .then(data => {
            if (data.state === 'play') {
                // Logo already set to animated, no change needed
            } else {
                // Set to static logo
                document.getElementById('maestro-logo-albums') && (document.getElementById('maestro-logo-albums').src = '/static/logo-static.svg');
            }
            if (data.state === 'play' || data.state === 'pause') {
                if (data.artist && data.artist !== 'N/A' && data.song_title && data.song_title !== 'N/A') {
                    nowPlayingBar.style.display = 'block';
                    npArtist.textContent = data.artist;
                    npAlbum.textContent = data.album || 'Unknown Album';
                    npTrack.textContent = data.song_title;
                }
            }
        })
        .catch(err => console.error('Error fetching initial state:', err));

    if (artistName) {
        console.log('[DEBUG] DOMContentLoaded fired - artistName exists:', artistName);
        document.getElementById('artist-title').textContent = `Artist: ${artistName}`;
        document.getElementById('back-link').href = `/browse/artists?genre=${encodeURIComponent(genreName)}`;
        console.log('[DEBUG] About to call loadAlbums with:', artistName);
        loadAlbums(artistName);
    } else {
        showError('No artist specified');
    }
});

function loadAlbums(artist) {
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const albumList = document.getElementById('album-list');
    const stats = document.getElementById('stats');

    loading.style.display = 'block';
    error.style.display = 'none';
    albumList.style.display = 'none';
    stats.style.display = 'none';

    const apiUrl = `/api/browse/albums?artist=${encodeURIComponent(artist)}${genreName ? `&genre=${encodeURIComponent(genreName)}` : ''}`;
    console.log('[DEBUG] browse_albums.js - Fetching:', apiUrl);

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            loading.style.display = 'none';

            if (data.status === 'success') {
                displayAlbums(data.albums);
                document.getElementById('album-count').textContent = data.count;
                stats.style.display = 'block';
            } else {
                showError(data.message || 'Failed to load albums');
            }
        })
        .catch(err => {
            loading.style.display = 'none';
            showError('Network error loading albums: ' + err.message);
        });
}

function displayAlbums(albums) {
    const albumList = document.getElementById('album-list');
    albumList.innerHTML = ''; // Clear any existing content

    if (albums.length === 0) {
        albumList.innerHTML = '<li style="text-align: center; padding: 40px; color: #bdc3c7;">No albums found</li>';
        albumList.style.display = 'block';
        return;
    }

    albums.forEach((album, index) => {
        const listItem = document.createElement('li');
        listItem.className = 'album-item';

        // Build thumbnail URL - use sample_file if available, otherwise fallback to artist/album
        let thumbnailUrl;
        if (album.sample_file) {
            thumbnailUrl = `/album_art?file=${encodeURIComponent(album.sample_file)}&artist=${encodeURIComponent(album.artist)}&album=${encodeURIComponent(album.album)}&size=thumb`;
        } else {
            thumbnailUrl = `/album_art?artist=${encodeURIComponent(album.artist)}&album=${encodeURIComponent(album.album)}&size=thumb`;
        }
        
        // Build title - add disc number if this is a disc entry
        const titleDisplay = album.disc_number 
            ? `${escapeHtml(album.album)} - Disc ${album.disc_number}`
            : `${escapeHtml(album.album)}`;

        listItem.innerHTML = `
            <div class="album-content">
                <img src="${thumbnailUrl}" 
                     alt="${escapeHtml(album.album)} cover" 
                     class="album-thumbnail"
                     loading="lazy"
                     onerror="this.style.display='none';">
                <div class="album-info-container" style="flex: 1;">
                    <div class="album-header">
                        <div class="album-info">
                            <div class="album-title">${titleDisplay}</div>
                            <div class="album-artist">by <a href="/search?query=${encodeURIComponent(stripLocation(album.artist))}&type=artist" style="color:#27ae60; text-decoration:underline;">${escapeHtml(album.artist)}</a></div>
                            <div class="album-meta">
                                📀 ${album.track_count} tracks
                                ${album.date ? `• 📅 ${album.date}` : ''}
                            </div>
                        </div>
                        <div class="album-actions">
                            <button class="btn btn-warning" onclick="clearAndAddAlbum('${jsString(album.artist)}', '${jsString(album.album)}'${album.disc_number ? `, ${album.disc_number}` : ''})">
                                🔄 Replace Playlist
                            </button>
                            <button class="btn btn-primary" onclick="addAlbumToPlaylist('${jsString(album.artist)}', '${jsString(album.album)}'${album.disc_number ? `, ${album.disc_number}` : ''})">
                                ➕ Add ${album.disc_number ? `Disc ${album.disc_number}` : 'Album'}
                            </button>
                            <button class="btn btn-secondary" onclick="toggleAlbumDetails('${jsString(album.album)}', '${jsString(album.artist)}', ${index})">
                                🔍 View Tracks
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            <div class="album-details" id="details-${index}" style="display: none;">
                <div class="loading-tracks" id="loading-${index}" style="text-align: center; padding: 20px; color: #bdc3c7;">
                    Loading tracks...
                </div>
                <div class="tracks-list" id="tracks-${index}" style="display: none;"></div>
            </div>
        `;

        albumList.appendChild(listItem);
    });

    albumList.style.display = 'block';
}

function addAlbumToPlaylist(artistName, albumName, discNumber) {
    const discText = discNumber ? ` (Disc ${discNumber})` : '';
    showMessage(`Adding album${discText} to playlist...`, 'info');

    const payload = {
        album: albumName,
        artist: artistName
    };
    
    if (discNumber) {
        payload.disc_number = discNumber;
    }

    fetch('/add_album_to_playlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showMessage(data.message, 'success');
            } else {
                showMessage(data.message || 'Failed to add album', 'error');
            }
        })
        .catch(err => {
            showMessage('Error adding album: ' + err.message, 'error');
        });
}

function clearAndAddAlbum(artistName, albumName, discNumber) {
    const discText = discNumber ? ` (Disc ${discNumber})` : '';

    // First, get the current playlist length (with cache-busting)
    fetch('/get_mpd_status?_t=' + Date.now())
        .then(response => response.json())
        .then(statusData => {
            const tracksCleared = statusData.queue_length || 0;
            console.log('[clearAndAddAlbum] Current playlist length:', tracksCleared);
            
            const payload = {
                album: albumName,
                artist: artistName
            };
            
            if (discNumber) {
                payload.disc_number = discNumber;
            }

            fetch('/clear_and_add_album', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showMessage(`▶️ ${tracksCleared} tracks cleared, now playing: ${artistName} - ${albumName}`, 'success');
                        // Auto-play after a brief delay
                        setTimeout(() => playbackAction('play'), 500);
                    } else {
                        showMessage(data.message || 'Failed to replace playlist', 'error');
                    }
                })
                .catch(err => {
                    showMessage('Error replacing playlist: ' + err.message, 'error');
                });
        })
        .catch(err => {
            showMessage('Error fetching playlist info: ' + err.message, 'error');
        });
}

function toggleAlbumDetails(albumName, artistName, index) {
    const detailsDiv = document.getElementById(`details-${index}`);
    const loadingDiv = document.getElementById(`loading-${index}`);
    const tracksDiv = document.getElementById(`tracks-${index}`);
    const button = event.target;

    if (detailsDiv.style.display === 'none') {
        detailsDiv.style.display = 'block';
        button.textContent = '🔼 Hide Tracks';
        loadingDiv.style.display = 'block';
        tracksDiv.style.display = 'none';

        fetch(`/api/album_tracks?album=${encodeURIComponent(albumName)}&artist=${encodeURIComponent(artistName)}`)
            .then(response => response.json())
            .then(data => {
                loadingDiv.style.display = 'none';
                if (data.status === 'success' && data.tracks && data.tracks.length > 0) {
                    // Check if this is a multi-disc album
                    if (data.disc_structure) {
                        displayMultiDiscTracks(data.disc_structure, albumName, artistName, index);
                    } else {
                        displayTracks(data.tracks, index);
                    }
                } else {
                    tracksDiv.innerHTML = '<p style="color: #bdc3c7; text-align: center;">No tracks found</p>';
                }
                tracksDiv.style.display = 'block';
            })
            .catch(err => {
                loadingDiv.style.display = 'none';
                tracksDiv.innerHTML = '<p style="color: #e74c3c; text-align: center;">Error loading tracks</p>';
                tracksDiv.style.display = 'block';
            });
    } else {
        detailsDiv.style.display = 'none';
        button.textContent = '🔍 Show Tracks';
    }
}

function displayTracks(tracks, index) {
    const tracksDiv = document.getElementById(`tracks-${index}`);

    if (tracks.length === 0) {
        tracksDiv.innerHTML = '<p style="color: #bdc3c7; text-align: center;">No tracks found</p>';
        return;
    }

    let tracksHtml = '';
    tracks.forEach((track, trackIndex) => {
        const duration = track.time ? formatDuration(parseInt(track.time)) : '--:--';
        tracksHtml += `
            <div class="track-item">
                <div class="track-info">
                    <div class="track-title">${trackIndex + 1}. ${escapeHtml(track.title || 'Unknown Title')}</div>
                    <div class="track-duration">${duration}</div>
                </div>
                <div class="track-actions">
                    <button class="btn btn-primary" style="padding: 4px 8px; font-size: 0.8em;" 
                            onclick="addTrackToPlaylist('${escapeHtml(track.file)}')">
                        ➕ Add
                    </button>
                </div>
            </div>
        `;
    });

    tracksDiv.innerHTML = tracksHtml;
}

function displayMultiDiscTracks(discStructure, albumName, artistName, index) {
    const tracksDiv = document.getElementById(`tracks-${index}`);
    
    let discsHtml = '';
    const discNumbers = Object.keys(discStructure).map(Number).sort((a, b) => a - b);
    
    discNumbers.forEach(discNum => {
        const discTracks = discStructure[discNum];
        
        // Calculate disc duration
        let discDuration = 0;
        discTracks.forEach(track => {
            if (track.time) {
                discDuration += parseInt(track.time);
            }
        });
        const discDurationFormatted = formatDuration(discDuration);
        
        discsHtml += `
            <div class="disc-section" style="margin-bottom: 20px; border: 1px solid #34495e; border-radius: 5px; padding: 15px; background-color: #1e2a35;">
                <div class="disc-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #27ae60;">
                    <div>
                        <h3 style="margin: 0; color: #27ae60;">💿 Disc ${discNum}</h3>
                        <div style="color: #bdc3c7; font-size: 0.9em; margin-top: 5px;">
                            ${discTracks.length} tracks • ${discDurationFormatted}
                        </div>
                    </div>
                    <button class="btn btn-primary" onclick="addAlbumToPlaylist('${artistName.replace(/'/g, "\\'")}', '${albumName.replace(/'/g, "\\'")}', ${discNum})">
                        ➕ Add Disc ${discNum}
                    </button>
                </div>
                <div class="disc-tracks">
        `;
        
        discTracks.forEach((track, trackIndex) => {
            const duration = track.time ? formatDuration(parseInt(track.time)) : '--:--';
            discsHtml += `
                <div class="track-item">
                    <div class="track-info">
                        <div class="track-title">${trackIndex + 1}. ${escapeHtml(track.title || 'Unknown Title')}</div>
                        <div class="track-duration">${duration}</div>
                    </div>
                    <div class="track-actions">
                        <button class="btn btn-primary" style="padding: 4px 8px; font-size: 0.8em;" 
                                onclick="addTrackToPlaylist('${escapeHtml(track.file)}')">
                            ➕ Add
                        </button>
                    </div>
                </div>
            `;
        });
        
        discsHtml += `
                </div>
            </div>
        `;
    });
    
    tracksDiv.innerHTML = discsHtml;
}

function addTrackToPlaylist(filePath) {
    fetch('/add_song_to_playlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `file=${encodeURIComponent(filePath)}`
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showMessage('Track added to playlist', 'success');
            } else {
                showMessage('Failed to add track', 'error');
            }
        })
        .catch(err => {
            showMessage('Error adding track: ' + err.message, 'error');
        });
}

function clearPlaylist() {
    if (confirm('Are you sure you want to clear the entire playlist?')) {
        fetch('/clear_playlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showMessage('Playlist cleared', 'success');
                } else {
                    showMessage(data.message || 'Failed to clear playlist', 'error');
                }
            })
            .catch(err => {
                showMessage('Error clearing playlist: ' + err.message, 'error');
            });
    }
}

function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function showError(message) {
    const error = document.getElementById('error');
    error.textContent = message;
    error.style.display = 'block';
}

function showMessage(text, type) {
    const existingMessages = document.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());

    const message = document.createElement('div');
    message.className = `message ${type}`;
    message.textContent = text;
    document.body.appendChild(message);

    setTimeout(() => {
        message.style.opacity = '0';
        setTimeout(() => {
            if (message.parentNode) {
                message.parentNode.removeChild(message);
            }
        }, 300);
    }, 5000);
}

// Function to strip location tags like [down], [up], etc. from artist names
function stripLocation(text) {
    if (!text) return text;
    return text.replace(/\s*\[.*?\]\s*$/g, '').trim();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function jsString(text) {
    if (text === undefined || text === null) return '';
    return String(text).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}

// Playback control function
function playbackAction(action) {
    fetch(`/${action}?ajax=1`, {
        method: 'GET'
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showMessage(data.message, 'success');
            } else {
                showMessage(data.message || `Failed to ${action}`, 'error');
            }
        })
        .catch(err => {
            showMessage(`Error: ${err.message}`, 'error');
        });
}

console.log('[SUCCESS] browse_albums.js loaded');
