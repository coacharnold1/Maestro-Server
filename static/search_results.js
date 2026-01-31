// Search Results JavaScript - External Script
// All logic moved from inline <script> tags to fix Jinja2 execution issue
// Note: Version info is loaded via global version-loader.js

// Socket.IO connection for real-time updates
const socket = io();
const maestroLogo = document.getElementById('maestro-logo');

socket.on('status_update', function(data) {
    // Update logo based on playback state
    if (maestroLogo) {
        maestroLogo.src = data.state === 'play' ? "/static/logo.svg" : "/static/logo-static.svg";
    }
});

socket.on('disconnect', function() {
    // Use static logo when not connected
    if (maestroLogo) maestroLogo.src = "/static/logo-static.svg";
});

// Fetch initial state to set logo correctly on page load
fetch('/get_mpd_status')
    .then(r => r.json())
    .then(data => {
        if (maestroLogo && data.state === 'play') {
            maestroLogo.src = "/static/logo.svg";
        } else if (maestroLogo) {
            maestroLogo.src = "/static/logo-static.svg";
        }
    })
    .catch(err => console.error('Error fetching initial state:', err));


// Playback control functions
function playbackAction(action) {
    fetch(`/${action}?ajax=1`, {
        method: 'GET'
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log(data.message);
                displayMessage('info', data.message || `${action.charAt(0).toUpperCase() + action.slice(1)} command sent`);
            } else {
                console.error(data.message || `Failed to ${action}`);
                displayMessage('error', data.message || `Failed to ${action}`);
            }
        })
        .catch(err => {
            console.error(`Error: ${err.message}`);
            displayMessage('error', `Error: ${err.message}`);
        });
}

// Clear playlist function
function clearPlaylist() {
    if (confirm('Are you sure you want to clear the entire playlist?')) {
        fetch('/clear_playlist?ajax=1', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    displayMessage('info', 'Playlist cleared');
                } else {
                    displayMessage('error', data.message || 'Error clearing playlist');
                }
            })
            .catch(error => {
                displayMessage('error', 'Error clearing playlist: ' + error.message);
            });
    }
}

// Clear and add functions (replace playlist)
function clearAndAddAlbum(artist, album) {
    console.log('clearAndAddAlbum called with:', {artist, album});
    
    if (!album || !artist) {
        console.error('Missing artist or album');
        displayMessage('error', 'Missing artist or album information');
        return;
    }
    
    if (confirm(`Clear playlist and start playing album "${album}" by ${artist}?`)) {
        displayMessage('info', 'Clearing playlist and adding album...');
        
        fetch('/clear_playlist?ajax=1', { method: 'POST' })
            .then(response => {
                console.log('Clear playlist response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Clear playlist response:', data);
                if (data.status === 'success') {
                    return addAlbumToPlaylist(album, artist, false);
                } else {
                    throw new Error('Failed to clear playlist');
                }
            })
            .then(() => {
                // Auto-play after adding
                console.log('Starting playback...');
                return fetch('/play?ajax=1', { method: 'POST' });
            })
            .then(response => {
                console.log('Play response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Play response:', data);
                displayMessage('success', `Now playing: "${album}" by ${artist}`);
            })
            .catch(error => {
                console.error('Error in clearAndAddAlbum:', error);
                displayMessage('error', 'Error: ' + error.message);
            });
    }
}

function clearAndAddSong(file) {
    console.log('clearAndAddSong called with:', file);
    
    if (!file) {
        console.error('No file provided to clearAndAddSong');
        displayMessage('error', 'No song file provided');
        return;
    }
    
    if (confirm('Clear playlist and start playing this song?')) {
        displayMessage('info', 'Clearing playlist and adding song...');
        
        fetch('/clear_playlist?ajax=1', { method: 'POST' })
            .then(response => {
                console.log('Clear playlist response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Clear playlist response:', data);
                if (data.status === 'success') {
                    return addSongToPlaylist(file, false);
                } else {
                    throw new Error('Failed to clear playlist');
                }
            })
            .then(() => {
                // Auto-play after adding
                console.log('Starting playback...');
                return fetch('/play?ajax=1', { method: 'POST' });
            })
            .then(response => {
                console.log('Play response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Play response:', data);
                displayMessage('success', 'Now playing song');
            })
            .catch(error => {
                console.error('Error in clearAndAddSong:', error);
                displayMessage('error', 'Error: ' + error.message);
            });
    }
}

