print("[DEBUG] app.py loaded and running", flush=True)

# Application version information
APP_VERSION = "3.3.0"
APP_BUILD_DATE = "2026-03-07" 
APP_NAME = "Maestro MPD Server"

# Simple threading mode to avoid eventlet issues
import os
os.environ["EVENTLET_THREADING"] = "1"

from flask import Flask, render_template, redirect, url_for, request, send_from_directory, Response, jsonify, flash, make_response
from flask_socketio import SocketIO, emit
from mpd import MPDClient, ConnectionError, CommandError
from typing import Optional
import socket
import subprocess
import os
import json
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import time
import requests
import random
import re
import html

# Import services
from services.mpd_service import MPDService
from services.bandcamp_service import BandcampService
from services.genius_service import GeniusService

# Import settings utilities
from utils.settings import (
    load_settings, save_settings,
    load_genre_stations, save_genre_stations,
    load_manual_stations, save_manual_stations,
    add_manual_station, remove_manual_station
)

# Import settings routes handlers
from routes.settings import settings_page_handler, settings_genius_page_handler

# Import playback routes handlers
from routes.playback import (
    play_handler, pause_handler, stop_handler,
    next_song_handler, previous_song_handler,
    seek_position_handler, set_volume_handler,
    restart_mpd_handler
)

# Import browse/search routes handlers
from routes.browse import (
    search_autocomplete_handler, search_handler,
    random_albums_handler,
    browse_genres_page_handler, browse_artists_page_handler, browse_albums_page_handler,
    api_browse_genres_handler, api_browse_artists_handler,
    api_browse_albums_handler, api_album_tracks_handler, recent_albums_page_handler
)

# Import playlist routes handlers
from routes.playlist import (
    add_album_to_playlist_handler, clear_and_add_album_handler,
    add_song_to_playlist_handler, playlist_page_handler,
    remove_from_playlist_handler, move_track_handler,
    clear_playlist_handler, save_playlist_handler,
    list_playlists_handler, load_playlist_handler,
    delete_playlist_handler, play_song_at_pos_handler,
    get_mpd_playlist_helper
)

# Import status/history routes handlers
from routes.status import (
    db_update_status_handler, get_mpd_status_handler,
    history_page_handler, get_history_handler,
    clear_history_handler
)

# Import radio routes handlers
from routes.radio import (
    get_genre_stations_handler, save_genre_station_handler,
    get_genre_station_handler, delete_genre_station_handler,
    set_genre_station_mode_handler, test_streaming_radio_handler,
    detect_radio_country_handler, get_radio_countries_handler,
    download_radio_backup_handler, get_backup_status_handler,
    get_radio_stations_handler, play_radio_station_handler,
    get_manual_stations_handler, save_manual_station_handler,
    remove_manual_station_handler
)

# Import integration routes handlers (Last.fm, Genius, Bandcamp, LMS)
from routes.integrations import (
    api_get_lyrics_handler, api_test_genius_handler,
    api_test_lastfm_handler, lastfm_request_token_handler,
    lastfm_finalize_handler, charts_page_handler, api_charts_handler,
    bandcamp_collection_handler, bandcamp_album_handler,
    bandcamp_add_track_handler, bandcamp_artwork_handler,
    api_lms_players_handler, api_lms_sync_handler,
    api_lms_unsync_handler, api_lms_status_handler,
    api_lms_volume_handler
)

# Import utility routes handlers
from routes.utilities import (
    get_version_info_handler, get_settings_info_handler,
    get_auto_fill_status_handler, toggle_auto_fill_handler,
    set_auto_fill_settings_handler, recent_albums_handler,
    list_music_directories_handler
)

# Import debug routes handlers
from routes.debug import (
    debug_albumartists_handler, debug_album_handler,
    debug_album_genre_handler, debug_album_search_handler,
    debug_genre_various_artists_handler
)

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
    def perform_search(client, search_tag, query, bandcamp_service=None):
        """Smart search function - groups by albums for artist/album searches"""
        try:
            import re
            
            if search_tag == 'any':
                results = client.search('any', query)
            else:
                results = client.search(search_tag, query)
            
            # Helper function to enrich metadata with Bandcamp info if available
            def enrich_with_bandcamp_metadata(metadata_dict, song_file):
                """Enrich metadata with cached Bandcamp data if available."""
                if not bandcamp_service or not bandcamp_service.is_enabled or not song_file:
                    return metadata_dict
                
                # Check if this is a Bandcamp stream
                if 'bandcamp.com' not in song_file:
                    return metadata_dict
                
                # Try to get cached metadata
                bc_meta = None
                
                # First try: direct URL lookup
                bc_meta = bandcamp_service.get_cached_metadata(song_file)
                
                # Second try: extract track_id from URL
                if not bc_meta and 'track_id=' in song_file:
                    track_id_match = re.search(r'track_id=(\d+)', song_file)
                    if track_id_match:
                        cache_key = f"track_{track_id_match.group(1)}"
                        bc_meta = bandcamp_service.get_cached_metadata(cache_key)
                
                # Apply metadata if found
                if bc_meta:
                    metadata_dict['artist'] = bc_meta.get('artist', metadata_dict.get('artist', 'Unknown Artist'))
                    metadata_dict['title'] = bc_meta.get('title', metadata_dict.get('title', 'Unknown Title'))
                    metadata_dict['album'] = bc_meta.get('album', metadata_dict.get('album', 'Unknown Album'))
                
                return metadata_dict
            
            # For artist or album searches, group by albums
            if search_tag in ['artist', 'album']:
                albums_dict = {}
                for song in results:
                    album_name = song.get('album', 'Unknown Album')
                    artist_name = song.get('artist', 'Unknown Artist')
                    song_file = song.get('file', '')
                    genre = song.get('genre', 'Unknown Genre')
                    
                    # Enrich with Bandcamp metadata if available
                    enriched = enrich_with_bandcamp_metadata({
                        'artist': artist_name,
                        'album': album_name,
                        'genre': genre
                    }, song_file)
                    artist_name = enriched['artist']
                    album_name = enriched['album']
                    
                    # Group by artist, album, AND directory to show each physical copy separately
                    album_dir = os.path.dirname(song_file) if song_file else ''
                    album_key = f"{artist_name}|||{album_name}|||{album_dir}"
                    
                    if album_key not in albums_dict:
                        albums_dict[album_key] = {
                            'item_type': 'album',
                            'artist': artist_name,
                            'album': album_name,
                            'genre': genre,
                            'track_count': 0,
                            'sample_file': song_file  # First song file for album art
                        }
                    albums_dict[album_key]['track_count'] += 1
                
                return list(albums_dict.values())
            
            # For title/any searches, return individual songs
            formatted_results = []
            for song in results:
                song_metadata = {
                    'item_type': 'song',
                    'artist': song.get('artist', 'Unknown Artist'),
                    'title': song.get('title', 'Unknown Title'),
                    'album': song.get('album', 'Unknown Album'),
                    'genre': song.get('genre', 'Unknown Genre'),
                    'file': song.get('file', ''),
                    'time': song.get('time', '0'),
                }
                
                # Enrich with Bandcamp metadata if available
                song_file = song.get('file', '')
                enriched = enrich_with_bandcamp_metadata(song_metadata, song_file)
                formatted_results.append(enriched)
            
            return formatted_results
        except Exception as e:
            print(f"Error in search: {e}")
            import traceback
            traceback.print_exc()
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
    GENIUS_CLIENT_ID = os.environ.get('GENIUS_CLIENT_ID', '')
    GENIUS_CLIENT_SECRET = os.environ.get('GENIUS_CLIENT_SECRET', '')
    GENIUS_ACCESS_TOKEN = os.environ.get('GENIUS_ACCESS_TOKEN', '')
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
    GENIUS_CLIENT_ID = ''  # Optional: Genius client id for lyrics lookup
    GENIUS_CLIENT_SECRET = ''  # Optional: Genius client secret for lyrics lookup
    GENIUS_ACCESS_TOKEN = ''  # Optional: Genius access token for lyrics lookup
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
if not GENIUS_CLIENT_ID:
    GENIUS_CLIENT_ID = _settings.get('genius_client_id', '')
if not GENIUS_CLIENT_SECRET:
    GENIUS_CLIENT_SECRET = _settings.get('genius_client_secret', '')
if not GENIUS_ACCESS_TOKEN:
    GENIUS_ACCESS_TOKEN = _settings.get('genius_access_token', '')
scrobbling_enabled = bool(_settings.get('enable_scrobbling', False))
lastfm_session_key = _settings.get('lastfm_session_key', '')
show_scrobble_toasts = bool(_settings.get('show_scrobble_toasts', True))

"""
Settings utilities imported from utils.settings module.
"""

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

# Initialize MPD Service with configuration
mpd_service = MPDService(host=MPD_HOST, port=MPD_PORT, timeout=30)

# Initialize Bandcamp Service with credentials from settings
bandcamp_service = BandcampService(
    username=_settings.get('bandcamp_username', ''),
    identity_token=_settings.get('bandcamp_identity_token', '')
)

# Initialize Genius Service for lyrics
genius_service = GeniusService()

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

# Rate limiting for album art requests to prevent client loops from overloading NFS
album_art_request_times = {}  # {(client_ip, cache_key): last_request_timestamp}
ALBUM_ART_RATE_LIMIT_SECONDS = 0  # Disabled - cache-busting timestamp prevents client loops

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

# --- API endpoint for application version info ---
@app.route('/api/version')
def get_version_info():
    app_ctx = {
        'APP_NAME': APP_NAME,
        'APP_VERSION': APP_VERSION,
        'APP_BUILD_DATE': APP_BUILD_DATE
    }
    return get_version_info_handler(app_ctx)

@app.route('/api/settings')
def get_settings_info():
    """Get public settings info (no sensitive data)"""
    app_ctx = {
        'load_settings': load_settings
    }
    return get_settings_info_handler(app_ctx)

