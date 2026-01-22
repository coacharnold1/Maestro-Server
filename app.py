print("[DEBUG] app.py loaded and running", flush=True)

# Application version information
APP_VERSION = "2.8.0"
APP_BUILD_DATE = "2026-01-21" 
APP_NAME = "Maestro MPD Server"

# Simple threading mode to avoid eventlet issues
import os
os.environ["EVENTLET_THREADING"] = "1"

from flask import Flask, render_template, redirect, url_for, request, send_from_directory, Response, jsonify, flash
from flask_socketio import SocketIO, emit
from mpd import MPDClient, ConnectionError, CommandError
import socket
import subprocess
import os
import json
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import time
import requests
import random

# Settings and data files
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')
GENRE_STATIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'genre_stations.json')

# Settings helpers
def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading settings.json: {e}")
    # defaults
    return {
        'theme': 'dark',
        'lastfm_api_key': '',
        'lastfm_shared_secret': '',
        'show_scrobble_toasts': True
    }

def save_settings(data: dict) -> bool:
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        try:
            os.chmod(SETTINGS_FILE, 0o600)
        except Exception as pe:
            print(f"Warning: could not set permissions on settings.json: {pe}")
        return True
    except Exception as e:
        print(f"Error saving settings.json: {e}")
        return False

# Globals for Last.fm scrobbling
scrobbling_enabled = False
lastfm_session_key = ''
current_track_start_ts = None
current_track_identity = None  # tuple (artist, title, album, file)
current_track_total_secs = None
last_scrobbled_identity = None
show_scrobble_toasts = True

# Try to load environment variables, fallback to direct config if not available
try:
    from dotenv import load_dotenv
    # Load environment variables from config.env file
    load_dotenv('config.env')
    ENV_LOADED = True
except ImportError:
    print("python-dotenv not installed. Using fallback configuration.")
    ENV_LOADED = False

# Try to import search functionality, create fallback if not available
try:
    from rudimentary_search import perform_search
    SEARCH_AVAILABLE = True
except ImportError:
    print("rudimentary_search not available. Search functionality will be limited.")
    SEARCH_AVAILABLE = False
    def perform_search(client, search_tag, query):
        """Smart search function - groups by albums for artist/album searches"""
        try:
            if search_tag == 'any':
                results = client.search('any', query)
            else:
                results = client.search(search_tag, query)
            
            # For artist or album searches, group by albums
            if search_tag in ['artist', 'album']:
                albums_dict = {}
                for song in results:
                    album_name = song.get('album', 'Unknown Album')
                    artist_name = song.get('artist', 'Unknown Artist')
                    song_file = song.get('file', '')
                    # Group by artist, album, AND directory to show each physical copy separately
                    album_dir = os.path.dirname(song_file) if song_file else ''
                    album_key = f"{artist_name}|||{album_name}|||{album_dir}"
                    
                    if album_key not in albums_dict:
                        albums_dict[album_key] = {
                            'item_type': 'album',
                            'artist': artist_name,
                            'album': album_name,
                            'track_count': 0,
                            'sample_file': song_file  # First song file for album art
                        }
                    albums_dict[album_key]['track_count'] += 1
                
                return list(albums_dict.values())
            
            # For title/any searches, return individual songs
            formatted_results = []
            for song in results:
                formatted_results.append({
                    'item_type': 'song',
                    'artist': song.get('artist', 'Unknown Artist'),
                    'title': song.get('title', 'Unknown Title'),
                    'album': song.get('album', 'Unknown Album'),
                    'file': song.get('file', ''),
                    'time': song.get('time', '0'),
                })
            return formatted_results
        except Exception as e:
            print(f"Error in search: {e}")
            return []

# Load configuration from environment variables or use defaults
if ENV_LOADED:
    app_name = globals().get('__app_id__', 'mpd-web-control')
    app = Flask(app_name)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Configuration from environment
    MPD_HOST = os.environ.get('MPD_HOST', 'localhost')
    MPD_PORT = int(os.environ.get('MPD_PORT', '6600'))
    MPD_TIMEOUT = int(os.environ.get('MPD_TIMEOUT', '10'))
    MUSIC_DIRECTORY = os.environ.get('MUSIC_DIRECTORY', '/media/music')
    LASTFM_API_KEY = os.environ.get('LASTFM_API_KEY', '')
    LASTFM_SHARED_SECRET = os.environ.get('LASTFM_SHARED_SECRET', '')
    MAESTRO_CONFIG_URL = os.environ.get('MAESTRO_CONFIG_URL', '')
    
    # Add to Flask app config
    app.config['MAESTRO_CONFIG_URL'] = MAESTRO_CONFIG_URL
else:
    # Fallback configuration
    app_name = globals().get('__app_id__', 'mpd-web-control')
    app = Flask(app_name)
    app.secret_key = 'mpd-web-control-secret-key-2025'
    
    # Direct configuration (will be overridden by config.env if it exists)
    MPD_HOST = 'localhost'
    MPD_PORT = 6600
    MPD_TIMEOUT = 10
    MUSIC_DIRECTORY = '/media/music'
    LASTFM_API_KEY = ''  # Set in config.env or settings page for Last.fm integration
    LASTFM_SHARED_SECRET = ''  # Set in config.env or settings page for Last.fm integration
    MAESTRO_CONFIG_URL = ''  # Set in config.env for system config link (optional)

# Load persisted settings and apply precedence: env vars > settings.json > defaults
_settings = load_settings()
# Theme: environment variable overrides settings.json, which overrides default
app.config['THEME'] = os.getenv('DEFAULT_THEME', _settings.get('theme', 'dark'))

# Ensure proper UTF-8 handling for JSON and templates
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'
if not LASTFM_API_KEY:
    LASTFM_API_KEY = _settings.get('lastfm_api_key', '')
if not LASTFM_SHARED_SECRET:
    LASTFM_SHARED_SECRET = _settings.get('lastfm_shared_secret', '')
scrobbling_enabled = bool(_settings.get('enable_scrobbling', False))
lastfm_session_key = _settings.get('lastfm_session_key', '')
show_scrobble_toasts = bool(_settings.get('show_scrobble_toasts', True))

"""
Settings utilities moved near imports for early availability.
"""
GENRE_STATIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'genre_stations.json')

# Recent albums cache - simple and safe change detection
recent_albums_cache = None
recent_albums_cache_mod_times = None

# Playlists directory for saving/loading playlists
PLAYLISTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'playlists')
os.makedirs(PLAYLISTS_DIR, exist_ok=True)

# Play history tracking (session-based, cleared on server restart)
play_history = []
MAX_HISTORY_ITEMS = 100  # Keep last 100 songs
last_tracked_song_id = None  # Track song ID to avoid duplicates

# Configure SocketIO to use threading for async support (no eventlet issues)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# Font path for image generation
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Last.fm API URL (use HTTPS)
LASTFM_API_URL = 'https://ws.audioscrobbler.com/2.0/'
LASTFM_AUTH_URL = 'https://www.last.fm/api/auth/'

# Global variable to store the last known MPD status for comparison
last_mpd_status = {}

# Simple in-memory cache for Last.fm album art data
album_art_cache = {}

# Default HTTP headers for outbound requests (identify our app version)
DEFAULT_HTTP_HEADERS = {
    'User-Agent': f"{APP_NAME}/{APP_VERSION}"
}

# Inject theme into templates
@app.context_processor
def inject_globals():
    return {
        'app_theme': app.config.get('THEME', 'dark')
    }