// Add to playlist functions
function addAlbumToPlaylist(album, artist, discNumber = null) {
    console.log('addAlbumToPlaylist called with:', {album, artist, discNumber});
    
    const payload = {
        album: album,
        artist: artist
    };
    
    if (discNumber !== null) {
        payload.disc_number = discNumber;
    }

    displayMessage('info', 'Adding album to playlist...');
    
    return fetch('/add_album_to_playlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
        .then(response => {
            console.log('Add album response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Add album response data:', data);
            if (data.status === 'success') {
                const discInfo = discNumber ? ` (Disc ${discNumber})` : '';
                displayMessage('success', `Album "${album}" by ${artist}${discInfo} added to playlist`);
            } else {
                displayMessage('error', data.message || 'Failed to add album');
            }
        })
        .catch(error => {
            console.error('Error adding album:', error);
            displayMessage('error', 'Error adding album: ' + error.message);
        });
}

function addSongToPlaylist(file, showConfirm = true) {
    console.log('addSongToPlaylist called with:', file);
    
    if (!file) {
        console.error('No file provided to addSongToPlaylist');
        displayMessage('error', 'No song file provided');
        return Promise.reject(new Error('No file provided'));
    }
    
    const formData = new FormData();
    formData.append('file', file);

    displayMessage('info', 'Adding song to playlist...');

    return fetch('/add_song_to_playlist', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            console.log('Add song response status:', response.status);
            return response.text();
        })
        .then(data => {
            console.log('Add song response:', data);
            displayMessage('success', 'Song added to playlist');
        })
        .catch(error => {
            console.error('Error adding song:', error);
            displayMessage('error', 'Error adding song: ' + error.message);
        });
}

// Format duration from seconds to MM:SS
function formatDuration(seconds) {
    if (!seconds || seconds === '0' || seconds === '') return '';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Escape HTML to prevent XSS and display issues
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Album drill-down functions
function viewAlbumSongs(artist, album) {
    displayMessage('info', `Loading songs for "${album}" by ${artist}...`);

    // Fetch album songs from server
    const formData = new FormData();
    formData.append('artist', artist);
    formData.append('album', album);

    fetch('/get_album_songs', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            // Handle both old format (array) and new format (object with songs/disc_structure)
            const songs = Array.isArray(data) ? data : data.songs;
            const discStructure = data.disc_structure || null;
            showAlbumSongs(artist, album, songs, discStructure);
        })
        .catch(error => {
            displayMessage('error', 'Error loading album songs: ' + error.message);
        });
}