# --- API endpoint for auto-fill status (for Add Music page) ---
@app.route('/get_auto_fill_status')
def get_auto_fill_status():
    app_ctx = {
        'auto_fill_active': auto_fill_active,
        'auto_fill_min_queue_length': auto_fill_min_queue_length,
        'auto_fill_num_tracks_min': auto_fill_num_tracks_min,
        'auto_fill_num_tracks_max': auto_fill_num_tracks_max,
        'auto_fill_genre_filter_enabled': auto_fill_genre_filter_enabled,
        'genre_station_mode': genre_station_mode,
        'genre_station_name': genre_station_name,
        'genre_station_genres': genre_station_genres
    }
    return get_auto_fill_status_handler(app_ctx)
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
    """
    Helper function to get MPD client connection.
    
    Create a FRESH client connection for each request to avoid socket buffer
    corruption from concurrent requests. Callers are responsible for closing.
    
    Returns:
        MPDClient: Fresh connected MPD client instance, or None if connection failed
    """
    try:
        client = MPDClient()
        client.timeout = 30
        client.connect(MPD_HOST, MPD_PORT)
        return client
    except Exception as e:
        print(f"[CRITICAL] Failed to create fresh MPD connection: {e}", flush=True)
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
            
            # Check for cached Bandcamp metadata (match by track_id or streaming URL)
            import re
            bc_meta = None
            
            # Try multiple lookup methods
            if song_file_path and 'bandcamp.com' in song_file_path:
                # First try: direct URL lookup (fastest)
                if song_file_path in bandcamp_metadata_cache:
                    bc_meta = bandcamp_metadata_cache[song_file_path]
                    print(f"[Bandcamp] Found metadata by URL: {song_file_path}", flush=True)
                # Second try: extract track_id from URL and look up by track_id key
                elif 'track_id=' in song_file_path:
                    track_id_match = re.search(r'track_id=(\d+)', song_file_path)
                    if track_id_match:
                        cache_key = f"track_{track_id_match.group(1)}"
                        bc_meta = bandcamp_metadata_cache.get(cache_key)
                        if bc_meta:
                            print(f"[Bandcamp] Found metadata by track_id: {cache_key}", flush=True)
            
            if bc_meta:
                current_artist = bc_meta.get('artist', current_artist)
                current_title = bc_meta.get('title', current_title)
                current_album = bc_meta.get('album', current_album)
                current_album = bc_meta.get('album', current_album)
                print(f"[Bandcamp] Using cached metadata: {current_artist} - {current_title}", flush=True)
            # Final fallback: if stream has NO metadata at all, use cached station name
            elif (current_artist == 'N/A' and current_title == 'N/A' and 
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

        # Find favicon for the currently playing stream (if it's a stream)
        stream_favicon = None
        if is_stream:
            # First check the in-memory cache (favicon sent when stream was played)
            if song_file_path in stream_favicon_cache:
                stream_favicon = stream_favicon_cache[song_file_path]
                print(f"[Stream] Found favicon in cache: {stream_favicon}")
            # Then check manual stations
            elif not stream_favicon:
                manual_stations = load_manual_stations()
                for station in manual_stations:
                    if station.get('url') == song_file_path and station.get('favicon'):
                        stream_favicon = station.get('favicon')
                        break
            
            # If still not found, check preset stations
            if not stream_favicon:
                try:
                    with open(GENRE_STATIONS_FILE, 'r') as f:
                        genre_stations = json.load(f)
                        # genre_stations is a dict of genres, not stations
                        # Skip this for now since it doesn't contain station URLs
                except Exception:
                    pass

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
            'is_stream': is_stream,
            'stream_favicon': stream_favicon,
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

        # If still no results, try fuzzy matching on album names
        if not songs:
            try:
                # Get all albums by this artist and find similar ones
                all_albums_by_artist = client.find('albumartist', artist)
                if not all_albums_by_artist:
                    all_albums_by_artist = client.find('artist', artist)
                
                # Build set of unique album names
                available_albums = set()
                for song in all_albums_by_artist:
                    if song.get('album'):
                        available_albums.add(song.get('album'))
                
                # Try to find a fuzzy match
                album_lower = album.lower().strip()
                matching_album = None
                
                for avail_album in available_albums:
                    avail_lower = avail_album.lower().strip()
                    # Check if Last.fm album name is a substring or vice versa, or if base names match
                    if (album_lower in avail_lower or avail_lower in album_lower or
                        avail_lower.split('(')[0].strip() == album_lower.split('(')[0].strip()):
                        matching_album = avail_album
                        print(f"[DEBUG] Fuzzy matched '{album}' → '{matching_album}'")
                        break
                
                # If found a fuzzy match, search for it
                if matching_album:
                    try:
                        songs = client.find('albumartist', artist, 'album', matching_album)
                        if not songs:
                            songs = client.find('artist', artist, 'album', matching_album)
                        print(f"[DEBUG] Fuzzy search found {len(songs)} songs in '{matching_album}'")
                    except Exception as e:
                        print(f"[DEBUG] Fuzzy match search failed: {e}")
                        songs = []
            except Exception as e:
                print(f"[DEBUG] Fuzzy album search failed: {e}")

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
    """Route handler for /settings - delegates to routes.settings module"""
    app_ctx = {
        'app': app,
        'globals': globals()
    }
    return settings_page_handler(app_ctx)


@app.route('/settings/genius', methods=['POST'])
def settings_genius_page():
    """Route handler for /settings/genius - delegates to routes.settings module"""
    app_ctx = {
        'app': app,
        'globals': globals()
    }
    return settings_genius_page_handler(app_ctx)

@app.route('/api/lyrics', methods=['POST'])
def api_get_lyrics():
    """Get lyrics for a track."""
    app_ctx = {
        'genius_service': genius_service
    }
    return api_get_lyrics_handler(app_ctx)

def _is_likely_instrumental(title: str) -> bool:
    """
    Check if track title suggests it's instrumental
    """
    instrumental_keywords = [
        'instrumental',
        'theme',
        'interlude',
        'intro',
        'outro',
        'remix',
        'version',
        'medley',
        'suite',
        'concerto',
        'symphony',
        'sonata',
        'prelude',
        'etude',
        'fugue',
        'nocturne',
    ]
    
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in instrumental_keywords)

def _try_lyrics_providers(artist: str, title: str) -> Optional[str]:
    """
    Try to fetch lyrics from available providers
    Currently uses Genius web search + page scrape (no JS required).
    """
    try:
        lyrics = _fetch_lyrics_genius(artist, title)
        if lyrics:
            return lyrics
        return None
    except Exception as e:
        print(f"Lyrics provider error: {e}")
        return None

def _fetch_lyrics_genius(artist: str, title: str) -> Optional[str]:
    """Search Genius and scrape lyrics from the first matching song page."""
    try:
        query = f"{artist} {title}".strip()
        if not query:
            return None

        search_url = "https://genius.com/api/search/song"
        params = {'q': query}
        resp = requests.get(search_url, params=params, timeout=8, headers=DEFAULT_HTTP_HEADERS)
        resp.raise_for_status()
        data = resp.json()
        sections = data.get('response', {}).get('sections', [])
        song_section = next((s for s in sections if s.get('type') == 'song'), None)
        hits = song_section.get('hits', []) if song_section else []

        for hit in hits:
            result = hit.get('result', {})
            url = result.get('url') or ''
            if not url:
                continue
            lyrics = _scrape_genius_page(url)
            if lyrics:
                return lyrics
        return None
    except Exception as e:
        print(f"[Genius] search error: {e}")
        return None

def _scrape_genius_page(url: str) -> Optional[str]:
    """Scrape lyrics text from a Genius song page using BeautifulSoup for robustness."""
    try:
        from bs4 import BeautifulSoup
        
        resp = requests.get(url, timeout=8, headers=DEFAULT_HTTP_HEADERS)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Find all containers with data-lyrics-container="true"
        containers = soup.find_all('div', {'data-lyrics-container': 'true'})
        if not containers:
            print(f"[Genius] No lyrics containers found on {url}")
            return None

        parts = []
        for container in containers:
            # Extract all text from container, preserving line breaks
            text_parts = []
            for element in container.descendants:
                if isinstance(element, str):
                    text = element.strip()
                    if text:
                        text_parts.append(text)
                elif element.name == 'br':
                    text_parts.append('\n')
            
            # Join and clean up
            block_text = ''.join(text_parts)
            block_text = re.sub(r'\n{3,}', '\n\n', block_text).strip()
            
            if block_text:
                parts.append(block_text)

        if not parts:
            print(f"[Genius] No lyric text extracted from {url}")
            return None

        lyrics = "\n\n".join(parts)
        
        # Clean up common metadata junk
        lyrics = _clean_genius_lyrics(lyrics)
        
        # Final cleanup: collapse excess blank lines
        lyrics = re.sub(r'\n{3,}', '\n\n', lyrics).strip()
        
        if not lyrics:
            return None
            
        print(f"[Genius] Successfully scraped {len(lyrics)} chars from {url}")
        return lyrics
    except ImportError:
        print("[Genius] BeautifulSoup not installed, falling back to regex parsing")
        return _scrape_genius_page_regex(url)
    except Exception as e:
        print(f"[Genius] scrape error: {e}")
        return None

def _clean_genius_lyrics(lyrics: str) -> Optional[str]:
    """
    Remove common metadata junk from Genius lyrics.
    Strips contributor info, translations, descriptions, etc.
    Keep all actual lyrics including verses 1, 2, 3...
    """
    lines = lyrics.split('\n')
    cleaned_lines = []
    
    # Patterns to completely remove lines
    junk_patterns = [
        r'^\d+\s+Contributors?$',        # "71 Contributors"
        r'^Translations?$',               # "Translations"
        r'^(Español|Italiano|Português|Français|Deutsch|中文|日本語)$',  # Language names
        r'^(Read More|See full lyrics|Get the lyrics|Lyrics)$',          # Common metadata
        r'^\[.*?\]\s*Lyrics.*$',          # "[Song Name] Lyrics"
    ]
    
    for line in lines:
        line_stripped = line.strip()
        
        # Check if this line is pure junk to skip
        is_junk = any(re.match(pattern, line_stripped) for pattern in junk_patterns)
        
        # Also skip lines that look like Genius descriptions (long text between metadata and [Verse)
        # Only if they don't contain typical lyric markers
        is_long_description = (len(line_stripped) > 100 and 
                              not re.match(r'^\[', line_stripped) and
                              'believe' not in line_stripped.lower() and
                              'dream' not in line_stripped.lower())
        
        if not is_junk and not is_long_description:
            cleaned_lines.append(line)

    # Join and clean up excess blank lines
    result = '\n'.join(cleaned_lines).strip()
    result = re.sub(r'\n{3,}', '\n\n', result).strip()
    
    return result if result else None

def _scrape_genius_page_regex(url: str) -> Optional[str]:
    """Fallback regex-based scraper if BeautifulSoup unavailable."""
    try:
        resp = requests.get(url, timeout=8, headers=DEFAULT_HTTP_HEADERS)
        resp.raise_for_status()
        html_text = resp.text

        # Try to find lyrics containers more carefully
        # Match opening div with data-lyrics-container, then all content until matching close
        pattern = r'<div[^>]*data-lyrics-container="true"[^>]*>(.*?)</div(?=>)'
        containers = re.findall(pattern, html_text, flags=re.DOTALL)
        
        if not containers:
            return None

        parts = []
        for block in containers:
            block = block.replace('<br/>', '\n').replace('<br>', '\n')
            block = re.sub(r'<[^>]+>', '', block)
            block = html.unescape(block)
            block = block.strip()
            if block:
                parts.append(block)

        if not parts:
            return None

        lyrics = "\n\n".join(parts)
        lyrics = re.sub(r'\n{3,}', '\n\n', lyrics).strip()
        return lyrics or None
    except Exception as e:
        print(f"[Genius] regex scrape error: {e}")
        return None

@app.route('/api/test_genius', methods=['POST'])
def api_test_genius():
    """Test Genius API connectivity."""
    app_ctx = {'genius_service': genius_service}
    return api_test_genius_handler(app_ctx)


@app.route('/api/test_lastfm', methods=['POST'])
def api_test_lastfm():
    """Test Last.fm API connectivity."""
    app_ctx = {
        'load_settings': load_settings,
        'LASTFM_API_KEY': LASTFM_API_KEY,
        'LASTFM_API_URL': LASTFM_API_URL,
        'DEFAULT_HTTP_HEADERS': DEFAULT_HTTP_HEADERS
    }
    return api_test_lastfm_handler(app_ctx)

@app.route('/lastfm/request_token', methods=['POST'])
def lastfm_request_token_route():
    """Get Last.fm request token for OAuth."""
    app_ctx = {
        'lastfm_request_token': lastfm_request_token,
        'load_settings': load_settings,
        'save_settings': save_settings,
        'LASTFM_API_KEY': LASTFM_API_KEY,
        'LASTFM_AUTH_URL': LASTFM_AUTH_URL
    }
    return lastfm_request_token_handler(app_ctx)

@app.route('/lastfm/finalize', methods=['POST'])
def lastfm_finalize_route():
    """Finalize Last.fm OAuth and get session key."""
    app_ctx = {
        'lastfm_get_session': lastfm_get_session,
        'save_settings': save_settings,
        'load_settings': load_settings
    }
    return lastfm_finalize_handler(app_ctx)

# --- Last.fm Charts API Endpoints ---
@app.route('/charts')
def charts_page():
    """Display user's Last.fm charts."""
    app_ctx = {}
    return charts_page_handler(app_ctx)

@app.route('/api/charts/<chart_type>')
def api_charts(chart_type):
    """Get user's Last.fm charts (artists, albums, or tracks)."""
    app_ctx = {
        'load_settings': load_settings,
        'lastfm_get_user_charts': lastfm_get_user_charts,
        'lastfm_session_key': lastfm_session_key,
        'LASTFM_API_KEY': LASTFM_API_KEY
    }
    return api_charts_handler(app_ctx, chart_type)

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

    # Generate album art URL with cache-busting timestamp to prevent browser cache issues
    # Include title parameter for better Last.fm stream matching (same as socket.io updates)
    # Guard against N/A placeholder values - don't generate URL if song data is incomplete
    if (mpd_info.get('song_file') and mpd_info.get('song_file') != 'N/A' and 
        mpd_info.get('artist') and mpd_info.get('artist') != 'N/A' and 
        mpd_info.get('album') and mpd_info.get('album') != 'N/A'):
        album_art_url = url_for('get_album_art', 
                                song_file=mpd_info.get('song_file', ''),
                                artist=mpd_info.get('artist', ''),
                                album=mpd_info.get('album', ''),
                                title=mpd_info.get('song_title', ''),
                                _t=int(time.time() * 1000))  # Cache-busting timestamp in milliseconds
    else:
        # For placeholder songs or disconnected state, use static placeholder
        album_art_url = url_for('static_placeholder_art')

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
    
    # Generate album art URL with cache-busting timestamp
    album_art_url = url_for('get_album_art', 
                            song_file=mpd_info.get('song_file', ''),
                            artist=mpd_info.get('artist', ''),
                            album=mpd_info.get('album', ''),
                            prefer_lastfm='true',
                            _t=int(time.time() * 1000))  # Cache-busting timestamp in milliseconds
    
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
                print(f"Found {len(local_albums_list)} local albums for {artist}, showing {min(8, len(albums))} random ones")
                
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
        
        return jsonify({'albums': albums})
    except Exception as e:
        print(f"Error in artist_images: {e}")
        return jsonify({'albums': []})