@app.template_filter('strip_location')
def strip_location_tag(artist_name):
    """Remove location tags like [down], [cloyd], etc. from artist names."""
    if not artist_name:
        return artist_name
    import re
    # Remove anything in square brackets at the end
    return re.sub(r'\s*\[.*?\]\s*$', '', str(artist_name)).strip()

@app.template_filter('urlencode_str')
def urlencode_str(s):
    """URL encode a single string value for use in query parameters."""
    from urllib.parse import quote
    if s is None:
        return ''
    return quote(str(s), safe='')

# --- Auto-Fill Configuration ---
auto_fill_active = False
auto_fill_min_queue_length = 5
auto_fill_num_tracks_min = 20
auto_fill_num_tracks_max = 25
auto_fill_genre_filter_enabled = False
auto_fill_last_artist = "N/A"
auto_fill_last_genre = "N/A"

# Genre station mode variables
genre_station_mode = False
genre_station_name = ""
genre_station_genres = []

# Radio stations storage functions
def load_genre_stations():
    """Load genre stations from JSON file"""
    try:
        if os.path.exists(GENRE_STATIONS_FILE):
            with open(GENRE_STATIONS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading genre stations: {e}")
        return {}

def save_genre_stations(stations):
    """Save genre stations to JSON file"""
    try:
        with open(GENRE_STATIONS_FILE, 'w') as f:
            json.dump(stations, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving genre stations: {e}")
        return False

# --- API endpoint for application version info ---
@app.route('/api/version')
def get_version_info():
    return jsonify({
        'app_name': APP_NAME,
        'version': APP_VERSION,
        'build_date': APP_BUILD_DATE,
        'status': 'running'
    })

# --- API endpoint for auto-fill status (for Add Music page) ---
@app.route('/get_auto_fill_status')
def get_auto_fill_status():
    return jsonify({
        'active': auto_fill_active,
        'min_queue_length': auto_fill_min_queue_length,
        'num_tracks_min': auto_fill_num_tracks_min,
        'num_tracks_max': auto_fill_num_tracks_max,
        'genre_filter_enabled': auto_fill_genre_filter_enabled,
        'genre_station_mode': genre_station_mode,
        'genre_station_name': genre_station_name,
        'genre_station_genres': genre_station_genres
    })
# Simple in-memory cache for Last.fm album art data
album_art_cache = {}

def has_station_indicators(text):
    """Check if text contains common radio station indicators"""
    if not text:
        return False
    text_lower = text.lower()
    indicators = ['radio', '.com', '.fm', '.net', 'station', 'broadcasting', 'fm', 'am']
    return any(ind in text_lower for ind in indicators)

def parse_stream_metadata(title_field, name_field=None):
    """
    Parse streaming radio metadata that often comes in various formats:
    - 'Artist - Title' format
    - 'Title by Artist' format
    - 'Title by Artist - Station' format (complex)
    - 'Artist - Station' format (when second part has station indicators)
    Returns tuple: (artist, title, station_name)
    """
    if not title_field or title_field == 'N/A':
        return None, None, None
    
    artist = None
    title = None
    station_name = name_field if name_field and name_field != 'N/A' else None
    
    # Try 'Title by Artist - Station' format first (most specific)
    if ' by ' in title_field:
        parts = title_field.split(' by ', 1)
        if len(parts) == 2:
            title = parts[0].strip()
            rest = parts[1].strip()  # This is "Artist - Station" or just "Artist"
            
            # Check if rest contains " - " which would indicate station info
            for sep in [' - ', ' – ', ' — ']:
                if sep in rest:
                    artist_station = rest.split(sep, 1)
                    if len(artist_station) == 2:
                        artist = artist_station[0].strip()
                        station_part = artist_station[1].strip()
                        # Check if second part looks like a station
                        if has_station_indicators(station_part):
                            station_name = station_part
                            if title and artist:
                                return artist, title, station_name
                    break
            
            # No station found, just "Title by Artist"
            artist = rest
            if title and artist:
                return artist, title, station_name
    
    # Try 'Artist - Title' format (common separators)
    separators = [' - ', ' – ', ' — ', ' – ']
    for sep in separators:
        if sep in title_field:
            parts = title_field.split(sep, 1)
            if len(parts) == 2:
                artist = parts[0].strip()
                title = parts[1].strip()
                if artist and title:
                    return artist, title, station_name
    
    # If no pattern matched, return None (will use original values)
    return None, None, station_name

def connect_mpd_client():
    """Helper function to connect to MPD and return the client object."""
    client = MPDClient()
    client.timeout = 30  # Increased from 10 to 30 seconds for large queries
    client.idletimeout = None
    try:
        client.connect(MPD_HOST, MPD_PORT)
        return client
    except ConnectionError as e:
        print(f"Could not connect to MPD: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while connecting to MPD: {e}")
        return None

def get_mpd_status_for_display():
    """Fetches and returns the current MPD status and song info, formatted for display."""
    global last_mpd_status, auto_fill_last_artist, auto_fill_last_genre

    try:
        client = connect_mpd_client()
        if not client:
            status_info = {
                'state': 'disconnected', 
                'message': 'Could not connect to MPD.', 
                'volume': 0, 
                'queue_length': 0, 
                'consume_mode': False,
                'shuffle_mode': False,
                'crossfade_enabled': False,
                'crossfade_seconds': 0
            }
            if status_info != last_mpd_status:
                last_mpd_status = status_info
                return status_info
            return None
        
        status = client.status()
        current_song = client.currentsong()
        playlist_info = client.playlistinfo()

        # Get consume mode status from MPD
        consume_mode_status = status.get('consume', '0') == '1'
        # Get shuffle (random) mode status from MPD
        shuffle_mode_status = status.get('random', '0') == '1'
        # Get crossfade status from MPD
        crossfade_seconds = int(status.get('xfade', '0'))
        crossfade_enabled = crossfade_seconds > 0

        # Get song file path first (needed for format detection)
        song_file_path = current_song.get('file', '')

        # Parse audio format info (e.g., "44100:16:2" => samplerate:bitdepth:channels)
        bit_depth_val = None
        sample_rate_val = None
        try:
            audio_field = status.get('audio')
            if audio_field:
                parts = str(audio_field).split(':')
                if len(parts) >= 1 and parts[0].isdigit():
                    sample_rate_val = int(parts[0])
                if len(parts) >= 2 and parts[1].isdigit():
                    bit_depth_val = int(parts[1])
        except Exception:
            bit_depth_val = None
            sample_rate_val = None

        # Determine file format from file extension (FLAC, MP3, OGG, etc.)
        file_format = None
        try:
            if song_file_path:
                import os
                ext = os.path.splitext(song_file_path)[1].upper().lstrip('.')
                if ext:
                    file_format = ext
        except Exception:
            file_format = None

        client.disconnect()

        # Determine next song (Up Next) from playlist based on current position
        next_song_title = 'End of queue'
        next_song_artist = '—'
        try:
            current_index = int(status.get('song', -1))
            if current_index >= 0 and (current_index + 1) < len(playlist_info):
                next_song = playlist_info[current_index + 1]
                next_song_title = next_song.get('title') or next_song.get('file', 'Unknown Title')
                next_song_artist = next_song.get('artist', 'Unknown Artist')
        except (ValueError, TypeError):
            # Leave defaults if parsing fails
            pass
        
        # Parse volume safely
        volume_str = status.get('volume', '0')
        try:
            volume = int(volume_str)
        except ValueError:
            volume = 0

        # Convert elapsed and total time to float first, then to int for formatting
        elapsed_time_float = float(status.get('elapsed', '0.0'))
        total_time_float = float(current_song.get('time', '0.0'))
        
        elapsed_time_int = int(elapsed_time_float)
        total_time_int = int(total_time_float)

        formatted_elapsed = f"{elapsed_time_int // 60:02d}:{elapsed_time_int % 60:02d}"
        formatted_total = f"{total_time_int // 60:02d}:{total_time_int % 60:02d}"

        current_artist = current_song.get('artist', 'N/A')
        current_title = current_song.get('title', 'N/A')
        current_album = current_song.get('album', 'N/A')
        current_genre = current_song.get('genre', 'N/A')
        current_name = current_song.get('name', 'N/A')
        
        # Detect if this is a stream (URL instead of file path)
        is_stream = song_file_path and (song_file_path.startswith('http://') or song_file_path.startswith('https://'))
        
        # For streams with no duration, show "LIVE" instead of 00:00
        if is_stream and total_time_float == 0:
            formatted_total = "LIVE"
        
        # Try to parse stream metadata for better display
        if is_stream:
            # Check if artist field contains "Artist - Station" pattern
            if current_artist != 'N/A' and (' - ' in current_artist or ' – ' in current_artist):
                # Split on dash and check if second part looks like a station name
                for sep in [' - ', ' – ', ' — ']:
                    if sep in current_artist:
                        parts = current_artist.split(sep, 1)
                        if len(parts) == 2:
                            first_part = parts[0].strip()
                            second_part = parts[1].strip()
                            # If second part has station indicators, it's "Artist - Station" format
                            if has_station_indicators(second_part):
                                current_artist = first_part
                                current_album = second_part
                                print(f"[Stream] Extracted artist from field: {current_artist} (Station: {current_album})")
                                break
            # Try parsing artist field for "Title by Artist" pattern
            elif current_artist != 'N/A' and ' by ' in current_artist:
                parsed_artist, parsed_title, station_name = parse_stream_metadata(current_artist, current_title)
                if parsed_artist and parsed_title:
                    current_title = parsed_title
                    current_artist = parsed_artist
                    if station_name:
                        current_album = station_name
                    print(f"[Stream] Parsed from artist field: {current_artist} - {current_title} (Station: {current_album})")
            # Fallback: try parsing title field if artist is N/A
            elif current_artist == 'N/A' and current_title != 'N/A':
                parsed_artist, parsed_title, station_name = parse_stream_metadata(current_title, current_name)
                if parsed_artist and parsed_title:
                    current_artist = parsed_artist
                    current_title = parsed_title
                    if station_name:
                        current_album = station_name
                    print(f"[Stream] Parsed from title field: {current_artist} - {current_title} (Station: {current_album})")
            
            # Final fallback: if stream has NO metadata at all, use cached station name
            if (current_artist == 'N/A' and current_title == 'N/A' and 
                song_file_path in stream_name_cache):
                station_name = stream_name_cache[song_file_path]
                current_title = f"🔴 LIVE: {station_name}"
                current_album = station_name
                print(f"[Stream] No metadata - using cached station name: {station_name}")

        # Update last known artist/genre for auto-fill
        if current_artist != 'N/A':
            auto_fill_last_artist = current_artist
        if current_genre != 'N/A':
            auto_fill_last_genre = current_genre

        current_status_info = {
            'state': status.get('state', 'unknown'),
            'song_id': current_song.get('id'),
            'song_title': current_title,
            'artist': current_artist,
            'album': current_album,
            'album_artist': current_song.get('albumartist', current_artist),
            'genre': current_genre,
            'file_format': file_format,
            'bit_depth': bit_depth_val,
            'sample_rate': sample_rate_val,
            'volume': volume,
            'elapsed_time': formatted_elapsed,
            'total_time': formatted_total,
            'raw_elapsed_time': elapsed_time_float,
            'raw_total_time': total_time_float,
            'song_file': song_file_path,
            'file': song_file_path,
            'queue_length': len(playlist_info),
            'consume_mode': consume_mode_status,
            'shuffle_mode': shuffle_mode_status,
            'crossfade_enabled': crossfade_enabled,
            'crossfade_seconds': crossfade_seconds,
            'next_song_title': next_song_title,
            'next_song_artist': next_song_artist,
            'message': 'Connected to MPD successfully.'
        }
        
        # Only return if status has changed to avoid unnecessary emissions
        if current_status_info != last_mpd_status:
            last_mpd_status = current_status_info
            return current_status_info
        return None

    except socket.error as e:
        status_info = {
            'state': 'disconnected', 
            'message': f'Could not connect to MPD: {e}', 
            'volume': 0, 
            'queue_length': 0, 
            'consume_mode': False,
            'shuffle_mode': False,
            'crossfade_enabled': False,
            'crossfade_seconds': 0,
            'next_song_title': 'N/A',
            'next_song_artist': 'N/A'
        }
        if status_info != last_mpd_status:
            last_mpd_status = status_info
            return status_info
        return None
    except Exception as e:
        print(f"MPD error in get_mpd_status_for_display: {e}")
        status_info = {
            'state': 'error', 
            'message': f'MPD error: {e}', 
            'volume': 0, 
            'queue_length': 0, 
            'consume_mode': False,
            'shuffle_mode': False,
            'crossfade_enabled': False,
            'crossfade_seconds': 0,
            'next_song_title': 'N/A',
            'next_song_artist': 'N/A'
        }
        if status_info != last_mpd_status:
            last_mpd_status = status_info
            return status_info
        return None

def mpd_status_monitor():
    """Background task to poll MPD status and emit updates via SocketIO."""
    while True:
        status = get_mpd_status_for_display()
        if status:
            socketio.emit('mpd_status', status)
            
            # Add to play history when a new song starts playing
            global last_tracked_song_id, play_history
            current_song_id = status.get('song_id')
            if status.get('state') == 'play' and current_song_id and current_song_id != last_tracked_song_id:
                last_tracked_song_id = current_song_id
                history_item = {
                    'timestamp': time.time(),
                    'artist': status.get('artist', 'Unknown Artist'),
                    'title': status.get('song_title', 'Unknown Title'),
                    'album': status.get('album', 'Unknown Album'),
                    'file': status.get('song_file', ''),
                    'album_artist': status.get('album_artist', '')
                }
                # Add to beginning of list (most recent first)
                play_history.insert(0, history_item)
                # Keep only MAX_HISTORY_ITEMS
                if len(play_history) > MAX_HISTORY_ITEMS:
                    play_history = play_history[:MAX_HISTORY_ITEMS]
            
            # Scrobbling integration on track changes
            try:
                if scrobbling_enabled and status.get('state') == 'play':
                    global current_track_identity, current_track_start_ts, last_scrobbled_identity
                    identity = (
                        status.get('artist') or '',
                        status.get('song_title') or '',
                        status.get('album') or '',
                        status.get('song_file') or ''
                    )
                    # If identity changed, handle previous track scrobble and start new now playing
                    if current_track_identity != identity:
                        now_ts = int(time.time())
                        # Scrobble previous track if eligible
                        if current_track_identity and current_track_start_ts:
                            prev_artist, prev_title, prev_album, _ = current_track_identity
                            # Determine duration/elapsed
                            prev_elapsed = max(0, now_ts - int(current_track_start_ts))
                            prev_total = int(current_track_total_secs or 0)
                            # Scrobble rule: >= 50% or >= 240s
                            if prev_title and (prev_elapsed >= 240 or (prev_total and prev_elapsed >= prev_total/2)):
                                if last_scrobbled_identity != current_track_identity:
                                    lastfm_scrobble(prev_artist, prev_title, prev_album, int(current_track_start_ts), duration=prev_total or None)
                                    last_scrobbled_identity = current_track_identity
                        # Start tracking new track
                        current_track_identity = identity
                        current_track_start_ts = int(time.time())
                        # Send now playing (use total time from status)
                        total_seconds = int(status.get('raw_total_time') or 0)
                        current_track_total_secs = total_seconds
                        lastfm_update_now_playing(identity[0], identity[1], album=identity[2], duration=total_seconds or None)
                # If stopped/paused: attempt scrobble of current track if it just ended
                elif scrobbling_enabled and status.get('state') in ['stop', 'pause']:
                    if current_track_identity and current_track_start_ts:
                        now_ts = int(time.time())
                        prev_artist, prev_title, prev_album, _ = current_track_identity
                        prev_elapsed = max(0, now_ts - int(current_track_start_ts))
                        prev_total = int(current_track_total_secs or 0)
                        if prev_title and (prev_elapsed >= 240 or (prev_total and prev_elapsed >= prev_total/2)):
                            if last_scrobbled_identity != current_track_identity:
                                lastfm_scrobble(prev_artist, prev_title, prev_album, int(current_track_start_ts), duration=prev_total or None)
                                last_scrobbled_identity = current_track_identity
                        current_track_identity = None
                        current_track_start_ts = None
                        current_track_total_secs = None
            except Exception as e:
                print(f"[Last.fm] Error in scrobble monitor: {e}")
        time.sleep(1)  # Improved from 0.5 to 1 second for better performance

def auto_fill_monitor():
    """Background task to monitor playlist length and trigger auto-fill."""
    global auto_fill_active, auto_fill_min_queue_length, auto_fill_num_tracks_min, auto_fill_num_tracks_max, auto_fill_genre_filter_enabled, auto_fill_last_artist, auto_fill_last_genre, genre_station_mode, genre_station_name, genre_station_genres

    last_auto_fill_time = 0  # Track when we last triggered auto-fill
    auto_fill_cooldown = 30  # Cooldown period in seconds
    
    while True:
        if auto_fill_active:
            status_info = get_mpd_status_for_display()
            if status_info and status_info['state'] == 'play':
                current_queue_length = status_info.get('queue_length', 0)
                current_time = time.time()
                
                # Only trigger auto-fill if below threshold AND cooldown period has passed
                if (current_queue_length < auto_fill_min_queue_length and 
                    current_time - last_auto_fill_time > auto_fill_cooldown):
                    
                    print(f"Auto-fill triggered: Queue length ({current_queue_length}) below min ({auto_fill_min_queue_length}).")
                    num_tracks_to_add = random.randint(auto_fill_num_tracks_min, auto_fill_num_tracks_max)
                    last_auto_fill_time = current_time  # Update the last trigger time
                    
                    # Determine seed artist/genre for auto-fill
                    seed_artist = status_info.get('artist')
                    seed_genre = status_info.get('genre')

                    # Check if we're in genre station mode
                    if genre_station_mode and genre_station_genres:
                        socketio.emit('server_message', {
                            'type': 'info', 
                            'text': f'🎵 Genre Station Auto-fill: Adding {num_tracks_to_add} tracks from station "{genre_station_name}"...'
                        })
                        # Use genre station auto-fill function
                        socketio.start_background_task(
                            target=perform_genre_station_auto_fill,
                            genres=genre_station_genres,
                            num_tracks=num_tracks_to_add
                        )
                    else:
                        # Regular auto-fill mode using similar artists
                        # Fallback to last known if current is N/A
                        if seed_genre == 'N/A' and auto_fill_last_genre != 'N/A':
                            seed_genre = auto_fill_last_genre

                        # Always check for artist fallback
                        if seed_artist == 'N/A' and auto_fill_last_artist != 'N/A':
                            seed_artist = auto_fill_last_artist

                        if seed_artist == 'N/A':
                            socketio.emit('server_message', {
                                'type': 'warning', 
                                'text': 'Auto-fill: No current or last known artist to base suggestions on. Skipping auto-fill.'
                            })
                        else:
                            socketio.emit('server_message', {
                                'type': 'info', 
                                'text': f'Auto-filling {num_tracks_to_add} tracks (based on "{seed_artist}")...'
                            })
                            # Run the add tracks logic in a non-blocking way
                            socketio.start_background_task(
                                target=perform_add_random_tracks_logic,
                                artist_name_input=seed_artist,
                                num_tracks=num_tracks_to_add,
                                clear_playlist=False,
                                filter_by_genre=auto_fill_genre_filter_enabled,
                                seed_genre=seed_genre
                            )
                elif current_queue_length < auto_fill_min_queue_length:
                    # Still below threshold but in cooldown period
                    cooldown_remaining = int(auto_fill_cooldown - (current_time - last_auto_fill_time))
                    print(f"Auto-fill cooldown active. Queue length: {current_queue_length}, cooldown remaining: {cooldown_remaining}s")
                    
            elif status_info and status_info['state'] != 'play':
                print("Auto-fill active but MPD is not playing. Skipping check.")
        
        time.sleep(5)

def get_similar_artists_from_lastfm(artist_name, limit=10):
    """Fetches similar artists from Last.fm for a given artist."""
    if not LASTFM_API_KEY:
        print("Last.fm API key not set. Cannot fetch similar artists.")
        return []

    params = {
        'method': 'artist.getsimilar',
        'artist': artist_name,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': limit
    }
    try:
        response = requests.get(LASTFM_API_URL, params=params, timeout=5, headers=DEFAULT_HTTP_HEADERS)
        response.raise_for_status()
        data = response.json()
        
        similar_artists = []
        if 'similarartists' in data and 'artist' in data['similarartists']:
            for artist_data in data['similarartists']['artist']:
                similar_artists.append(artist_data.get('name'))
        return [a for a in similar_artists if a]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching similar artists from Last.fm: {e}")
        return []

def get_top_tracks_from_lastfm(artist_name, limit=5):
    """Fetches top tracks from Last.fm for a given artist."""
    if not LASTFM_API_KEY:
        print("Last.fm API key not set. Cannot fetch top tracks.")
        return []

    params = {
        'method': 'artist.gettoptracks',
        'artist': artist_name,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': limit
    }
    try:
        response = requests.get(LASTFM_API_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        tracks = []
        if 'toptracks' in data and 'track' in data['toptracks']:
            for track_data in data['toptracks']['track']:
                track_name = track_data.get('name')
                artist_name_from_api = track_data.get('artist', {}).get('name')
                if track_name and artist_name_from_api:
                    tracks.append({'artist': artist_name_from_api, 'title': track_name})
        return tracks
    except requests.exceptions.RequestException as e:
        print(f"Error fetching top tracks from Last.fm: {e}")
        return []

def get_top_albums_from_lastfm(artist_name, limit=3):
    """Fetches top albums from Last.fm for a given artist."""
    if not LASTFM_API_KEY:
        print("Last.fm API key not set. Cannot fetch top albums.")
        return []

    params = {
        'method': 'artist.gettopalbums',
        'artist': artist_name,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': limit
    }
    try:
        response = requests.get(LASTFM_API_URL, params=params, timeout=5, headers=DEFAULT_HTTP_HEADERS)
        response.raise_for_status()
        data = response.json()

        albums = []
        if 'topalbums' in data and 'album' in data['topalbums']:
            for album_data in data['topalbums']['album']:
                name = album_data.get('name')
                # Some entries may be "(null)" or empty from Last.fm – filter them out
                if name and name.lower() not in ['(null)', 'null', 'unknown']:
                    albums.append({'artist': artist_name, 'album': name})
        return albums
    except requests.exceptions.RequestException as e:
        print(f"Error fetching top albums from Last.fm: {e}")
        return []

def _add_album_songs_to_playlist_with_client(client, artist: str, album: str) -> int:
    """Add all songs for the given album using an existing MPD client; return count added."""
    added_count = 0
    try:
        # Prefer AlbumArtist first
        songs = []
        try:
            songs = client.find('albumartist', artist, 'album', album)
        except Exception as e:
            print(f"[DEBUG] AlbumArtist search failed for '{album}' by '{artist}': {e}")
            songs = []

        if not songs:
            try:
                songs = client.find('artist', artist, 'album', album)
            except Exception as e:
                print(f"[DEBUG] Artist search failed for '{album}' by '{artist}': {e}")
                songs = []

        for song in songs:
            file_path = song.get('file')
            if file_path:
                try:
                    client.add(file_path)
                    added_count += 1
                except CommandError as e:
                    print(f"MPD CommandError adding {file_path}: {e}")
                except Exception as e:
                    print(f"Error adding {file_path}: {e}")
    except Exception as e:
        print(f"Error while adding album '{album}' by '{artist}': {e}")
    return added_count

def _lastfm_sign(params: dict) -> str:
    """Create Last.fm API signature (MD5 of concatenated sorted params + shared secret)."""
    # Exclude 'format' and 'callback' and 'api_sig' from signature
    sign_items = [(k, v) for k, v in params.items() if k not in ['format', 'callback', 'api_sig']]
    sign_items.sort(key=lambda x: x[0])
    concat = ''.join([f"{k}{v}" for k, v in sign_items]) + LASTFM_SHARED_SECRET
    import hashlib
    return hashlib.md5(concat.encode('utf-8')).hexdigest()

def lastfm_api_post(method: str, extra_params: dict) -> dict:
    if not LASTFM_API_KEY or not LASTFM_SHARED_SECRET:
        raise RuntimeError('Last.fm API key/secret not set')
    params = { 'method': method, 'api_key': LASTFM_API_KEY }
    params.update(extra_params)
    params['api_sig'] = _lastfm_sign(params)
    params['format'] = 'json'
    r = requests.post(LASTFM_API_URL, data=params, timeout=8, headers=DEFAULT_HTTP_HEADERS)
    r.raise_for_status()
    data = r.json()
    # Check for Last.fm API errors in response
    if 'error' in data:
        error_code = data.get('error', 0)
        error_msg = data.get('message', 'Unknown error')
        raise RuntimeError(f'Last.fm API error {error_code}: {error_msg}')
    return data

def lastfm_request_token() -> str:
    data = lastfm_api_post('auth.getToken', {})
    token = data.get('token')
    if not token:
        raise RuntimeError('Failed to obtain Last.fm token')
    return token

def lastfm_get_session(token: str) -> str:
    data = lastfm_api_post('auth.getSession', {'token': token})
    sess = data.get('session', {})
    sk = sess.get('key')
    if not sk:
        raise RuntimeError('Failed to obtain Last.fm session key')
    return sk

def lastfm_update_now_playing(artist: str, track: str, album: str = '', duration: int = None):
    if not lastfm_session_key:
        return
    params = {
        'artist': artist or '',
        'track': track or '',
        'sk': lastfm_session_key
    }
    if album:
        params['album'] = album
    if isinstance(duration, (int, float)) and duration > 0:
        params['duration'] = int(duration)
    try:
        lastfm_api_post('track.updateNowPlaying', params)
        # Notify UI that Now Playing was sent (if enabled)
        if show_scrobble_toasts:
            try:
                socketio.emit('server_message', {
                    'type': 'info',
                    'text': f"Now Playing sent to Last.fm: {artist or 'Unknown Artist'} — {track or 'Unknown Title'}"
                })
            except Exception:
                # UI notification failures should not impact playback
                pass
    except Exception as e:
        print(f"[Last.fm] updateNowPlaying failed: {e}")

def lastfm_scrobble(artist: str, track: str, album: str, timestamp_unix: int, duration: int = None):
    if not lastfm_session_key:
        return
    # Use array-style parameters as recommended by Last.fm for scrobble batches
    params = {
        'artist[0]': artist or '',
        'track[0]': track or '',
        'timestamp[0]': int(timestamp_unix),
        'sk': lastfm_session_key
    }
    if album:
        params['album[0]'] = album
    if isinstance(duration, (int, float)) and duration > 0:
        params['duration[0]'] = int(duration)
    try:
        lastfm_api_post('track.scrobble', params)
        # Notify UI that a track was scrobbled (if enabled)
        if show_scrobble_toasts:
            try:
                parts = []
                if artist:
                    parts.append(artist)
                if track:
                    parts.append(track)
                label = ' — '.join(parts) if parts else 'Track scrobbled'
                socketio.emit('server_message', {
                    'type': 'success',
                    'text': f"Scrobbled: {label}"
                })
            except Exception:
                pass
    except Exception as e:
        print(f"[Last.fm] scrobble failed: {e}")

def lastfm_get_user_charts(chart_type: str, period: str = 'overall', limit: int = 50):
    """
    Fetch user charts from Last.fm (top artists, albums, or tracks).
    
    Args:
        chart_type: 'artists', 'albums', or 'tracks'
        period: '7day', '1month', '3month', '6month', '12month', 'overall'
        limit: number of items to return (max 50 for UI simplicity)
    
    Returns:
        List of dicts with name, playcount, and other metadata
    """
    if not lastfm_session_key:
        raise RuntimeError('Last.fm session key not set')
    
    # Map chart_type to Last.fm method
    method_map = {
        'artists': 'user.getTopArtists',
        'albums': 'user.getTopAlbums',
        'tracks': 'user.getTopTracks'
    }
    method = method_map.get(chart_type)
    if not method:
        raise ValueError(f"Invalid chart_type: {chart_type}")
    
    # Make API call (uses GET-style params but our helper does POST)
    params = {
        'sk': lastfm_session_key,
        'period': period,
        'limit': str(limit)
    }
    
    try:
        # For user methods, we need the username from session
        # But we can also use sk directly - Last.fm will infer user
        response = lastfm_api_post(method, params)
        
        # Parse response based on chart type
        if chart_type == 'artists':
            artists_data = response.get('topartists', {}).get('artist', [])
            return [{
                'name': item.get('name', 'Unknown'),
                'playcount': item.get('playcount', '0'),
                'url': item.get('url', '')
            } for item in artists_data]
        
        elif chart_type == 'albums':
            albums_data = response.get('topalbums', {}).get('album', [])
            return [{
                'name': item.get('name', 'Unknown Album'),
                'artist': item.get('artist', {}).get('name', 'Unknown Artist') if isinstance(item.get('artist'), dict) else item.get('artist', 'Unknown Artist'),
                'playcount': item.get('playcount', '0'),
                'url': item.get('url', '')
            } for item in albums_data]
        
        elif chart_type == 'tracks':
            tracks_data = response.get('toptracks', {}).get('track', [])
            return [{
                'name': item.get('name', 'Unknown Track'),
                'artist': item.get('artist', {}).get('name', 'Unknown Artist') if isinstance(item.get('artist'), dict) else item.get('artist', 'Unknown Artist'),
                'playcount': item.get('playcount', '0'),
                'url': item.get('url', '')
            } for item in tracks_data]
        
        return []
    except Exception as e:
        print(f"[Last.fm] Failed to fetch {chart_type} charts: {e}")
        raise

# --- Settings & Last.fm management ---
@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    global LASTFM_API_KEY, LASTFM_SHARED_SECRET, scrobbling_enabled, lastfm_session_key, show_scrobble_toasts
    current = load_settings()
    if request.method == 'POST':
        theme = request.form.get('theme', current.get('theme', 'dark')).strip() or 'dark'
        lastfm_key = request.form.get('lastfm_api_key', '').strip()
        lastfm_secret = request.form.get('lastfm_shared_secret', '').strip()
        scrobble_flag = request.form.get('enable_scrobbling') == 'on'
        show_toasts_flag = request.form.get('show_scrobble_toasts') == 'on'

        # Update in-memory and persisted settings. Environment variables still take precedence at runtime
        current['theme'] = theme
        current['enable_scrobbling'] = scrobble_flag
        scrobbling_enabled = scrobble_flag
        current['show_scrobble_toasts'] = show_toasts_flag
        show_scrobble_toasts = show_toasts_flag
        if lastfm_key:
            current['lastfm_api_key'] = lastfm_key
            # Update runtime value only if not set via environment
            if not os.environ.get('LASTFM_API_KEY'):
                LASTFM_API_KEY = lastfm_key
        if lastfm_secret:
            current['lastfm_shared_secret'] = lastfm_secret
            if not os.environ.get('LASTFM_SHARED_SECRET'):
                LASTFM_SHARED_SECRET = lastfm_secret

        if save_settings(current):
            app.config['THEME'] = theme
            flash('Settings saved successfully', 'success')
        else:
            flash('Failed to save settings', 'error')
        return redirect(url_for('settings_page'))

    # Mask secrets in UI
    masked_key = '•' * 10 if current.get('lastfm_api_key') else ''
    masked_secret = '•' * 10 if current.get('lastfm_shared_secret') else ''
    return render_template('settings.html',
                           theme=current.get('theme', 'dark'),
                           enable_scrobbling=bool(current.get('enable_scrobbling', False)),
                           lastfm_connected=bool(current.get('lastfm_session_key')),
                           show_scrobble_toasts=bool(current.get('show_scrobble_toasts', True)),
                           lastfm_api_key_masked=masked_key,
                           lastfm_shared_secret_masked=masked_secret)

@app.route('/api/test_lastfm', methods=['POST'])
def api_test_lastfm():
    key = request.form.get('api_key', '').strip() or LASTFM_API_KEY
    if not key:
        return jsonify({'status': 'error', 'message': 'No API key provided'}), 400
    try:
        params = {
            'method': 'artist.getsimilar',
            'artist': 'Metallica',
            'api_key': key,
            'format': 'json',
            'limit': 1
        }
        r = requests.get(LASTFM_API_URL, params=params, timeout=5, headers=DEFAULT_HTTP_HEADERS)
        r.raise_for_status()
        data = r.json()
        if 'similarartists' in data:
            return jsonify({'status': 'success', 'message': 'Last.fm API key appears valid.'})
        return jsonify({'status': 'error', 'message': 'Unexpected response from Last.fm.'}), 502
    except requests.exceptions.HTTPError as he:
        return jsonify({'status': 'error', 'message': f'HTTP error: {he}'}), 502
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error contacting Last.fm: {e}'}), 502

@app.route('/lastfm/request_token', methods=['POST'])
def lastfm_request_token_route():
    try:
        token = lastfm_request_token()
        s = load_settings()
        s['lastfm_auth_token'] = token
        save_settings(s)
        auth_url = f"{LASTFM_AUTH_URL}?api_key={LASTFM_API_KEY}&token={token}"
        return jsonify({'status': 'success', 'auth_url': auth_url})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/lastfm/finalize', methods=['POST'])
def lastfm_finalize_route():
    global lastfm_session_key
    try:
        s = load_settings()
        token = s.get('lastfm_auth_token', '')
        if not token:
            return jsonify({'status': 'error', 'message': 'No pending token. Request a token first.'}), 400
        sk = lastfm_get_session(token)
        s['lastfm_session_key'] = sk
        s['lastfm_auth_token'] = ''
        save_settings(s)
        lastfm_session_key = sk
        return jsonify({'status': 'success', 'message': 'Last.fm connected successfully.'})
    except Exception as e:
        print(f"[Last.fm] Finalize error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- Last.fm Charts API Endpoints ---
@app.route('/charts')
def charts_page():
    """Display the Last.fm charts page."""
    return render_template('charts.html')

@app.route('/api/charts/<chart_type>')
def api_charts(chart_type):
    """
    Return Last.fm user charts (artists, albums, or tracks).
    Query params: period (7day, 1month, 3month, 6month, 12month, overall)
    """
    if chart_type not in ['artists', 'albums', 'tracks']:
        return jsonify({'status': 'error', 'message': 'Invalid chart type'}), 400
    
    if not lastfm_session_key:
        return jsonify({'status': 'error', 'message': 'Last.fm not connected'}), 401
    
    period = request.args.get('period', 'overall')
    valid_periods = ['7day', '1month', '3month', '6month', '12month', 'overall']
    if period not in valid_periods:
        period = 'overall'
    
    try:
        data = lastfm_get_user_charts(chart_type, period=period, limit=50)
        return jsonify({
            'status': 'success',
            'chart_type': chart_type,
            'period': period,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        print(f"[Charts] Error fetching {chart_type}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def is_genre_match(target_genre, candidate_genre):
    """
    Compares two genre strings for a flexible match, considering sub-genres and base genres.
    Returns True if they are considered a match, False otherwise.
    """
    if not target_genre or not candidate_genre:
        return False
    
    target_genre_lower = target_genre.lower()
    candidate_genre_lower = candidate_genre.lower()

    # Case 1: Exact match
    if target_genre_lower == candidate_genre_lower:
        return True

    # Case 2: One genre string contains the other
    if target_genre_lower in candidate_genre_lower or candidate_genre_lower in target_genre_lower:
        return True

    # Case 3: Extract base genre and compare
    def get_base_genre(genre_str):
        if '(' in genre_str and ')' in genre_str:
            return genre_str.split('(')[0].strip().lower()
        return genre_str.lower()

    base_target = get_base_genre(target_genre)
    base_candidate = get_base_genre(candidate_genre)

    if base_target and base_candidate and base_target == base_candidate:
        return True

    return False

def perform_add_random_tracks_logic(artist_name_input, num_tracks, clear_playlist, filter_by_genre, seed_genre=None):
    """
    Centralized logic for adding random tracks, reusable by both manual and auto-fill.
    """
    print(f"Performing add random tracks logic: artist={artist_name_input}, num_tracks={num_tracks}, clear_playlist={clear_playlist}, filter_by_genre={filter_by_genre}, seed_genre={seed_genre}")

    if not artist_name_input:
        socketio.emit('server_message', {'type': 'error', 'text': 'Artist name is required for track addition logic.'})
        print("[DEBUG] Entered /api/album_tracks", flush=True)
        return

    try:
        client = connect_mpd_client()
        if not client:
            socketio.emit('server_message', {'type': 'error', 'text': 'Could not connect to MPD to add tracks.'})
            return

        current_genre_for_filter = seed_genre

        if filter_by_genre and (current_genre_for_filter == 'N/A' or not current_genre_for_filter):
            socketio.emit('server_message', {'type': 'warning', 'text': 'Genre filter requested, but no genre found for current song. Adding all genres.'})

        candidate_uris = []
        processed_lastfm_tracks = set()

        # Get top tracks for the initial artist from Last.fm
        top_tracks_initial_artist = get_top_tracks_from_lastfm(artist_name_input, limit=num_tracks)
        for track_info in top_tracks_initial_artist:
            track_key = (track_info['artist'], track_info['title'])
            if track_key not in processed_lastfm_tracks:
                processed_lastfm_tracks.add(track_key)
                # Search local MPD for this track
                mpd_search_results = client.search('artist', track_info['artist'], 'title', track_info['title'])
                if mpd_search_results:
                    for mpd_track in mpd_search_results:
                        file_path = mpd_track.get('file')
                        if file_path and file_path not in candidate_uris:
                            # Check genre if filtering is enabled
                            if filter_by_genre and current_genre_for_filter:
                                try:
                                    mpd_track_details = client.readcomments(file_path)
                                    mpd_track_genre = mpd_track_details.get('genre')
                                    if isinstance(mpd_track_genre, list):
                                        mpd_track_genre = mpd_track_genre[0] if mpd_track_genre else 'N/A'
                                    if is_genre_match(current_genre_for_filter, mpd_track_genre):
                                        candidate_uris.append(file_path)
                                    else:
                                        print(f"Skipped (genre mismatch): {track_info['artist']} - {track_info['title']} (MPD Genre: {mpd_track_genre}, Target: {current_genre_for_filter})")
                                except Exception as e:
                                    print(f"Error reading genre for {file_path}: {e}. Skipping genre check.")
                            else:
                                candidate_uris.append(file_path)
                else:
                    print(f"Last.fm suggested '{track_info['artist']} - {track_info['title']}', but not found in local MPD.")

        # Get similar artists and their top tracks
        similar_artists = get_similar_artists_from_lastfm(artist_name_input, limit=30)
        print(f"[AUTO-FILL DEBUG] Got {len(similar_artists)} similar artists from Last.fm for {artist_name_input}", flush=True)
        socketio.emit('server_message', {'type': 'info', 'text': f'Checking {len(similar_artists)} similar artists...'})
        for sim_artist in similar_artists:
            top_tracks_sim_artist = get_top_tracks_from_lastfm(sim_artist, limit=5)
            for track_info in top_tracks_sim_artist:
                track_key = (track_info['artist'], track_info['title'])
                if track_key not in processed_lastfm_tracks:
                    processed_lastfm_tracks.add(track_key)
                    mpd_search_results = client.search('artist', track_info['artist'], 'title', track_info['title'])
                    if mpd_search_results:
                        for mpd_track in mpd_search_results:
                            file_path = mpd_track.get('file')
                            if file_path and file_path not in candidate_uris:
                                if filter_by_genre and current_genre_for_filter:
                                    try:
                                        mpd_track_details = client.readcomments(file_path)
                                        mpd_track_genre = mpd_track_details.get('genre')
                                        if isinstance(mpd_track_genre, list):
                                            mpd_track_genre = mpd_track_genre[0] if mpd_track_genre else 'N/A'
                                        if is_genre_match(current_genre_for_filter, mpd_track_genre):
                                            candidate_uris.append(file_path)
                                        else:
                                            print(f"Skipped (genre mismatch): {track_info['artist']} - {track_info['title']} (MPD Genre: {mpd_track_genre}, Target: {current_genre_for_filter})")
                                    except Exception as e:
                                        print(f"Error reading genre for {file_path}: {e}. Skipping genre check.")
                                else:
                                    candidate_uris.append(file_path)
                    else:
                        print(f"Last.fm suggested '{track_info['artist']} - {track_info['title']}' from similar artist, but not found in local MPD.")

            # Fallback to broader local search for similar artist - collect 2-3 tracks from each
            if sim_artist:
                try:
                    mpd_all_artist_tracks = client.find('artist', sim_artist)
                    if mpd_all_artist_tracks:
                        print(f"[AUTO-FILL DEBUG] Found {len(mpd_all_artist_tracks)} tracks by {sim_artist}, adding up to 3...", flush=True)
                        random.shuffle(mpd_all_artist_tracks)
                        tracks_added_from_this_artist = 0
                        # Limit to 2-3 tracks per artist to ensure variety
                        max_tracks_per_artist = 3
                        for mpd_track in mpd_all_artist_tracks:
                            if tracks_added_from_this_artist >= max_tracks_per_artist:
                                break
                            file_path = mpd_track.get('file')
                            if file_path and file_path not in candidate_uris:
                                if filter_by_genre and current_genre_for_filter:
                                    try:
                                        mpd_track_details = client.readcomments(file_path)
                                        mpd_track_genre = mpd_track_details.get('genre')
                                        if isinstance(mpd_track_genre, list):
                                            mpd_track_genre = mpd_track_genre[0] if mpd_track_genre else 'N/A'
                                        if is_genre_match(current_genre_for_filter, mpd_track_genre):
                                            candidate_uris.append(file_path)
                                            tracks_added_from_this_artist += 1
                                    except Exception as e:
                                        print(f"Error reading genre for {file_path} in broader search: {e}. Skipping genre check.")
                                else:
                                    candidate_uris.append(file_path)
                                    tracks_added_from_this_artist += 1
                except CommandError as e:
                    print(f"MPD CommandError during broader search for artist {sim_artist}: {e}")
                except Exception as e:
                    print(f"Error during broader search for artist {sim_artist}: {e}")

        if not candidate_uris:
            socketio.emit('server_message', {'type': 'error', 'text': f'No local MPD tracks found matching Last.fm suggestions for "{artist_name_input}" or similar artists, with current filters.'})
            return

        print(f"[AUTO-FILL DEBUG] Collected {len(candidate_uris)} total candidate tracks from all similar artists", flush=True)
        socketio.emit('server_message', {'type': 'info', 'text': f'Collected {len(candidate_uris)} tracks, adding {num_tracks}...'})
        
        # Shuffle all collected and filtered tracks
        random.shuffle(candidate_uris)

        added_count = 0
        for mpd_uri in candidate_uris:
            if added_count >= num_tracks:
                break
            try:
                client.add(mpd_uri)
                added_count += 1
            except CommandError as e:
                print(f"MPD CommandError adding {mpd_uri} to queue: {e}")
            except Exception as e:
                print(f"Error adding {mpd_uri} to queue: {e}")

        client.disconnect()
        socketio.emit('server_message', {'type': 'info', 'text': f'Added {added_count} relevant tracks to playlist.'})
        # Trigger a status update after adding tracks
        socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))

    except Exception as e:
        print(f"Error during track addition logic: {e}")
        socketio.emit('server_message', {'type': 'error', 'text': f'Error adding tracks to MPD: {e}'})

def perform_genre_station_auto_fill(genres, num_tracks):
    """
    Radio station specific auto-fill function that adds tracks based on station genres.
    v3: Enhanced with batch processing for large genre lists (50+ genres) to prevent timeouts.
    """
    print(f"Performing genre station auto-fill v3: {len(genres)} genres, {num_tracks} tracks needed")
    
    try:
        candidate_uris = []
        batch_size = 15  # Process genres in batches to prevent timeouts
        target_candidates = num_tracks * 5  # Early stopping when we have 5x needed tracks
        
        # Process genres in batches
        for batch_start in range(0, len(genres), batch_size):
            batch_end = min(batch_start + batch_size, len(genres))
            batch_genres = genres[batch_start:batch_end]
            
            print(f"Processing genre batch {batch_start//batch_size + 1}: genres {batch_start+1}-{batch_end}")
            
            # Fresh MPD connection for each batch
            client = connect_mpd_client()
            if not client:
                socketio.emit('server_message', {
                    'type': 'error', 
                    'text': f'Could not connect to MPD for batch {batch_start//batch_size + 1}'
                })
                continue
            
            try:
                # Get songs from current batch of genres
                for genre in batch_genres:
                    try:
                        genre_songs = client.find('genre', genre)
                        print(f"  Genre '{genre}': {len(genre_songs)} songs")
                        
                        # Add all songs from this genre to candidates
                        for song in genre_songs:
                            file_path = song.get('file')
                            if file_path and file_path not in candidate_uris:
                                candidate_uris.append(file_path)
                                
                                # Early stopping if we have enough candidates
                                if len(candidate_uris) >= target_candidates:
                                    print(f"  Early stop: {len(candidate_uris)} candidates found")
                                    break
                        
                        # Break out of genre loop if we have enough
                        if len(candidate_uris) >= target_candidates:
                            break
                            
                    except Exception as e:
                        print(f"  Error fetching songs for genre '{genre}': {e}")
                        continue
                
                client.disconnect()
                
                # Early exit if we have enough candidates
                if len(candidate_uris) >= target_candidates:
                    print(f"Early stopping: {len(candidate_uris)} candidates sufficient")
                    break
                    
            except Exception as e:
                print(f"Error processing batch: {e}")
                client.disconnect()
                continue
        
        if not candidate_uris:
            socketio.emit('server_message', {
                'type': 'warning', 
                'text': f'No songs found for genre station genres (processed {len(genres)} genres)'
            })
            return
        
        print(f"Radio station auto-fill: {len(candidate_uris)} total candidates collected")
        
        # Randomly select tracks from candidates
        random.shuffle(candidate_uris)
        tracks_to_add = candidate_uris[:num_tracks]
        
        # Add selected tracks to playlist with fresh connection
        client = connect_mpd_client()
        if not client:
            socketio.emit('server_message', {
                'type': 'error', 
                'text': 'Could not connect to MPD for adding tracks'
            })
            return
        
        added_count = 0
        for track_uri in tracks_to_add:
            try:
                client.add(track_uri)
                added_count += 1
            except Exception as e:
                print(f"Error adding genre station track {track_uri}: {e}")
        
        client.disconnect()
        
        # Success message with genre count
        socketio.emit('server_message', {
            'type': 'success', 
            'text': f'🎵 Genre Station Auto-fill: Added {added_count} tracks from {len(genres)} genres'
        })
        
        # Trigger status update
        socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
        
    except Exception as e:
        print(f"Error during genre station auto-fill v3: {e}")
        socketio.emit('server_message', {
            'type': 'error', 
            'text': f'Radio station auto-fill error: {e}'
        })

# --- Web Routes ---

@app.route('/')
def index():
    mpd_info = get_mpd_status_for_display()
    if mpd_info is None:
        mpd_info = last_mpd_status if last_mpd_status else {
            'state': 'unknown', 
            'message': 'Loading...', 
            'volume': 0, 
            'queue_length': 0, 
            'consume_mode': False,
            'shuffle_mode': False,
            'crossfade_enabled': False,
            'crossfade_seconds': 0
        }

    album_art_url = url_for('get_album_art', 
                            song_file=mpd_info.get('song_file', ''),
                            artist=mpd_info.get('artist', ''),
                            album=mpd_info.get('album', ''))

    return render_template('index.html', 
                         mpd_info=mpd_info, 
                         album_art_url=album_art_url,
                         maestro_config_url=app.config.get('MAESTRO_CONFIG_URL', ''))

@app.route('/album_art_view')
def album_art_view():
    """Full-screen album art view page."""
    mpd_info = get_mpd_status_for_display()
    if mpd_info is None:
        mpd_info = last_mpd_status if last_mpd_status else {
            'state': 'unknown',
            'artist': 'Unknown Artist',
            'album': 'Unknown Album',
            'song_file': ''
        }
    
    album_art_url = url_for('get_album_art', 
                            song_file=mpd_info.get('song_file', ''),
                            artist=mpd_info.get('artist', ''),
                            album=mpd_info.get('album', ''),
                            prefer_lastfm='true')
    
    return render_template('album_art_view.html',
                         artist=mpd_info.get('artist', 'Unknown Artist'),
                         album=mpd_info.get('album', 'Unknown Album'),
                         album_art_url=album_art_url,
                         lastfm_configured=bool(LASTFM_API_KEY))

@app.route('/api/artist_images')
def get_artist_images():
    """Fetch album covers from local database first, then LastFM top albums for collage."""
    artist = request.args.get('artist', '')
    
    if not artist:
        return jsonify({'albums': []})
    
    try:
        albums = []
        
        # First, search local MPD database for albums by this artist
        client = connect_mpd_client()
        if client:
            try:
                # Search for albums containing the artist name (catches collaborations)
                all_albums = client.list('album', 'artist', artist)
                
                # Also search for albums where artist appears anywhere in the artist field
                # This catches "Artist1 & Artist2" type collaborations
                all_songs = client.search('artist', artist)
                
                # Collect unique album/artist combinations with file paths
                local_albums = {}
                
                # From song search - this gives us file paths
                for song in all_songs:
                    song_artist = song.get('artist', '')
                    song_album = song.get('album', '')
                    song_file = song.get('file', '')
                    if song_album and song_file:
                        key = f"{song_artist}|||{song_album}"
                        if key not in local_albums:
                            local_albums[key] = {
                                'artist': song_artist,
                                'album': song_album,
                                'local': True,
                                'file': song_file
                            }
                
                # Add local albums to results (randomized selection)
                import random
                local_albums_list = list(local_albums.values())
                random.shuffle(local_albums_list)  # Randomize so you see different albums each time
                albums.extend(local_albums_list[:8])  # Limit to 8
                print(f"Found {len(local_albums_list)} local albums for {artist}, showing 8 random ones")
                
                client.disconnect()
            except Exception as e:
                print(f"Error searching MPD for albums: {e}")
                if client:
                    client.disconnect()
        
        # If we don't have 8 albums yet, fill with albums from similar artists (that are in local library)
        if len(albums) < 8 and LASTFM_API_KEY:
            print(f"Only found {len(albums)} albums for {artist}, searching similar artists for more local content...")
            similar_artists = get_similar_artists_from_lastfm(artist, limit=20)
            
            if similar_artists:
                client = connect_mpd_client()
                if client:
                    try:
                        for sim_artist in similar_artists:
                            if len(albums) >= 8:
                                break
                            
                            # Search for albums by this similar artist in local library
                            sim_songs = client.search('artist', sim_artist)
                            sim_albums = {}
                            
                            for song in sim_songs:
                                song_artist = song.get('artist', '')
                                song_album = song.get('album', '')
                                song_file = song.get('file', '')
                                if song_album and song_file:
                                    key = f"{song_artist}|||{song_album}"
                                    if key not in sim_albums:
                                        sim_albums[key] = {
                                            'artist': song_artist,
                                            'album': song_album,
                                            'local': True,
                                            'file': song_file
                                        }
                            
                            if sim_albums:
                                # Add random albums from this similar artist
                                import random
                                sim_albums_list = list(sim_albums.values())
                                random.shuffle(sim_albums_list)
                                
                                # Add as many as we need (up to 8 total)
                                remaining_slots = 8 - len(albums)
                                albums.extend(sim_albums_list[:remaining_slots])
                                print(f"Added {min(len(sim_albums_list), remaining_slots)} albums from similar artist: {sim_artist}")
                        
                        client.disconnect()
                    except Exception as e:
                        print(f"Error searching similar artists in MPD: {e}")
                        if client:
                            client.disconnect()
        
        print(f"Returning {len(albums)} total local albums for album art grid")