function showAlbumSongs(artist, album, songs, discStructure) {
    // Hide search results and show album songs section
    const resultsSection = document.querySelector('.song-list');
    const searchResultsInfo = document.getElementById('search-results-info');
    const albumSection = document.getElementById('album-songs-section');
    const albumInfo = document.getElementById('album-info');
    const songsList = document.getElementById('album-songs-list');
    const albumArtLarge = document.getElementById('album-art-large');

    // Insert large album art
    let artUrl = `/album_art?artist=${encodeURIComponent(artist)}&album=${encodeURIComponent(album)}&size=full`;
    if (songs.length && songs[0].file) {
        artUrl = `/album_art?file=${encodeURIComponent(songs[0].file)}&artist=${encodeURIComponent(artist)}&album=${encodeURIComponent(album)}&size=full`;
    }
    albumArtLarge.innerHTML = `<img src="${artUrl}" alt="${album} cover" style="max-width:300px; max-height:300px; border-radius:12px; box-shadow:0 4px 18px #222; margin-bottom:18px; background:#222;" onerror="this.src='/static_placeholder_art'">`;

    // Update album info
    const discInfo = discStructure ? ` - ${Object.keys(discStructure).length} discs` : '';
    albumInfo.innerHTML = `<div class="results-info">Songs in "${album}" by <strong>${artist}</strong> (${songs.length} tracks${discInfo})</div>`;

    // Clear and populate songs list
    songsList.innerHTML = '';
    
    // If multi-disc album, display by disc
    if (discStructure) {
        const discNumbers = Object.keys(discStructure).map(Number).sort((a, b) => a - b);
        
        discNumbers.forEach(discNum => {
            const discTracks = discStructure[discNum];
            
            // Create disc header with add button
            const discHeader = document.createElement('div');
            discHeader.style.cssText = 'background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); padding: 12px 18px; margin: 20px 0 10px 0; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid #3498db;';
            discHeader.innerHTML = `
                <h3 style="margin: 0; color: #ecf0f1; font-size: 1.1em;">💿 Disc ${discNum}</h3>
                <button onclick="addAlbumToPlaylist('${album.replace(/'/g, "\\'")}', '${artist.replace(/'/g, "\\'")}', ${discNum})" 
                        style="background: #27ae60; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; font-weight: bold; transition: background 0.3s;"
                        onmouseover="this.style.background='#229954'" 
                        onmouseout="this.style.background='#27ae60'">
                    ➕ Add Disc ${discNum}
                </button>
            `;
            songsList.appendChild(discHeader);
            
            // Add tracks for this disc
            discTracks.forEach((song, index) => {
                const li = document.createElement('li');
                
                // Create song info
                const songInfo = document.createElement('div');
                songInfo.className = 'song-info';
                songInfo.innerHTML = `
                    <div class="title">${index + 1}. ${escapeHtml(song.title || 'Unknown Title')}</div>
                    <div class="artist">${escapeHtml(song.artist || artist)}</div>
                    <div class="album">${escapeHtml(song.album || album)}</div>
                    ${song.time ? `<div class="duration">⏱️ ${formatDuration(song.time)}</div>` : ''}
                `;
                
                // Create action buttons with data attributes
                const songActions = document.createElement('div');
                songActions.className = 'song-actions';
                
                const startBtn = document.createElement('button');
                startBtn.className = 'btn-start-single-song';
                startBtn.textContent = '🔄 Start Playing';
                startBtn.dataset.file = song.file;
                startBtn.dataset.title = song.title || 'Unknown Title';
                
                const addBtn = document.createElement('button');
                addBtn.className = 'btn-add-single-song';
                addBtn.textContent = '➕ Add Song';
                addBtn.dataset.file = song.file;
                
                songActions.appendChild(startBtn);
                songActions.appendChild(addBtn);
                
                li.appendChild(songInfo);
                li.appendChild(songActions);
                songsList.appendChild(li);
            });
        });
    } else {
        // Single disc - display normally
        songs.forEach((song, index) => {
            const li = document.createElement('li');
            
            // Create song info
            const songInfo = document.createElement('div');
            songInfo.className = 'song-info';
            songInfo.innerHTML = `
                <div class="title">${index + 1}. ${escapeHtml(song.title || 'Unknown Title')}</div>
                <div class="artist">${escapeHtml(song.artist || artist)}</div>
                <div class="album">${escapeHtml(song.album || album)}</div>
                ${song.time ? `<div class="duration">⏱️ ${formatDuration(song.time)}</div>` : ''}
            `;
            
            // Create action buttons with data attributes
            const songActions = document.createElement('div');
            songActions.className = 'song-actions';
            
            const startBtn = document.createElement('button');
            startBtn.className = 'btn-start-single-song';
            startBtn.textContent = '🔄 Start Playing';
            startBtn.dataset.file = song.file;
            startBtn.dataset.title = song.title || 'Unknown Title';
            
            const addBtn = document.createElement('button');
            addBtn.className = 'btn-add-single-song';
            addBtn.textContent = '➕ Add Song';
            addBtn.dataset.file = song.file;
            
            songActions.appendChild(startBtn);
            songActions.appendChild(addBtn);
            
            li.appendChild(songInfo);
            li.appendChild(songActions);
            songsList.appendChild(li);
        });
    }

    // Hide search results, show album songs
    if (resultsSection) resultsSection.style.display = 'none';
    if (searchResultsInfo) searchResultsInfo.style.display = 'none';
    albumSection.style.display = 'block';

    // Scroll to top
    window.scrollTo(0, 0);
}

function hideAlbumSongs() {
    // Hide album songs and show search results
    const resultsSection = document.querySelector('.song-list');
    const searchResultsInfo = document.getElementById('search-results-info');
    const albumSection = document.getElementById('album-songs-section');

    albumSection.style.display = 'none';
    if (resultsSection) resultsSection.style.display = 'block';
    if (searchResultsInfo) searchResultsInfo.style.display = 'block';

    // Scroll to top
    window.scrollTo(0, 0);
}