@app.route('/api/search/autocomplete')
def search_autocomplete_data():
    """Return all artists, albums, and titles for client-side autocomplete."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client
    }
    return search_autocomplete_handler(app_ctx)

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search page with improved functionality from beta version."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'perform_search': perform_search
    }
    return search_handler(app_ctx)

@app.route('/random_albums', methods=['GET'])
def random_albums():
    """Return 25 random albums from the library."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client
    }
    return random_albums_handler(app_ctx)

@app.route('/play', methods=['GET', 'POST'])
def play():
    """Route handler for /play - delegates to routes.playback module"""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
    }
    return play_handler(app_ctx)


@app.route('/pause', methods=['GET', 'POST'])
def pause():
    """Route handler for /pause - delegates to routes.playback module"""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
    }
    return pause_handler(app_ctx)


@app.route('/stop', methods=['GET', 'POST'])
def stop():
    """Route handler for /stop - delegates to routes.playback module"""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
    }
    return stop_handler(app_ctx)


@app.route('/next', methods=['GET', 'POST'])
def next_song():
    """Route handler for /next - delegates to routes.playback module"""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
    }
    return next_song_handler(app_ctx)


@app.route('/previous', methods=['GET', 'POST'])
def previous_song():
    """Route handler for /previous - delegates to routes.playback module"""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
    }
    return previous_song_handler(app_ctx)


@app.route('/seek', methods=['POST'])
def seek_position():
    """Route handler for /seek - delegates to routes.playback module"""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
    }
    return seek_position_handler(app_ctx)


@app.route('/set_volume', methods=['POST'])
def set_volume():
    """Route handler for /set_volume - delegates to routes.playback module"""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'socketio': socketio,
        'get_mpd_status_for_display': get_mpd_status_for_display
    }
    return set_volume_handler(app_ctx)


@app.route('/restart_mpd')
def restart_mpd():
    """Route handler for /restart_mpd - delegates to routes.playback module"""
    app_ctx = {
        'socketio': socketio,
        'get_mpd_status_for_display': get_mpd_status_for_display
    }
    return restart_mpd_handler(app_ctx)

@app.route('/update_mpd_db')
def update_mpd_db():
    try:
        client = connect_mpd_client()
        if client:
            # Send update command to MPD
            update_job = client.update()
            client.disconnect()
            
            print(f"MPD database update started. Job ID: {update_job}")
            
            # Emit success message
            socketio.emit('server_message', {'type': 'success', 'text': 'MPD database update started successfully'})
            
            # Wait a moment and then trigger status update
            socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
            
            return redirect(url_for('index'))
        else:
            error_msg = "Could not connect to MPD to update database"
            print(error_msg)
            socketio.emit('server_message', {'type': 'error', 'text': error_msg})
            return redirect(url_for('index'))
            
    except Exception as e:
        error_msg = f"Error updating MPD database: {str(e)}"
        print(error_msg)
        socketio.emit('server_message', {'type': 'error', 'text': error_msg})
        return redirect(url_for('index'))

@app.route('/api/db_update_status')
def db_update_status():
    """Check if MPD database update is in progress."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client
    }
    return db_update_status_handler(app_ctx)

@app.route('/add_music')
def add_music_page():
    """Add music page."""
    mpd_info = get_mpd_status_for_display()
    current_artist = mpd_info.get('artist', '') if mpd_info else ''
    current_genre = mpd_info.get('genre', '') if mpd_info else ''
    return render_template('add_music.html', current_artist=current_artist, current_genre=current_genre)

@app.route('/add_random_tracks', methods=['POST'])
def add_random_tracks_manual():
    """Handle manual adding of random tracks."""
    global genre_station_mode, genre_station_name, genre_station_genres
    
    artist_name_input = request.form.get('artist_name')
    num_tracks = request.form.get('num_tracks', type=int, default=5)
    clear_playlist = request.form.get('clear_playlist') == 'true'
    filter_by_genre = request.form.get('filter_by_genre') == 'true'

    # Clear genre station mode when manually adding tracks
    genre_station_mode = False
    genre_station_name = ""
    genre_station_genres = []
    print("Genre station mode cleared due to manual track addition")

    # Use current playing genre as seed for manual add
    mpd_status = get_mpd_status_for_display()
    seed_genre = mpd_status.get('genre') if mpd_status else 'N/A'

    socketio.emit('server_message', {'type': 'info', 'text': f'Manually searching Last.fm for similar artists and tracks for {artist_name_input}...'})
    
    # Run the logic in a background task to avoid blocking the Flask route
    socketio.start_background_task(
        target=perform_add_random_tracks_logic,
        artist_name_input=artist_name_input,
        num_tracks=num_tracks,
        clear_playlist=clear_playlist,
        filter_by_genre=filter_by_genre,
        seed_genre=seed_genre
    )
    
    return ('', 204)

@app.route('/api/genres', methods=['GET'])
def get_genres():
    """Get all available genres from MPD."""
    try:
        client = connect_mpd_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
        
        try:
            genres = client.list('genre')
            client.disconnect()
            
            # Extract genre names from the dictionaries and filter out empty/invalid genres
            genre_names = [item.get('genre', '') for item in genres if isinstance(item, dict)]
            valid_genres = [g for g in genre_names if g and g.strip() and g.strip() != 'N/A']
            valid_genres.sort(key=str.lower)  # Case-insensitive sort
            
            return jsonify(valid_genres)
        except Exception as e:
            client.disconnect()
            return jsonify({'status': 'error', 'message': f'MPD error: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/genre_stations', methods=['GET'])
def get_genre_stations():
    """Get all saved genre stations."""
    app_ctx = {
        'load_genre_stations': load_genre_stations
    }
    return get_genre_stations_handler(app_ctx)

@app.route('/api/genre_stations', methods=['POST'])
def save_genre_station():
    """Save a new genre station."""
    app_ctx = {
        'load_genre_stations': load_genre_stations,
        'save_genre_stations': save_genre_stations
    }
    return save_genre_station_handler(app_ctx)

@app.route('/api/genre_stations/<station_name>', methods=['GET'])
def get_genre_station(station_name):
    """Get a specific genre station."""
    app_ctx = {
        'load_genre_stations': load_genre_stations
    }
    return get_genre_station_handler(app_ctx, station_name)

@app.route('/api/genre_stations/<station_name>', methods=['DELETE'])
def delete_genre_station(station_name):
    """Delete a genre station."""
    app_ctx = {
        'load_genre_stations': load_genre_stations,
        'save_genre_stations': save_genre_stations
    }
    return delete_genre_station_handler(app_ctx, station_name)

@app.route('/api/genre_station_mode', methods=['POST'])
def set_genre_station_mode():
    """Set genre station mode for auto-fill."""
    global genre_station_mode, genre_station_name, genre_station_genres
    
    app_ctx = {}
    result = set_genre_station_mode_handler(app_ctx)
    
    # Parse response and update globals
    import json
    if hasattr(result, 'get_json'):
        data = result.get_json()
        if data.get('action') == 'set_mode':
            genre_station_mode = True
            genre_station_name = data.get('station_name', '')
            genre_station_genres = data.get('genres', [])
            print(f"Genre station mode activated: '{genre_station_name}' with genres {genre_station_genres}")
        else:
            genre_station_mode = False
            genre_station_name = ""
            genre_station_genres = []
            print("Genre station mode deactivated")
    
    return result

@app.route('/api/streaming_radio/test', methods=['POST'])
def test_streaming_radio():
    """Test internet radio streaming."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'socketio': socketio,
        'get_mpd_status_for_display': get_mpd_status_for_display
    }
    return test_streaming_radio_handler(app_ctx)

# --- Radio Browser API Integration ---
@app.route('/api/radio/detect-country', methods=['GET'])
def detect_radio_country():
    """Detect user's country from IP address."""
    app_ctx = {}
    return detect_radio_country_handler(app_ctx)

@app.route('/api/radio/countries', methods=['GET'])
def get_radio_countries():
    """Get list of countries with radio stations."""
    app_ctx = {}
    return get_radio_countries_handler(app_ctx)

# Simple cache for radio stations (country/search -> stations, timestamp)
radio_stations_cache = {}
CACHE_DURATION = 600  # In-memory cache for 10 minutes
PERSISTENT_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache', 'radio')
PERSISTENT_CACHE_DURATION = 7 * 24 * 60 * 60  # File cache for 7 days
BACKUP_DB_FILE = os.path.join(PERSISTENT_CACHE_DIR, 'radio_backup.json.gz')
BACKUP_DB_URL = 'https://backups.radio-browser.info/radiobrowser_stations_latest.json.gz'

# Ensure cache directory exists
os.makedirs(PERSISTENT_CACHE_DIR, exist_ok=True)

def get_cache_filename(cache_key):
    """Generate safe filename for cache key."""
    import hashlib
    safe_key = hashlib.md5(cache_key.encode()).hexdigest()
    return os.path.join(PERSISTENT_CACHE_DIR, f"stations_{safe_key}.json")

def load_from_persistent_cache(cache_key):
    """Load stations from disk cache if available and not stale."""
    try:
        cache_file = get_cache_filename(cache_key)
        if os.path.exists(cache_file):
            import time
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < PERSISTENT_CACHE_DURATION:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"Loaded stations from persistent cache (age: {file_age/3600:.1f} hours)")
                    return data
            else:
                print(f"Persistent cache expired (age: {file_age/86400:.1f} days)")
    except Exception as e:
        print(f"Error loading persistent cache: {e}")
    return None

def save_to_persistent_cache(cache_key, data):
    """Save stations to disk cache."""
    try:
        cache_file = get_cache_filename(cache_key)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(data)} stations to persistent cache")
    except Exception as e:
        print(f"Error saving persistent cache: {e}")

def load_backup_database():
    """Load stations from the backup database file."""
    try:
        if not os.path.exists(BACKUP_DB_FILE):
            print("No backup database file found")
            return None
        
        import gzip
        import time
        
        # Check file age
        file_age_days = (time.time() - os.path.getmtime(BACKUP_DB_FILE)) / 86400
        print(f"Loading backup database (age: {file_age_days:.1f} days)")
        
        with gzip.open(BACKUP_DB_FILE, 'rt', encoding='utf-8') as f:
            stations = json.load(f)
            print(f"Loaded {len(stations)} stations from backup database")
            return stations
    except Exception as e:
        print(f"Error loading backup database: {e}")
        return None

def filter_backup_stations(stations, country=None, name_search=None, limit=50):
    """Filter stations from backup database by country/name."""
    try:
        filtered = []
        
        for station in stations:
            # Filter by country if specified (backup uses iso_3166_1)
            station_country = station.get('iso_3166_1', '').upper()
            if country and station_country != country.upper():
                continue
            
            # Filter by name search if specified
            if name_search and name_search.lower() not in station.get('name', '').lower():
                continue
            
            # Format for our UI (backup uses different field names)
            formatted = {
                'name': station.get('name', 'Unknown Station'),
                'url': station.get('url_stream') or station.get('url_resolved', ''),
                'favicon': station.get('url_favicon', ''),
                'country': station.get('iso_3166_1', ''),
                'tags': station.get('tags', ''),
                'genre': station.get('tags', '').split(',')[0] if station.get('tags') else '',
                'bitrate': station.get('bitrate', 0),
                'codec': station.get('codec', ''),
                'homepage': station.get('url_homepage', '')
            }
            filtered.append(formatted)
            
            # Limit results
            if len(filtered) >= int(limit):
                break
        
        print(f"Filtered to {len(filtered)} stations from backup database")
        return filtered
    except Exception as e:
        print(f"Error filtering backup stations: {e}")
        import traceback
        traceback.print_exc()
        return []

@app.route('/api/radio/backup/download', methods=['POST'])
def download_radio_backup():
    """Download the latest radio browser backup database."""
    app_ctx = {
        'BACKUP_DB_URL': BACKUP_DB_URL,
        'BACKUP_DB_FILE': BACKUP_DB_FILE,
        'load_backup_database': load_backup_database
    }
    return download_radio_backup_handler(app_ctx)

@app.route('/api/radio/backup/status', methods=['GET'])
def get_backup_status():
    """Check if backup database exists and get its info."""
    app_ctx = {
        'BACKUP_DB_FILE': BACKUP_DB_FILE,
        'load_backup_database': load_backup_database
    }
    return get_backup_status_handler(app_ctx)

@app.route('/api/radio/stations', methods=['GET'])
def get_radio_stations():
    """Get radio stations from Radio Browser API with caching."""
    app_ctx = {
        'radio_stations_cache': radio_stations_cache,
        'CACHE_DURATION': CACHE_DURATION,
        'load_backup_database': load_backup_database,
        'filter_backup_stations': filter_backup_stations
    }
    return get_radio_stations_handler(app_ctx)

# Cache for stream favicons (stream_url -> favicon_url)
stream_favicon_cache = {}
# Cache for stream station names (stream_url -> station_name)
stream_name_cache = {}
# Cache for Bandcamp stream metadata (stream_url -> {artist, title, album, artwork_url})
bandcamp_metadata_cache = {}

@app.route('/api/radio/play', methods=['POST'])
def play_radio_station():
    """Play a radio station."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'socketio': socketio,
        'get_mpd_status_for_display': get_mpd_status_for_display,
        'stream_favicon_cache': stream_favicon_cache,
        'stream_name_cache': stream_name_cache
    }
    return play_radio_station_handler(app_ctx)

# --- Manual Radio Stations API ---
@app.route('/api/radio/manual/list', methods=['GET'])
def get_manual_stations():
    """Get list of manually added radio stations."""
    app_ctx = {'load_manual_stations': load_manual_stations}
    return get_manual_stations_handler(app_ctx)

@app.route('/api/radio/manual/save', methods=['POST'])
def save_manual_station():
    """Save a manually added radio station."""
    app_ctx = {'add_manual_station': add_manual_station}
    return save_manual_station_handler(app_ctx)

@app.route('/api/radio/manual/remove', methods=['POST'])
def remove_manual_station_endpoint():
    """Remove a manually added station by URL."""
    app_ctx = {'remove_manual_station': remove_manual_station}
    return remove_manual_station_handler(app_ctx)

# --- Safer actions for Last.fm artist items (Charts page) ---
@app.route('/add_top_albums_by_artist', methods=['POST'])
def add_top_albums_by_artist():
    """Add top N albums (1-5) by an artist based on Last.fm popularity."""
    if not LASTFM_API_KEY:
        return jsonify({'status': 'error', 'message': 'Last.fm API key not set. Configure it in Settings.'}), 400

    try:
        if request.is_json:
            data = request.get_json()
            artist = (data.get('artist') or '').strip()
            count = int(data.get('count') or 1)
        else:
            artist = (request.form.get('artist') or '').strip()
            count = int(request.form.get('count', 1))

        if not artist:
            return jsonify({'status': 'error', 'message': 'Artist is required'}), 400

        # Bound the count for safety
        if count < 1:
            count = 1
        if count > 5:
            count = 5

        top_albums = get_top_albums_from_lastfm(artist, limit=count)
        if not top_albums:
            return jsonify({'status': 'error', 'message': f'No top albums found for {artist} on Last.fm'}), 404

        client = connect_mpd_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500

        total_added = 0
        albums_processed = []
        try:
            for entry in top_albums:
                album_name = entry.get('album') or entry.get('name')
                if not album_name:
                    continue
                added = _add_album_songs_to_playlist_with_client(client, artist, album_name)
                if added > 0:
                    total_added += added
                    albums_processed.append({'album': album_name, 'songs_added': added})
        finally:
            try:
                client.disconnect()
            except Exception:
                pass

        if total_added == 0:
            msg = f"No local songs found for top {len(top_albums)} album(s) by {artist}."
            socketio.emit('server_message', {'type': 'warning', 'text': msg})
            return jsonify({'status': 'error', 'message': msg}), 404

        msg = f"Added {total_added} songs from {len(albums_processed)} top album(s) by {artist}."
        socketio.emit('server_message', {'type': 'success', 'text': msg})
        socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
        return jsonify({'status': 'success', 'message': msg, 'details': albums_processed})

    except Exception as e:
        print(f"Error in add_top_albums_by_artist: {e}")
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'}), 500

@app.route('/add_top_tracks_by_artist', methods=['POST'])
def add_top_tracks_by_artist():
    """Add top N tracks (1-20) by an artist based on Last.fm popularity."""
    if not LASTFM_API_KEY:
        return jsonify({'status': 'error', 'message': 'Last.fm API key not set. Configure it in Settings.'}), 400

    try:
        if request.is_json:
            data = request.get_json()
            artist = (data.get('artist') or '').strip()
            count = int(data.get('count') or 10)
        else:
            artist = (request.form.get('artist') or '').strip()
            count = int(request.form.get('count', 10))

        if not artist:
            return jsonify({'status': 'error', 'message': 'Artist is required'}), 400

        # Bound the count for safety
        if count < 1:
            count = 1
        if count > 20:
            count = 20

        tracks = get_top_tracks_from_lastfm(artist, limit=count)
        if not tracks:
            return jsonify({'status': 'error', 'message': f'No top tracks found for {artist} on Last.fm'}), 404

        client = connect_mpd_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500

        added_count = 0
        try:
            for t in tracks:
                title = t.get('title') or t.get('name')
                if not title:
                    continue
                try:
                    results = client.search('artist', artist, 'title', title)
                except Exception as se:
                    print(f"MPD search error for {artist} - {title}: {se}")
                    results = []
                if results:
                    # Add the first match
                    file_path = results[0].get('file')
                    if file_path:
                        try:
                            client.add(file_path)
                            added_count += 1
                        except CommandError as e:
                            print(f"MPD add error for {file_path}: {e}")
                else:
                    print(f"Top track not found locally: {artist} - {title}")
        finally:
            try:
                client.disconnect()
            except Exception:
                pass

        if added_count == 0:
            msg = f"No local matches for top {len(tracks)} track(s) by {artist}."
            socketio.emit('server_message', {'type': 'warning', 'text': msg})
            return jsonify({'status': 'error', 'message': msg}), 404

        msg = f"Added {added_count} top track(s) by {artist}."
        socketio.emit('server_message', {'type': 'success', 'text': msg})
        socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
        return jsonify({'status': 'success', 'message': msg, 'tracks_added': added_count})

    except Exception as e:
        print(f"Error in add_top_tracks_by_artist: {e}")
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'}), 500

@app.route('/add_random_by_genre', methods=['POST'])
def add_random_by_genre():
    """Add random songs from selected genres using Auto-Fill settings."""
    try:
        # Handle FormData
        genres_json = request.form.get('genres')
        
        if genres_json:
            import json
            genres = json.loads(genres_json)
        else:
            genres = []
        
        if not genres:
            error_msg = 'No genres selected'
            socketio.emit('server_message', {'type': 'error', 'text': error_msg})
            return jsonify({'status': 'error', 'message': error_msg}), 400
        
        # Use Auto-Fill settings for track count
        num_tracks = random.randint(auto_fill_num_tracks_min, auto_fill_num_tracks_max)
        
        client = connect_mpd_client()
        if not client:
            error_msg = 'Could not connect to MPD'
            socketio.emit('server_message', {'type': 'error', 'text': error_msg})
            return jsonify({'status': 'error', 'message': error_msg}), 500
        
        try:
            # Get songs from all selected genres (OR logic)
            all_songs = []
            for genre in genres:
                genre_songs = client.find('genre', genre)
                all_songs.extend(genre_songs)
            
            if not all_songs:
                client.disconnect()
                error_msg = 'No songs found in selected genres'
                socketio.emit('server_message', {'type': 'error', 'text': error_msg})
                return jsonify({'status': 'error', 'message': error_msg}), 404
            
            # Remove duplicates (songs that appear in multiple selected genres)
            unique_songs = {}
            for song in all_songs:
                file_path = song.get('file', '')
                if file_path:
                    unique_songs[file_path] = song
            
            songs_list = list(unique_songs.values())
            
            # Shuffle and limit to requested number
            random.shuffle(songs_list)
            selected_songs = songs_list[:num_tracks]
            
            # Add songs to playlist
            for song in selected_songs:
                client.add(song['file'])
            
            # Small delay to ensure MPD processes the additions
            import time
            time.sleep(0.2)
            
            client.disconnect()
            
            genre_list = ', '.join(genres[:3]) + ('...' if len(genres) > 3 else '')
            success_msg = f'Added {len(selected_songs)} random songs from genres: {genre_list} (using Auto-Fill settings: {auto_fill_num_tracks_min}-{auto_fill_num_tracks_max})'
            socketio.emit('server_message', {'type': 'success', 'text': success_msg})
            
            return jsonify({
                'status': 'success', 
                'message': success_msg,
                'songs_added': len(selected_songs)
            })
            
        except Exception as e:
            client.disconnect()
            error_msg = f'MPD error: {str(e)}'
            socketio.emit('server_message', {'type': 'error', 'text': error_msg})
            return jsonify({'status': 'error', 'message': error_msg}), 500
            
    except Exception as e:
        error_msg = f'Server error: {str(e)}'
        socketio.emit('server_message', {'type': 'error', 'text': error_msg})
        return jsonify({'status': 'error', 'message': error_msg}), 500

# ============================================================================
# MULTI-DISC ALBUM ORGANIZATION FUNCTIONS
# ============================================================================

def extract_disc_number(song):
    """
    Extract disc number from song metadata.
    Returns integer disc number, or None if not available.
    
    Handles formats:
    - disc: "1", "2" (just number)
    - disc: "1/2" (disc/total_discs)
    - Returns 1 by default for single-disc albums
    """
    disc_field = song.get('disc', '')
    
    # Handle disc field which can be a string or list
    if isinstance(disc_field, list):
        disc_str = disc_field[0] if disc_field else ''
    else:
        disc_str = str(disc_field)
    
    disc_str = disc_str.strip()
    if not disc_str:
        return 1  # Default to disc 1 if no disc info
    
    # Handle "1/2" format (disc/total)
    if '/' in disc_str:
        disc_str = disc_str.split('/')[0]
    
    try:
        disc_num = int(disc_str)
        return disc_num if disc_num > 0 else 1
    except (ValueError, TypeError):
        return 1  # Default to disc 1 on parse error


def organize_album_by_disc(songs):
    """
    Group songs by disc number.
    Returns dict {disc_num: [songs]} if multi-disc, or None if single-disc.
    
    Args:
        songs: List of song dicts from MPD (each has 'file' and optional 'disc' field)
    
    Returns:
        dict: {1: [...], 2: [...]} if multi-disc detected, None otherwise
    """
    if not songs:
        return None
    
    disc_map = {}
    max_disc = 0
    
    for song in songs:
        disc_num = extract_disc_number(song)
        max_disc = max(max_disc, disc_num)
        
        if disc_num not in disc_map:
            disc_map[disc_num] = []
        disc_map[disc_num].append(song)
    
    # Only return disc map if actually multi-disc
    if max_disc > 1:
        print(f"[DISC] Multi-disc album detected: {max_disc} discs", flush=True)
        for disc_num in sorted(disc_map.keys()):
            print(f"[DISC] Disc {disc_num}: {len(disc_map[disc_num])} tracks", flush=True)
        return disc_map
    
    return None  # Single-disc, no organization needed


def adjust_file_paths_for_disc(songs, disc_map):
    """
    Adjust file paths to include disc subdirectory structure.
    
    Converts paths like:
      'Artist/Album/01-Track.mp3' 
    To:
      'Artist/Album/disc1/01-Track.mp3'
    
    Args:
        songs: List of song dicts from MPD
        disc_map: Dict {disc_num: [songs]} from organize_album_by_disc()
    
    Returns:
        List of songs with updated 'file' paths
    """
    if not disc_map:
        return songs
    
    adjusted_songs = []
    
    for disc_num in sorted(disc_map.keys()):
        disc_songs = disc_map[disc_num]
        
        for song in disc_songs:
            song_copy = song.copy()  # Don't modify original
            old_file = song_copy.get('file', '')
            
            if not old_file:
                adjusted_songs.append(song_copy)
                continue
            
            # Insert disc directory before filename
            # e.g., 'Artist/Album/track.mp3' -> 'Artist/Album/disc1/track.mp3'
            parts = old_file.rsplit('/', 1)  # Split into directory and filename
            
            if len(parts) == 2:
                directory, filename = parts
                new_file = f"{directory}/disc{disc_num}/{filename}"
            else:
                # Just filename, no directory
                new_file = f"disc{disc_num}/{old_file}"
            
            song_copy['file'] = new_file
            print(f"[DISC] D{disc_num}: {old_file} -> {new_file}", flush=True)
            adjusted_songs.append(song_copy)
    
    return adjusted_songs

@app.route('/add_album_to_playlist', methods=['POST'])
def add_album_to_playlist():
    """Add an entire album to the playlist."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'socketio': socketio,
        'get_mpd_status_for_display': get_mpd_status_for_display,
        'organize_album_by_disc': organize_album_by_disc
    }
    return add_album_to_playlist_handler(app_ctx)