// Special function for individual songs from album drill-down
function clearAndAddSingleSong(file, title) {
    if (confirm(`Clear playlist and start playing "${title}"?`)) {
        fetch('/clear_playlist?ajax=1', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    return addSongToPlaylist(file, false);
                } else {
                    throw new Error('Failed to clear playlist');
                }
            })
            .then(() => {
                // Auto-play after adding
                return fetch('/play?ajax=1', { method: 'POST' });
            })
            .then(response => response.json())
            .then(data => {
                displayMessage('info', `Now playing: "${title}"`);
            })
            .catch(error => {
                displayMessage('error', 'Error: ' + error.message);
            });
    }
}

function displayMessage(type, text) {
    const messageArea = document.getElementById('message-area');
    messageArea.textContent = text;
    messageArea.className = `show ${type}`;
    messageArea.style.opacity = 1;

    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageArea.style.opacity = 0;
        setTimeout(() => {
            messageArea.textContent = '';
            messageArea.className = '';
        }, 300);
    }, 5000);
}

// Wire up button clicks via data-* attributes
// Execute immediately since DOM is already loaded (script at bottom of page)
(function() {
    console.log('Initializing search results button handlers...');
    
    const viewAlbumBtns = document.querySelectorAll('.btn-view-album');
    console.log('Found', viewAlbumBtns.length, 'view album buttons');
    viewAlbumBtns.forEach(btn => {
        btn.addEventListener('click', function(){
            const artist = this.dataset.artist || '';
            const album = this.dataset.album || '';
            console.log('View album clicked:', artist, album);
            viewAlbumSongs(artist, album);
        });
    });
    
    const replaceAlbumBtns = document.querySelectorAll('.btn-replace-album');
    console.log('Found', replaceAlbumBtns.length, 'replace album buttons');
    replaceAlbumBtns.forEach(btn => {
        btn.addEventListener('click', function(){
            const artist = this.dataset.artist || '';
            const album = this.dataset.album || '';
            console.log('Replace album clicked:', artist, album);
            clearAndAddAlbum(artist, album);
        });
    });
    
    const addAlbumBtns = document.querySelectorAll('.btn-add-album');
    console.log('Found', addAlbumBtns.length, 'add album buttons');
    addAlbumBtns.forEach(btn => {
        btn.addEventListener('click', function(){
            const artist = this.dataset.artist || '';
            const album = this.dataset.album || '';
            console.log('Add album clicked:', artist, album);
            addAlbumToPlaylist(album, artist);
        });
    });
    
    const replaceSongBtns = document.querySelectorAll('.btn-replace-song');
    console.log('Found', replaceSongBtns.length, 'replace song buttons');
    replaceSongBtns.forEach(btn => {
        btn.addEventListener('click', function(){
            const file = this.dataset.file || '';
            console.log('Replace song clicked:', file);
            clearAndAddSong(file);
        });
    });
    
    const addSongBtns = document.querySelectorAll('.btn-add-song');
    console.log('Found', addSongBtns.length, 'add song buttons');
    addSongBtns.forEach(btn => {
        btn.addEventListener('click', function(){
            const file = this.dataset.file || '';
            console.log('Add song clicked:', file);
            addSongToPlaylist(file);
        });
    });
    
    // Event delegation for dynamically created album drill-down buttons
    document.addEventListener('click', function(e) {
        // Handle "Start Playing" button in album drill-down
        if (e.target.classList.contains('btn-start-single-song')) {
            const file = e.target.dataset.file;
            const title = e.target.dataset.title;
            console.log('Start single song clicked:', file, title);
            if (file) {
                clearAndAddSingleSong(file, title);
            } else {
                console.error('No file data on start button');
                displayMessage('error', 'No song file available');
            }
        }
        
        // Handle "Add Song" button in album drill-down
        if (e.target.classList.contains('btn-add-single-song')) {
            const file = e.target.dataset.file;
            console.log('Add single song clicked:', file);
            if (file) {
                addSongToPlaylist(file);
            } else {
                console.error('No file data on add button');
                displayMessage('error', 'No song file available');
            }
        }
    });
    
    console.log('Search results button handlers initialized');
})();

console.log('[SUCCESS] search_results.js loaded');