@app.route('/clear_and_add_album', methods=['POST'])
def clear_and_add_album():
    """Clear playlist and add an entire album (or just a disc)."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'socketio': socketio,
        'get_mpd_status_for_display': get_mpd_status_for_display,
        'organize_album_by_disc': organize_album_by_disc
    }
    return clear_and_add_album_handler(app_ctx)

@app.route('/get_album_songs', methods=['POST'])
def get_album_songs():
    """Get all songs from a specific album."""
    try:
        artist = request.form.get('artist', '').strip()
        album = request.form.get('album', '')  # Don't strip - preserve trailing spaces in album names
        
        if not album or not album.strip():
            return jsonify({'error': 'Album is required'}), 400
            
        client = connect_mpd_client()
        if not client:
            return jsonify({'error': 'Could not connect to MPD'}), 500
            
        try:
            print(f"[DEBUG] /get_album_songs - Searching for album='{album}', artist='{artist}'", flush=True)
            
            # If artist specified, search by both artist and album for exact match
            if artist:
                songs = client.find('album', album, 'artist', artist)
                print(f"[DEBUG] /get_album_songs - Album+Artist exact search returned {len(songs) if songs else 0} tracks", flush=True)
                
                # If no exact match, try with trailing space
                if not songs:
                    songs = client.find('album', album + ' ', 'artist', artist)
                    print(f"[DEBUG] /get_album_songs - Album+Artist search with trailing space returned {len(songs) if songs else 0} tracks", flush=True)
            else:
                # No artist specified, search by album only
                songs = client.find('album', album)
                print(f"[DEBUG] /get_album_songs - Album-only exact search returned {len(songs) if songs else 0} tracks", flush=True)
                
                # If no results, try with trailing space
                if not songs:
                    songs = client.find('album', album + ' ')
                    print(f"[DEBUG] /get_album_songs - Album-only search with trailing space returned {len(songs) if songs else 0} tracks", flush=True)
            
            # Format the songs for the frontend
            formatted_songs = []
            for song in songs:
                formatted_songs.append({
                    'file': song.get('file', ''),
                    'title': song.get('title', 'Unknown Title'),
                    'artist': song.get('artist', artist),
                    'album': song.get('album', album),
                    'track': song.get('track', ''),
                    'time': song.get('time', '0')
                })
            
            # Sort by track number if available
            formatted_songs.sort(key=lambda x: int(x['track'].split('/')[0]) if x['track'] and x['track'].split('/')[0].isdigit() else 999)
            
            # Check if this is a multi-disc album
            disc_structure = organize_album_by_disc(songs)
            
            response = {'songs': formatted_songs}
            
            if disc_structure and len(disc_structure) > 1:
                disc_structure_serializable = {}
                for disc_num, disc_tracks in disc_structure.items():
                    disc_structure_serializable[str(disc_num)] = [
                        {
                            'file': track.get('file', ''),
                            'title': track.get('title', 'Unknown Title'),
                            'artist': track.get('artist', artist),
                            'album': track.get('album', album),
                            'track': track.get('track', ''),
                            'time': track.get('time', '0')
                        }
                        for track in disc_tracks
                    ]
                response['disc_structure'] = disc_structure_serializable
            
            client.disconnect()
            return jsonify(response)
            
        except Exception as e:
            if client:
                client.disconnect()
            return jsonify({'error': f'Error fetching album songs: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Error in get_album_songs: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/add_song_to_playlist', methods=['POST'])
def add_song_to_playlist():
    """Add a single song to the playlist."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'socketio': socketio,
        'get_mpd_status_for_display': get_mpd_status_for_display
    }
    return add_song_to_playlist_handler(app_ctx)

def get_mpd_playlist():
    """Fetches the current MPD playlist."""
    client = connect_mpd_client()
    if not client:
        return []
    try:
        playlist = client.playlistinfo()
        client.disconnect()
        # Add a 'pos' (position) to each song for easier removal and playing
        for i, song in enumerate(playlist):
            song['pos'] = i
        return playlist
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return []

@app.route('/playlist')
def playlist_page():
    """Renders the playlist HTML page."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'bandcamp_service': bandcamp_service
    }
    return playlist_page_handler(app_ctx)

@app.route('/history')
def history_page():
    """Renders the history HTML page."""
    app_ctx = {
        'get_mpd_status_for_display': get_mpd_status_for_display,
        'last_mpd_status': last_mpd_status,
        'app': app,
        'play_history': play_history
    }
    return history_page_handler(app_ctx)

@app.route('/api/history', methods=['GET'])
def get_history():
    """Return play history as JSON."""
    app_ctx = {
        'play_history': play_history
    }
    return get_history_handler(app_ctx)

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Clear play history."""
    global play_history, last_tracked_song_id
    app_ctx = {}
    result = clear_history_handler(app_ctx)
    # Actually clear the history
    play_history = []
    last_tracked_song_id = None
    return result

@app.route('/radio')
def radio_page():
    """Renders the internet radio page."""
    return render_template('radio.html')

# Album Art Routes
@app.route('/clear_art_cache', methods=['POST'])
def clear_album_art_cache():
    """Clear the album art cache to force fresh fetches"""
    global album_art_cache
    album_art_cache = {}
    print("Album art cache cleared.")
    return jsonify({'status': 'success', 'message': 'Album art cache cleared'})

@app.route('/album_art')
def get_album_art():
    """
    Serves album art for the currently playing song or thumbnails for browse pages.
    Prioritizes local files, then fetches from Last.fm if not found.
    For streams, attempts to fetch art via Last.fm track.getInfo.
    Supports 'size=thumb' parameter for 64x64px thumbnails.
    HIGH-QUALITY MODE: If prefer_lastfm=true, tries LastFM first for best quality.
    """
    song_file = request.args.get('song_file', '') or request.args.get('file', '')
    artist = request.args.get('artist', '')
    album = request.args.get('album', '')
    size = request.args.get('size', 'full')  # 'full' or 'thumb'
    prefer_lastfm = request.args.get('prefer_lastfm', 'false').lower() == 'true'  # High-quality mode

    # DEBUG: Log all requests to /album_art
    print(f"[ALBUM_ART] Request: song_file={bool(song_file)}, artist={artist[:20] if artist else 'NONE'}, album={album[:20] if album else 'NONE'}, size={size}, client_ip={request.remote_addr}")

    # Rate limiting: prevent client loops from hammering NFS with identical requests
    client_ip = request.remote_addr
    cache_key_base = f"{song_file}-{artist}-{album}-{size}"
    rate_limit_key = (client_ip, cache_key_base)
    current_time = time.time()
    
    if rate_limit_key in album_art_request_times:
        last_request = album_art_request_times[rate_limit_key]
        time_since_last = current_time - last_request
        if time_since_last < ALBUM_ART_RATE_LIMIT_SECONDS:
            print(f"[RATE LIMIT] Blocked request from {client_ip} - {time_since_last:.2f}s since last request (limit: {ALBUM_ART_RATE_LIMIT_SECONDS}s)")
            # Too soon - return cached version immediately if available
            cached_data = album_art_cache.get(cache_key_base)
            if cached_data:
                print(f"[RATE LIMIT] Serving cached version")
                return Response(cached_data['data'], mimetype=cached_data['mimetype'])
            # If not cached yet, serve placeholder to avoid NFS stress
            print(f"[RATE LIMIT] No cache, serving placeholder")
            return redirect(url_for('static_placeholder_art'))
    
    # Update last request time
    album_art_request_times[rate_limit_key] = current_time
    
    # Clean up old rate limit entries (keep only last 1000 entries)
    if len(album_art_request_times) > 1000:
        # Remove oldest entries
        sorted_keys = sorted(album_art_request_times.items(), key=lambda x: x[1])
        for old_key, _ in sorted_keys[:500]:
            del album_art_request_times[old_key]

    # Detect if this is a stream
    is_stream = song_file and (song_file.startswith('http://') or song_file.startswith('https://'))
    
    # HIGH-QUALITY MODE: Try LastFM first if requested (for full-screen view)
    if prefer_lastfm and not is_stream and artist and album and LASTFM_API_KEY:
        print(f"[HIGH-QUALITY MODE] Trying LastFM first for {artist} - {album}")
        try:
            # Create cache key for high-quality images
            cache_key = f"hq-{song_file}-{artist}-{album}" if song_file else f"hq-{artist}-{album}"
            
            cached_image_data = album_art_cache.get(cache_key)
            if cached_image_data:
                print(f"Serving high-quality album art from cache.")
                return Response(cached_image_data['data'], mimetype=cached_image_data['mimetype'])
            
            params = {
                'method': 'album.getinfo',
                'api_key': LASTFM_API_KEY,
                'artist': artist,
                'album': album,
                'format': 'json'
            }
            response = requests.get(LASTFM_API_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            image_url = None
            if 'album' in data and 'image' in data['album']:
                for size_preference in ['mega', 'extralarge', 'large']:
                    for img in data['album']['image']:
                        if img.get('size') == size_preference and img.get('#text'):
                            image_url = img['#text']
                            print(f"[HIGH-QUALITY] Found {size_preference} size image")
                            break
                    if image_url:
                        break

            if image_url:
                image_response = requests.get(image_url, timeout=5)
                image_response.raise_for_status()
                image_data = image_response.content
                mimetype = image_response.headers.get('Content-Type', 'image/jpeg')
                
                album_art_cache[cache_key] = {'data': image_data, 'mimetype': mimetype}
                print(f"[HIGH-QUALITY] Successfully fetched from LastFM")
                return Response(image_data, mimetype=mimetype)
            else:
                print(f"[HIGH-QUALITY] No LastFM image found, falling back to local")
        except Exception as e:
            print(f"[HIGH-QUALITY] LastFM fetch failed: {e}, falling back to local")

    # 1. Try local album art first (skip for streams)
    if song_file and not is_stream:
        full_song_path = os.path.join(MUSIC_DIRECTORY, song_file)
        album_dir = os.path.dirname(full_song_path)

        art_filenames = [
            'folder.jpg', 'cover.jpg', 'Cover.jpg', '00cover.jpg', 'album.jpg', 'front.jpg',
            'folder.png', 'cover.png', 'album.png', 'front.png'
        ]

        for filename in art_filenames:
            art_path = os.path.join(album_dir, filename)
            if os.path.exists(art_path) and os.path.isfile(art_path):
                real_art_path = os.path.realpath(art_path)
                real_music_dir = os.path.realpath(MUSIC_DIRECTORY)
                if not real_art_path.startswith(real_music_dir):
                    print(f"Security warning: Attempt to access file outside music directory: {real_art_path}")
                    return redirect(url_for('static_placeholder_art'))
                
                # Generate thumbnail if requested
                if size == 'thumb':
                    try:
                        from PIL import Image
                        import io
                        
                        # Create cache key for thumbnail
                        thumb_cache_key = f"thumb-{artist}-{album}-{filename}"
                        cached_thumb = album_art_cache.get(thumb_cache_key)
                        
                        if cached_thumb:
                            return Response(cached_thumb['data'], mimetype=cached_thumb['mimetype'])
                        
                        # Generate thumbnail
                        with Image.open(art_path) as img:
                            img.thumbnail((64, 64), Image.Resampling.LANCZOS)
                            img_io = io.BytesIO()
                            img.save(img_io, 'JPEG', quality=85, optimize=True)
                            img_data = img_io.getvalue()
                            
                            # Cache the thumbnail
                            album_art_cache[thumb_cache_key] = {'data': img_data, 'mimetype': 'image/jpeg'}
                            return Response(img_data, mimetype='image/jpeg')
                    except Exception as e:
                        print(f"Error generating thumbnail: {e}")
                        # Fall through to serve original file
                
                return send_from_directory(album_dir, filename, mimetype='image/jpeg')
    
    print(f"[ALBUM_ART] No local art found, checking streams and Last.fm")
    
    # 2. For streams with artist but no album, try Last.fm track.getInfo
    if is_stream and artist and artist != 'N/A' and LASTFM_API_KEY:
        # Get title from request args
        title = request.args.get('title', '')
        
        if title and title != 'N/A':
            cache_key = f"stream-{artist}-{title}" if size == 'full' else f"thumb-stream-{artist}-{title}"
            cached_image_data = album_art_cache.get(cache_key)

            if cached_image_data:
                print(f"Serving stream album art for {artist} - {title} from cache.")
                return Response(cached_image_data['data'], mimetype=cached_image_data['mimetype'])
            
            try:
                # Use track.getInfo to get album art for the current track
                params = {
                    'method': 'track.getinfo',
                    'api_key': LASTFM_API_KEY,
                    'artist': artist,
                    'track': title,
                    'format': 'json'
                }
                print(f"Attempting to fetch album art for stream: {artist} - {title} from Last.fm...")
                response = requests.get(LASTFM_API_URL, params=params, timeout=5)
                response.raise_for_status()
                data = response.json()

                image_url = None
                if 'track' in data and 'album' in data['track'] and 'image' in data['track']['album']:
                    # Find the highest quality image - mega is largest available from Last.fm
                    for size_preference in ['mega', 'extralarge', 'large', 'medium']:
                        for img in data['track']['album']['image']:
                            if img.get('size') == size_preference and img.get('#text'):
                                image_url = img['#text']
                                print(f"Found {size_preference} image for {artist} - {title}")
                                break
                        if image_url:
                            break

                if image_url:
                    image_response = requests.get(image_url, timeout=5)
                    image_response.raise_for_status()
                    image_data = image_response.content
                    mimetype = image_response.headers.get('Content-Type', 'image/jpeg')

                    # Generate thumbnail if requested
                    if size == 'thumb':
                        try:
                            from PIL import Image
                            import io
                            
                            with Image.open(io.BytesIO(image_data)) as img:
                                img.thumbnail((64, 64), Image.Resampling.LANCZOS)
                                img_io = io.BytesIO()
                                img.save(img_io, 'JPEG', quality=85, optimize=True)
                                thumb_data = img_io.getvalue()
                                
                                album_art_cache[cache_key] = {'data': thumb_data, 'mimetype': 'image/jpeg'}
                                return Response(thumb_data, mimetype='image/jpeg')
                        except Exception as e:
                            print(f"Error generating stream thumbnail: {e}")

                    # Store full image in cache
                    full_cache_key = f"stream-{artist}-{title}"
                    album_art_cache[full_cache_key] = {'data': image_data, 'mimetype': mimetype}
                    return Response(image_data, mimetype=mimetype)
                else:
                    print(f"No image found for stream track: {artist} - {title}")

            except requests.exceptions.RequestException as req_e:
                print(f"Error fetching stream album art from Last.fm: {req_e}")
            except Exception as e:
                print(f"An unexpected error occurred during Last.fm stream art fetch: {e}")
    
    # 3. If no local art or stream art, try Last.fm album lookup (only if API key is provided)
    if artist and album and LASTFM_API_KEY:
        # Create more unique cache keys by including file path if available
        if song_file:
            cache_key = f"{song_file}-{artist}-{album}" if size == 'full' else f"thumb-{song_file}-{artist}-{album}"
        else:
            cache_key = f"{artist}-{album}" if size == 'full' else f"thumb-{artist}-{album}"
        
        cached_image_data = album_art_cache.get(cache_key)

        if cached_image_data:
            print(f"Serving album art for {artist} - {album} from cache ({'thumbnail' if size == 'thumb' else 'full size'}).")
            return Response(cached_image_data['data'], mimetype=cached_image_data['mimetype'])
        
        try:
            params = {
                'method': 'album.getinfo',
                'api_key': LASTFM_API_KEY,
                'artist': artist,
                'album': album,
                'format': 'json'
            }
            print(f"Attempting to fetch album art for {artist} - {album} from Last.fm...")
            response = requests.get(LASTFM_API_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            image_url = None
            if 'album' in data and 'image' in data['album']:
                # Find the highest quality image available - check in order of preference
                for size_preference in ['mega', 'extralarge', 'large', 'medium']:
                    for img in data['album']['image']:
                        if img.get('size') == size_preference and img.get('#text'):
                            image_url = img['#text']
                            print(f"Found {size_preference} size image for {artist} - {album}")
                            break
                    if image_url:
                        break

            if image_url:
                print(f"Found Last.fm image URL: {image_url}")
                image_response = requests.get(image_url, timeout=5)
                image_response.raise_for_status()
                image_data = image_response.content
                mimetype = image_response.headers.get('Content-Type', 'image/jpeg')

                # Generate thumbnail if requested
                if size == 'thumb':
                    try:
                        from PIL import Image
                        import io
                        
                        with Image.open(io.BytesIO(image_data)) as img:
                            img.thumbnail((64, 64), Image.Resampling.LANCZOS)
                            img_io = io.BytesIO()
                            img.save(img_io, 'JPEG', quality=85, optimize=True)
                            thumb_data = img_io.getvalue()
                            
                            # Store thumbnail in cache
                            album_art_cache[cache_key] = {'data': thumb_data, 'mimetype': 'image/jpeg'}
                            return Response(thumb_data, mimetype='image/jpeg')
                    except Exception as e:
                        print(f"Error generating Last.fm thumbnail: {e}")
                        # Fall through to serve original image

                # Store full image in cache
                if song_file:
                    full_cache_key = f"{song_file}-{artist}-{album}"
                else:
                    full_cache_key = f"{artist}-{album}"
                album_art_cache[full_cache_key] = {'data': image_data, 'mimetype': mimetype}
                return Response(image_data, mimetype=mimetype)
            else:
                print(f"No image URL found for {artist} - {album} from Last.fm API.")

        except requests.exceptions.RequestException as req_e:
            print(f"Error fetching album art from Last.fm: {req_e}")
        except ValueError as json_e:
            print(f"Error parsing Last.fm JSON response: {json_e}")
        except Exception as e:
            print(f"An unexpected error occurred during Last.fm art fetch: {e}")

    # 4a. For Bandcamp streams, try to use cached artwork (match by track_id)
    bc_meta = None
    if is_stream and 'bandcamp.com' in song_file and 'track_id=' in song_file:
        import re
        track_id_match = re.search(r'track_id=(\d+)', song_file)
        if track_id_match:
            cache_key = f"track_{track_id_match.group(1)}"
            bc_meta = bandcamp_metadata_cache.get(cache_key)
    elif is_stream and song_file in bandcamp_metadata_cache:
        bc_meta = bandcamp_metadata_cache[song_file]
    
    if bc_meta:
        artwork_url = bc_meta.get('artwork_url', '')
        if artwork_url:
            cache_key = f"bandcamp-{song_file}" if size == 'full' else f"thumb-bandcamp-{song_file}"
            
            # Check cache first
            cached_art = album_art_cache.get(cache_key)
            if cached_art:
                print(f"Serving cached Bandcamp artwork for: {song_file}")
                return Response(cached_art['data'], mimetype=cached_art['mimetype'])
            
            try:
                # If artwork_url is a relative path to our own API, make internal request
                if artwork_url.startswith('/api/bandcamp/artwork/'):
                    artwork_url = f"http://localhost:5003{artwork_url}"
                print(f"Fetching Bandcamp artwork: {artwork_url}")
                art_response = requests.get(artwork_url, timeout=5)
                art_response.raise_for_status()
                art_data = art_response.content
                mimetype = art_response.headers.get('Content-Type', 'image/jpeg')
                
                # Cache and return
                album_art_cache[cache_key] = {'data': art_data, 'mimetype': mimetype}
                print(f"Cached and serving Bandcamp artwork for: {song_file}")
                return Response(art_data, mimetype=mimetype)
            except Exception as e:
                print(f"Error fetching Bandcamp artwork: {e}")
    
    # 4b. For streams with no Last.fm art, try to use cached favicon
    if is_stream and song_file in stream_favicon_cache:
        favicon_url = stream_favicon_cache[song_file]
        cache_key = f"favicon-{song_file}" if size == 'full' else f"thumb-favicon-{song_file}"
        
        # Check cache first
        cached_favicon = album_art_cache.get(cache_key)
        if cached_favicon:
            print(f"Serving cached favicon for stream: {song_file}")
            return Response(cached_favicon['data'], mimetype=cached_favicon['mimetype'])
        
        try:
            print(f"Fetching favicon for stream: {favicon_url}")
            favicon_response = requests.get(favicon_url, timeout=5)
            favicon_response.raise_for_status()
            favicon_data = favicon_response.content
            mimetype = favicon_response.headers.get('Content-Type', 'image/png')
            
            # Generate thumbnail if requested
            if size == 'thumb':
                try:
                    from PIL import Image
                    import io
                    
                    with Image.open(io.BytesIO(favicon_data)) as img:
                        img.thumbnail((64, 64), Image.Resampling.LANCZOS)
                        img_io = io.BytesIO()
                        img.save(img_io, 'PNG', optimize=True)
                        thumb_data = img_io.getvalue()
                        
                        album_art_cache[cache_key] = {'data': thumb_data, 'mimetype': 'image/png'}
                        return Response(thumb_data, mimetype='image/png')
                except Exception as e:
                    print(f"Error generating favicon thumbnail: {e}")
            
            # Cache and return full favicon
            full_cache_key = f"favicon-{song_file}"
            album_art_cache[full_cache_key] = {'data': favicon_data, 'mimetype': mimetype}
            return Response(favicon_data, mimetype=mimetype)
            
        except Exception as e:
            print(f"Error fetching favicon: {e}")

    # 5. If no local or Last.fm art or favicon, redirect to the placeholder art
    print(f"[ALBUM_ART] No art found anywhere, returning placeholder redirect")
    return redirect(url_for('static_placeholder_art'))

@app.route('/static_placeholder_art')
def static_placeholder_art():
    """Generates and serves an artistic 'No Art' placeholder image with gradient and musical motif."""
    img_size = (300, 300)
    
    # Create gradient background (dark blue to deep purple)
    img = Image.new('RGB', img_size)
    pixels = img.load()
    
    for y in range(img_size[1]):
        # Gradient from #1a3a52 (dark blue) to #2d1b4e (deep purple)
        r = int(26 + (45 - 26) * (y / img_size[1]))
        g = int(58 + (27 - 58) * (y / img_size[1]))
        b = int(82 + (78 - 82) * (y / img_size[1]))
        for x in range(img_size[0]):
            pixels[x, y] = (r, g, b)
    
    d = ImageDraw.Draw(img, 'RGBA')
    
    # Draw subtle circles/rings in the background
    center_x, center_y = img_size[0] // 2, img_size[1] // 2
    for radius in [80, 60, 40]:
        d.ellipse(
            [(center_x - radius, center_y - radius), (center_x + radius, center_y + radius)],
            outline=(61, 189, 227, 30),  # Light blue, semi-transparent
            width=2
        )
    
    # Draw musical notes or radio waves
    # Draw 3 radio wave arcs
    for i, (offset, alpha) in enumerate([(0, 80), (15, 60), (30, 40)]):
        r = 25 + offset
        d.arc(
            [(center_x - r, center_y - r), (center_x + r, center_y + r)],
            0, 180,
            fill=(52, 211, 153, alpha),  # Green, varying transparency
            width=2
        )
    
    # Draw center circle
    d.ellipse(
        [(center_x - 15, center_y - 15), (center_x + 15, center_y + 15)],
        fill=(52, 211, 153, 200),  # Solid green center
        outline=(255, 255, 255, 100)
    )
    
    # Draw a music note in the center
    # Stem
    d.line([(center_x + 2, center_y - 12), (center_x + 2, center_y + 5)], fill=(255, 255, 255, 255), width=2)
    # Note heads (two eighth notes)
    d.ellipse([(center_x - 2, center_y - 5), (center_x + 6, center_y + 1)], fill=(255, 255, 255, 255))
    d.ellipse([(center_x + 8, center_y + 2), (center_x + 16, center_y + 8)], fill=(255, 255, 255, 255))
    # Beam connecting notes
    d.line([(center_x + 2, center_y - 5), (center_x + 12, center_y + 2)], fill=(255, 255, 255, 200), width=2)
    
    # Add text
    text = "No Album Art"
    try:
        font_large = ImageFont.truetype(FONT_PATH, 18)
    except IOError:
        font_large = ImageFont.load_default()
    
    # Draw main text with shadow effect
    shadow_offset = 2
    d.text((center_x + shadow_offset, 250 + shadow_offset), text, fill=(0, 0, 0, 100), font=font_large, anchor='mm')
    d.text((center_x, 250), text, fill=(226, 232, 240, 255), font=font_large, anchor='mm')

    byte_io = BytesIO()
    img.save(byte_io, 'PNG')
    byte_io.seek(0)
    return Response(byte_io.getvalue(), mimetype='image/png')

# Auto-fill Routes
@app.route('/toggle_auto_fill', methods=['POST'])
def toggle_auto_fill():
    global auto_fill_active
    app_ctx = {'socketio': socketio}
    result = toggle_auto_fill_handler(app_ctx)
    
    # Update global state
    data = request.get_json()
    new_state = data.get('active')
    if isinstance(new_state, bool):
        auto_fill_active = new_state
        # Emit updated status to all clients
        socketio.emit('auto_fill_status', {
            'active': auto_fill_active,
            'min_queue_length': auto_fill_min_queue_length,
            'num_tracks_min': auto_fill_num_tracks_min,
            'num_tracks_max': auto_fill_num_tracks_max,
            'genre_filter_enabled': auto_fill_genre_filter_enabled
        })
    
    return result


@app.route('/set_auto_fill_settings', methods=['POST'])
def set_auto_fill_settings():
    global auto_fill_min_queue_length, auto_fill_num_tracks_min, auto_fill_num_tracks_max, auto_fill_genre_filter_enabled
    
    app_ctx = {
        'socketio': socketio,
        'auto_fill_min_queue_length': auto_fill_min_queue_length,
        'auto_fill_num_tracks_min': auto_fill_num_tracks_min,
        'auto_fill_num_tracks_max': auto_fill_num_tracks_max,
        'auto_fill_genre_filter_enabled': auto_fill_genre_filter_enabled
    }
    result = set_auto_fill_settings_handler(app_ctx)
    
    # Update global state from request
    data = request.get_json()
    try:
        auto_fill_min_queue_length = int(data.get('min_queue_length', auto_fill_min_queue_length))
        auto_fill_num_tracks_min = int(data.get('num_tracks_min', auto_fill_num_tracks_min))
        auto_fill_num_tracks_max = int(data.get('num_tracks_max', auto_fill_num_tracks_max))
        auto_fill_genre_filter_enabled = bool(data.get('genre_filter_enabled', auto_fill_genre_filter_enabled))
        
        # Emit updated status to all clients
        socketio.emit('auto_fill_status', {
            'active': auto_fill_active,
            'min_queue_length': auto_fill_min_queue_length,
            'num_tracks_min': auto_fill_num_tracks_min,
            'num_tracks_max': auto_fill_num_tracks_max,
            'genre_filter_enabled': auto_fill_genre_filter_enabled,
            'genre_station_mode': genre_station_mode,
            'genre_station_name': genre_station_name,
            'genre_station_genres': genre_station_genres
        })
        return ('', 200)
    except ValueError:
        return ('', 400)


# Playlist Management Routes
@app.route('/remove_from_playlist', methods=['POST'])
def remove_from_playlist():
    """Removes a song from the playlist by its position."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'socketio': socketio
    }
    return remove_from_playlist_handler(app_ctx)

@app.route('/move_track', methods=['POST'])
def move_track():
    """Moves a track up/down or to a specific position in the playlist."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'socketio': socketio
    }
    return move_track_handler(app_ctx)

@app.route('/clear_playlist', methods=['POST'])
def clear_playlist():
    """Clears the entire MPD playlist."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'socketio': socketio
    }
    return clear_playlist_handler(app_ctx)

@app.route('/save_playlist', methods=['POST'])
def save_playlist():
    """Save the current MPD playlist to an M3U file."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'playlists_dir': PLAYLISTS_DIR
    }
    return save_playlist_handler(app_ctx)

@app.route('/list_playlists', methods=['GET'])
def list_playlists():
    """List all saved M3U playlists."""
    app_ctx = {
        'playlists_dir': PLAYLISTS_DIR
    }
    return list_playlists_handler(app_ctx)

@app.route('/load_playlist', methods=['POST'])
def load_playlist():
    """Load a saved M3U playlist into MPD, clearing the current playlist."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'socketio': socketio,
        'playlists_dir': PLAYLISTS_DIR
    }
    return load_playlist_handler(app_ctx)

@app.route('/delete_playlist', methods=['POST'])
def delete_playlist():
    """Delete a saved M3U playlist."""
    app_ctx = {
        'playlists_dir': PLAYLISTS_DIR
    }
    return delete_playlist_handler(app_ctx)

@app.route('/play_song_at_pos', methods=['POST'])
def play_song_at_pos():
    """Plays a song at a specific position in the playlist."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'socketio': socketio,
        'get_mpd_status_for_display': get_mpd_status_for_display
    }
    return play_song_at_pos_handler(app_ctx)


@app.route('/toggle_consume_mode', methods=['POST'])
def toggle_consume_mode():
    """Toggles MPD's consume mode."""
    data = request.get_json()
    new_state = data.get('active')

    if not isinstance(new_state, bool):
        return jsonify({'status': 'error', 'message': 'Invalid state provided'}), 400

    client = connect_mpd_client()
    if not client:
        return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
    try:
        client.consume(1 if new_state else 0)
        client.disconnect()
        status_text = "enabled" if new_state else "disabled"
        socketio.emit('server_message', {'type': 'info', 'text': f'MPD consume mode has been {status_text}.'})
        # Immediately send updated status to reflect the change
        socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
        return jsonify({'status': 'success', 'message': f'Consume mode {status_text}'})
    except CommandError as e:
        print(f"MPD CommandError toggling consume mode: {e}")
        return jsonify({'status': 'error', 'message': f'MPD error: {e}'}), 500
    except Exception as e:
        print(f"Error toggling consume mode: {e}")
        return jsonify({'status': 'error', 'message': f'Error toggling consume mode: {e}'}), 500

@app.route('/toggle_shuffle_mode', methods=['POST'])
def toggle_shuffle_mode():
    """Toggles MPD's shuffle (random) mode."""
    data = request.get_json()
    new_state = data.get('active')

    if not isinstance(new_state, bool):
        return jsonify({'status': 'error', 'message': 'Invalid state provided'}), 400

    client = connect_mpd_client()
    if not client:
        return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
    try:
        client.random(1 if new_state else 0)
        client.disconnect()
        status_text = "enabled" if new_state else "disabled"
        socketio.emit('server_message', {'type': 'info', 'text': f'MPD shuffle mode has been {status_text}.'})
        # Immediately send updated status to reflect the change
        socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
        return jsonify({'status': 'success', 'message': f'Shuffle mode {status_text}'})
    except CommandError as e:
        print(f"MPD CommandError toggling shuffle mode: {e}")
        return jsonify({'status': 'error', 'message': f'MPD error: {e}'}), 500
    except Exception as e:
        print(f"Error toggling shuffle mode: {e}")
        return jsonify({'status': 'error', 'message': f'Error toggling shuffle mode: {e}'}), 500

@app.route('/toggle_crossfade', methods=['POST'])
def toggle_crossfade():
    """Toggles MPD's crossfade mode (5 seconds when enabled, 0 when disabled)."""
    data = request.get_json()
    new_state = data.get('active')

    if not isinstance(new_state, bool):
        return jsonify({'status': 'error', 'message': 'Invalid state provided'}), 400

    client = connect_mpd_client()
    if not client:
        return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
    try:
        # Set crossfade to 5 seconds when enabled, 0 when disabled
        crossfade_seconds = 5 if new_state else 0
        client.crossfade(crossfade_seconds)
        client.disconnect()
        status_text = f"enabled ({crossfade_seconds}s)" if new_state else "disabled"
        socketio.emit('server_message', {'type': 'info', 'text': f'MPD crossfade has been {status_text}.'})
        # Immediately send updated status to reflect the change
        socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
        return jsonify({'status': 'success', 'message': f'Crossfade {status_text}'})
    except CommandError as e:
        print(f"MPD CommandError toggling crossfade: {e}")
        return jsonify({'status': 'error', 'message': f'MPD error: {e}'}), 500
    except Exception as e:
        print(f"Error toggling crossfade: {e}")
        return jsonify({'status': 'error', 'message': f'Error toggling crossfade: {e}'}), 500

@app.route('/get_mpd_status')
def get_mpd_status():
    """API endpoint to get current MPD status."""
    app_ctx = {
        'get_mpd_status_for_display': get_mpd_status_for_display,
        'last_mpd_status': last_mpd_status
    }
    return get_mpd_status_handler(app_ctx)

@app.route('/recent_albums')
def recent_albums():
    """Get recently added albums from MPD database."""
    app_ctx = {
        'get_recent_albums_from_mpd': get_recent_albums_from_mpd
    }
    return recent_albums_handler(app_ctx)


@app.route('/recent')
def recent_albums_page():
    """Display the recent albums page."""
    return recent_albums_page_handler({})


@app.route('/api/list_music_directories')
def list_music_directories():
    """List available directories within the music library for recent albums browsing."""
    app_ctx = {}
    return list_music_directories_handler(app_ctx)


def get_recent_albums_from_mpd(limit=25, force_refresh=False):
    """
    Get recently added albums from configured directories in settings.json.
    This is much faster and more accurate than scanning the entire database.
    Uses smart caching to avoid rescanning when directories haven't changed.
    """
    import time
    global recent_albums_cache, recent_albums_cache_mod_times
    
    # Get directories from settings
    settings = load_settings()
    recent_dirs = settings.get('recent_albums_dir', 'ripped')
    
    # Parse comma-separated directories and clean them up
    if isinstance(recent_dirs, str):
        # Remove /media/music/ prefix if present, MPD uses relative paths
        directories_to_check = [d.strip().replace('/media/music/', '') for d in recent_dirs.split(',') if d.strip()]
    else:
        directories_to_check = ['ripped']  # fallback default
    
    if not directories_to_check:
        directories_to_check = ['ripped']  # ensure we have at least one directory
    
    print(f"Checking recent albums from directories: {directories_to_check}")
    
    # Simple change detection cache - safe fallback to normal scan
    try:
        
        # Skip cache check if force refresh is requested
        if force_refresh:
            print("Force refresh requested, bypassing cache")
        else:
            # Check if we already have cached results
            if recent_albums_cache:
                print(f"Found cached recent albums with {len(recent_albums_cache)} albums")
                
                # Only do directory check if we have cached mod times to compare
                if recent_albums_cache_mod_times:
                    # Quick check if directories have changed
                    current_mod_times = {}
                    client = connect_mpd_client()
                    if client:
                        for directory in directories_to_check:
                            try:
                                # Get directory stats from MPD
                                dir_stats = client.lsinfo(directory)
                                # Use the count and newest file as a simple change indicator
                                files = [item for item in dir_stats if 'file' in item]
                                current_mod_times[directory] = {
                                    'file_count': len(files),
                                    'last_check': time.time()
                                }
                            except:
                                # If we can't check a directory, invalidate cache
                                current_mod_times = None
                                break
                        client.disconnect()
                    
                    # Check if directories haven't changed
                    if (current_mod_times and 
                        current_mod_times == recent_albums_cache_mod_times):
                        print(f"Using cached recent albums (no changes detected)")
                        return recent_albums_cache[:limit]
                    else:
                        print(f"Directory changes detected, need to rescan")
                else:
                    # We have cache but no mod times, use cache anyway for speed
                    print(f"Using cached recent albums (no mod time comparison)")
                    return recent_albums_cache[:limit]
            
    except Exception as e:
        print(f"Cache check failed, falling back to normal scan: {e}")
        pass  # Fall through to normal scan
    
    # Normal scan (existing logic) - runs if no cache or changes detected
    
    client = connect_mpd_client()
    if not client:
        return []
    
    start_time = time.time()
    
    try:
        print(f"Getting recent albums from configured directories: {directories_to_check}")
        
        all_albums_dict = {}
        
        for directory in directories_to_check:
            try:
                print(f"Scanning {directory} directory...")
                dir_files = client.listallinfo(directory)
                
                if not dir_files:
                    print(f"No files found in '{directory}' directory")
                    continue
                
                print(f"Found {len(dir_files)} total items in '{directory}' directory")
                
                # Count music files vs other items
                music_files = [item for item in dir_files if 'file' in item and 'album' in item]
                print(f"Found {len(music_files)} music files with album info in '{directory}'")
                
                # Group files by album
                for song in dir_files:
                    # Skip non-music files
                    if 'file' not in song or 'album' not in song:
                        continue
                    
                    # Handle album field which can be a string or list
                    album_field = song.get('album', '')
                    if isinstance(album_field, list):
                        album_name = album_field[0] if album_field else ''
                    else:
                        album_name = str(album_field).strip()
                    
                    if not album_name:
                        continue
                    
                    # Create unique key with directory prefix to avoid conflicts
                    album_key = f"{directory}::{album_name}"
                    
                    # Group by album
                    if album_key not in all_albums_dict:
                        # Prefer AlbumArtist over Artist for grouping (handles compilations properly)
                        albumartist_field = song.get('albumartist')
                        artist_field = song.get('artist', 'Unknown Artist')
                        
                        # Use AlbumArtist if available, otherwise fall back to Artist
                        if albumartist_field:
                            artist_field = albumartist_field
                        
                        original_artist_field = artist_field  # Store original for MPD searches
                        
                        if isinstance(artist_field, list):
                            artist_name = ', '.join(artist_field)
                            # For MPD searches, use the first artist in the list
                            original_artist_name = artist_field[0] if artist_field else 'Unknown Artist'
                        else:
                            artist_name = str(artist_field)
                            original_artist_name = str(artist_field)
                        
                        all_albums_dict[album_key] = {
                            'album': album_name,
                            'artist': artist_name,
                            'original_artist': original_artist_name,  # Single artist for MPD search
                            'date': song.get('last-modified', ''),
                            'genre': song.get('genre', 'Unknown Genre'),
                            'songs': [song],
                            'sample_file': song.get('file', ''),
                            'source_dir': directory
                        }
                    else:
                        # Keep the newest modification date for the album
                        song_date = song.get('last-modified', '')
                        if song_date > all_albums_dict[album_key]['date']:
                            all_albums_dict[album_key]['date'] = song_date
                        all_albums_dict[album_key]['songs'].append(song)
                
                print(f"Found {len([k for k in all_albums_dict.keys() if k.startswith(directory)])} albums in '{directory}' directory")
                
            except Exception as e:
                print(f"Error accessing '{directory}' directory: {e}")
                continue
        
        if not all_albums_dict:
            print("No albums found in any recent directories")
            return []
        
        print(f"Total: {len(all_albums_dict)} albums found across all directories")
        
        # Convert to final format with duration calculations
        album_info_list = []
        
        for album_key, album_data in all_albums_dict.items():
            # ========================================================================
            # MULTI-DISC DETECTION: Check if album has multiple discs
            # Organize by disc but keep as single album entry
            # ========================================================================
            disc_structure = organize_album_by_disc(album_data['songs'])
            
            # Calculate total duration for all tracks
            total_duration = 0
            for song in album_data['songs']:
                if 'time' in song:
                    try:
                        total_duration += int(song['time'])
                    except (ValueError, TypeError):
                        pass
            
            # Format duration
            hours = total_duration // 3600
            minutes = (total_duration % 3600) // 60
            seconds = total_duration % 60
            if hours > 0:
                duration_formatted = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_formatted = f"{minutes}:{seconds:02d}"
            
            # Add source directory to artist display for clarity, but keep original for searching
            artist_display = f"{album_data['artist']} [{album_data['source_dir']}]"
            
            # Build album info - include disc structure if multi-disc
            album_info = {
                'album': album_data['album'],
                'artist': artist_display,           # For display in UI
                'original_artist': album_data['original_artist'],  # Single artist for MPD searches
                'genre': album_data.get('genre', 'Unknown Genre'),
                'date': album_data['date'],
                'file_count': len(album_data['songs']),
                'duration': total_duration,
                'duration_formatted': duration_formatted,
                'sample_file': album_data['sample_file'],
                'songs': album_data['songs'],  # All songs for the album
                'disc_structure': disc_structure if disc_structure else None,  # Disc organization
                'is_multi_disc': bool(disc_structure and len(disc_structure) > 1)  # Flag for multi-disc
            }
            
            if disc_structure:
                print(f"[DISC] Album '{album_data['album']}' has {len(disc_structure)} discs")
            
            album_info_list.append(album_info)
        
        # Sort by date (most recent first) and return limited results
        recent_albums = sorted(album_info_list, key=lambda x: x['date'], reverse=True)
        client.disconnect()
        
        # Update cache with new results
        try:
            recent_albums_cache = recent_albums
            recent_albums_cache_mod_times = current_mod_times if 'current_mod_times' in locals() else None
            print(f"Cache updated with {len(recent_albums)} albums")
        except:
            pass  # Cache update failure doesn't break anything
        
        elapsed = time.time() - start_time
        print(f"Found {len(recent_albums)} total albums in {elapsed:.2f} seconds, returning top {limit}")
        return recent_albums[:limit]
        
    except Exception as e:
        import traceback
        print(f"Error in get_recent_albums_from_mpd: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        if client:
            client.disconnect()
        return []


# SocketIO Events
@socketio.on('connect')
def test_connect():
    print('Client connected')
    # When a client connects, send them the current MPD status immediately
    status = get_mpd_status_for_display()
    if status:
        emit('mpd_status', status)
    # Also send auto-fill status to new connections
    emit('auto_fill_status', {
        'active': auto_fill_active,
        'min_queue_length': auto_fill_min_queue_length,
        'num_tracks_min': auto_fill_num_tracks_min,
        'num_tracks_max': auto_fill_num_tracks_max,
        'genre_filter_enabled': auto_fill_genre_filter_enabled,
        'genre_station_mode': genre_station_mode,
        'genre_station_name': genre_station_name,
        'genre_station_genres': genre_station_genres
    })

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

# --- Browse Database Routes ---
@app.route('/browse')
def browse_genres_page():
    """Browse genres page."""
    app_ctx = {}
    return browse_genres_page_handler(app_ctx)

@app.route('/browse/artists')
def browse_artists_page():
    """Browse artists page."""
    app_ctx = {}
    return browse_artists_page_handler(app_ctx)

@app.route('/browse/albums')
def browse_albums_page():
    """Browse albums page."""
    app_ctx = {}
    return browse_albums_page_handler(app_ctx)

@app.route('/bandcamp')
def bandcamp_page():
    """Bandcamp browse page."""
    return render_template('bandcamp.html')

# --- Browse Database API Endpoints ---
@app.route('/api/browse/genres', methods=['GET'])
def api_browse_genres():
    """Return all genres - simple fast version without counting."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client
    }
    return api_browse_genres_handler(app_ctx)

@app.route('/debug/albumartists')
def debug_albumartists():
    """Debug route to see what AlbumArtist values MPD has."""
    app_ctx = {'connect_mpd_client': connect_mpd_client}
    return debug_albumartists_handler(app_ctx)


@app.route('/debug/album/<album_name>')
def debug_album(album_name):
    """Debug specific album to see its Artist vs AlbumArtist tags."""
    app_ctx = {'connect_mpd_client': connect_mpd_client}
    return debug_album_handler(app_ctx, album_name)


@app.route('/debug/album_genre/<album_name>')
def debug_album_genre(album_name):
    """Debug what genre(s) an album is tagged with."""
    app_ctx = {'connect_mpd_client': connect_mpd_client}
    return debug_album_genre_handler(app_ctx, album_name)


@app.route('/debug/album_search/<search_term>')
def debug_album_search(search_term):
    """Debug albums containing a search term to see their tags."""
    app_ctx = {'connect_mpd_client': connect_mpd_client}
    return debug_album_search_handler(app_ctx, search_term)


@app.route('/debug/genre_various_artists/<genre_name>')
def debug_genre_various_artists(genre_name):
    """Debug which Various Artists albums are in a specific genre."""
    app_ctx = {'connect_mpd_client': connect_mpd_client}
    return debug_genre_various_artists_handler(app_ctx, genre_name)

@app.route('/api/browse/artists', methods=['GET'])
def api_browse_artists():
    """Return artists for a specific genre - simple fast version."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client
    }
    return api_browse_artists_handler(app_ctx)

@app.route('/api/browse/albums', methods=['GET'])
def api_browse_albums():
    """Return albums for a specific artist with track counts - uses AlbumArtist when available."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client
    }
    return api_browse_albums_handler(app_ctx)

# --- API endpoint for album tracks (for Show Tracks button) ---
@app.route('/api/album_tracks', methods=['GET'])
def api_album_tracks():
    """Return all tracks for a given album and artist as JSON."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'organize_album_by_disc': organize_album_by_disc
    }
    return api_album_tracks_handler(app_ctx)

# --- SocketIO Event Handlers ---
@socketio.on('connect')
def on_connect():
    """Handle client connection."""
    print(f"Client connected: {request.sid}")
    # Send current status immediately upon connection
    status = get_mpd_status_for_display()
    if status:
        emit('mpd_status', status)

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection."""
    print(f"Client disconnected: {request.sid}")

# ============================================================================
# LMS (LOGITECH MEDIA SERVER) API ROUTES
# ============================================================================

def get_lms_client():
    """Get LMS client instance from settings"""
    try:
        from lms_client import create_lms_client
        settings = load_settings()
        return create_lms_client(settings)
    except ImportError:
        return None
    except Exception as e:
        print(f"Error creating LMS client: {e}")
        return None

@app.route('/api/lms/players')
def api_lms_players():
    """Get list of available Squeezebox players."""
    app_ctx = {'get_lms_client': get_lms_client}
    return api_lms_players_handler(app_ctx)

@app.route('/api/lms/sync', methods=['POST'])
def api_lms_sync():
    """Sync MPD stream to selected Squeezebox players."""
    app_ctx = {
        'get_lms_client': get_lms_client,
        'request': request
    }
    return api_lms_sync_handler(app_ctx)

@app.route('/api/lms/unsync', methods=['POST'])
def api_lms_unsync():
    """Stop streaming on selected Squeezebox players."""
    app_ctx = {'get_lms_client': get_lms_client}
    return api_lms_unsync_handler(app_ctx)

@app.route('/api/lms/status')
def api_lms_status():
    """Get LMS enabled status and player information."""
    app_ctx = {
        'load_settings': load_settings,
        'get_lms_client': get_lms_client
    }
    return api_lms_status_handler(app_ctx)

@app.route('/api/lms/volume', methods=['POST'])
def api_lms_volume():
    """Set volume on a Squeezebox player."""
    app_ctx = {'get_lms_client': get_lms_client}
    return api_lms_volume_handler(app_ctx)

# ============================================================================
# BANDCAMP INTEGRATION
# ============================================================================

# ============================================================================
# BANDCAMP INTEGRATION
# ============================================================================

@app.route('/api/bandcamp/collection')
def bandcamp_collection():
    """Get user's Bandcamp collection."""
    app_ctx = {'bandcamp_service': bandcamp_service}
    return bandcamp_collection_handler(app_ctx)

@app.route('/api/bandcamp/album/<int:album_id>')
def bandcamp_album(album_id):
    """Get album details including tracks."""
    app_ctx = {'bandcamp_service': bandcamp_service}
    return bandcamp_album_handler(app_ctx, album_id)

@app.route('/api/bandcamp/add_track', methods=['POST'])
def bandcamp_add_track():
    """Add Bandcamp track to MPD playlist."""
    app_ctx = {
        'connect_mpd_client': connect_mpd_client,
        'bandcamp_service': bandcamp_service
    }
    return bandcamp_add_track_handler(app_ctx)

@app.route('/api/bandcamp/artwork/<int:art_id>')
def bandcamp_artwork(art_id):
    """Proxy Bandcamp artwork."""
    app_ctx = {'bandcamp_service': bandcamp_service}
    return bandcamp_artwork_handler(app_ctx, art_id)

# --- Application Startup ---
if __name__ == '__main__':
    print(f"[INFO] {APP_NAME} v{APP_VERSION} (Build: {APP_BUILD_DATE})")
    print("[DEBUG] app.py loaded and running")
    
    # Start background monitoring threads
    socketio.start_background_task(target=mpd_status_monitor)
    socketio.start_background_task(target=auto_fill_monitor)
    
    # Get configuration from environment or use defaults
    if ENV_LOADED:
        app_host = os.environ.get('APP_HOST', '0.0.0.0')
        app_port = int(os.environ.get('APP_PORT', '5003'))
        debug_mode = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes', 'on')
    else:
        app_host = '0.0.0.0'
        app_port = 5003
        debug_mode = False
    
    print(f"Starting MPD Web Control on {app_host}:{app_port}")
    
    # Run the application
    socketio.run(app, host=app_host, port=app_port, debug=debug_mode, allow_unsafe_werkzeug=True)