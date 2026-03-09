"""
Radio route handlers for Maestro Server.

Handles:
- Genre stations (create, list, delete, manage modes)
- Streaming radio (test, detect country, list countries)
- Radio backup (download, status)
- Radio stations (list, play)
- Manual radio stations (list, save, remove)
"""

from flask import jsonify, request
import time


def get_genre_stations_handler(app_ctx):
    """Get all saved genre stations."""
    load_genre_stations = app_ctx['load_genre_stations']
    try:
        stations = load_genre_stations()
        return jsonify({'status': 'success', 'stations': stations})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error loading stations: {str(e)}'}), 500


def save_genre_station_handler(app_ctx):
    """Save a new genre station."""
    load_genre_stations = app_ctx['load_genre_stations']
    save_genre_stations = app_ctx['save_genre_stations']
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        station_name = data.get('name', '').strip()
        genres = data.get('genres', [])
        
        if not station_name:
            return jsonify({'status': 'error', 'message': 'Station name is required'}), 400
        
        if not genres or not isinstance(genres, list):
            return jsonify({'status': 'error', 'message': 'At least one genre is required'}), 400
        
        # Load existing stations
        stations = load_genre_stations()
        
        # Add new station
        stations[station_name] = {
            'genres': genres,
            'created': int(time.time())
        }
        
        # Save stations
        if save_genre_stations(stations):
            return jsonify({'status': 'success', 'message': f'Station "{station_name}" saved'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to save station'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error saving station: {str(e)}'}), 500


def get_genre_station_handler(app_ctx, station_name):
    """Get a specific genre station."""
    load_genre_stations = app_ctx['load_genre_stations']
    
    try:
        stations = load_genre_stations()
        
        if station_name not in stations:
            return jsonify({'status': 'error', 'message': 'Station not found'}), 404
        
        return jsonify({'status': 'success', 'station': stations[station_name]})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error loading station: {str(e)}'}), 500


def delete_genre_station_handler(app_ctx, station_name):
    """Delete a genre station."""
    load_genre_stations = app_ctx['load_genre_stations']
    save_genre_stations = app_ctx['save_genre_stations']
    
    try:
        stations = load_genre_stations()
        
        if station_name not in stations:
            return jsonify({'status': 'error', 'message': 'Station not found'}), 404
        
        del stations[station_name]
        
        if save_genre_stations(stations):
            return jsonify({'status': 'success', 'message': f'Station "{station_name}" deleted'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to delete station'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error deleting station: {str(e)}'}), 500


def set_genre_station_mode_handler(app_ctx):
    """Set genre station mode for auto-fill."""
    # Note: genre_station_mode, genre_station_name, genre_station_genres are globals
    # that need to be updated in app.py
    try:
        data = request.get_json()
        station_name = data.get('station_name', '')
        genres = data.get('genres', [])
        
        if station_name and genres:
            return jsonify({
                'status': 'success', 
                'message': f'Genre station mode set to "{station_name}"',
                'action': 'set_mode',
                'station_name': station_name,
                'genres': genres
            })
        else:
            return jsonify({
                'status': 'success', 
                'message': 'Genre station mode cleared',
                'action': 'clear_mode'
            })
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error setting genre station mode: {str(e)}'}), 500


def test_streaming_radio_handler(app_ctx):
    """Test internet radio streaming by playing a stream URL."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    socketio = app_ctx['socketio']
    get_mpd_status_for_display = app_ctx['get_mpd_status_for_display']
    
    try:
        data = request.get_json()
        stream_url = data.get('url', '').strip()
        
        if not stream_url:
            return jsonify({'status': 'error', 'message': 'Stream URL is required'}), 400
        
        if not stream_url.startswith(('http://', 'https://')):
            return jsonify({'status': 'error', 'message': 'Invalid URL. Must start with http:// or https://'}), 400
        
        client = connect_mpd_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
        
        try:
            client.clear()
            client.add(stream_url)
            client.play(0)
            
            socketio.emit('server_message', {
                'type': 'success',
                'text': f'🔴 LIVE: Tuned into stream'
            })
            
            socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
            
            return jsonify({'status': 'success', 'message': 'Stream started'})
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'MPD error: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def detect_radio_country_handler(app_ctx):
    """Detect user's country from IP address for radio station defaults."""
    import requests
    
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip:
            response = requests.get(f'https://ipapi.co/{ip}/country/', timeout=3)
            if response.status_code == 200:
                country_code = response.text.strip()
                return jsonify({'country': country_code})
        
        return jsonify({'country': 'US'})
    except Exception as e:
        print(f"Country detection error: {e}")
        return jsonify({'country': 'US'})


def get_radio_countries_handler(app_ctx):
    """Get list of countries with radio stations."""
    countries = [
        {'code': 'US', 'name': 'United States', 'flag': '🇺🇸'},
        {'code': 'GB', 'name': 'United Kingdom', 'flag': '🇬🇧'},
        {'code': 'IT', 'name': 'Italy', 'flag': '🇮🇹'},
        {'code': 'DE', 'name': 'Germany', 'flag': '🇩🇪'},
        {'code': 'FR', 'name': 'France', 'flag': '🇫🇷'},
        {'code': 'ES', 'name': 'Spain', 'flag': '🇪🇸'},
        {'code': 'PT', 'name': 'Portugal', 'flag': '🇵🇹'},
        {'code': 'CA', 'name': 'Canada', 'flag': '🇨🇦'},
        {'code': 'AU', 'name': 'Australia', 'flag': '🇦🇺'},
        {'code': 'NL', 'name': 'Netherlands', 'flag': '🇳🇱'},
        {'code': 'BR', 'name': 'Brazil', 'flag': '🇧🇷'},
        {'code': 'MX', 'name': 'Mexico', 'flag': '🇲🇽'},
        {'code': 'JP', 'name': 'Japan', 'flag': '🇯🇵'},
        {'code': 'KR', 'name': 'South Korea', 'flag': '🇰🇷'},
        {'code': 'SE', 'name': 'Sweden', 'flag': '🇸🇪'},
        {'code': 'NO', 'name': 'Norway', 'flag': '🇳🇴'},
        {'code': 'DK', 'name': 'Denmark', 'flag': '🇩🇰'},
        {'code': 'FI', 'name': 'Finland', 'flag': '🇫🇮'},
        {'code': 'PL', 'name': 'Poland', 'flag': '🇵🇱'},
        {'code': 'RU', 'name': 'Russia', 'flag': '🇷🇺'},
        {'code': 'IN', 'name': 'India', 'flag': '🇮🇳'},
    ]
    return jsonify(countries)


def download_radio_backup_handler(app_ctx):
    """Download the latest radio browser backup database."""
    import os
    import requests
    
    # These would be defined in app.py
    BACKUP_DB_URL = app_ctx.get('BACKUP_DB_URL', '')
    BACKUP_DB_FILE = app_ctx.get('BACKUP_DB_FILE', '')
    load_backup_database = app_ctx.get('load_backup_database')
    
    if not BACKUP_DB_URL or not BACKUP_DB_FILE:
        return jsonify({'status': 'error', 'message': 'Backup not configured'}), 400
    
    try:
        print(f"Downloading radio backup database from {BACKUP_DB_URL}")
        
        response = requests.get(BACKUP_DB_URL, timeout=60, stream=True)
        
        if response.status_code == 200:
            with open(BACKUP_DB_FILE, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size_mb = os.path.getsize(BACKUP_DB_FILE) / (1024 * 1024)
            print(f"Downloaded backup database: {file_size_mb:.1f} MB")
            
            if load_backup_database:
                stations = load_backup_database()
                if stations:
                    return jsonify({
                        'status': 'success',
                        'message': f'Downloaded backup with {len(stations)} stations',
                        'size_mb': round(file_size_mb, 1),
                        'stations_count': len(stations)
                    })
            
            return jsonify({'status': 'error', 'message': 'Downloaded but failed to parse'}), 500
        else:
            return jsonify({'status': 'error', 'message': f'Download failed: HTTP {response.status_code}'}), 500
            
    except Exception as e:
        print(f"Error downloading backup: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def get_backup_status_handler(app_ctx):
    """Check if backup database exists and get its info."""
    import os
    import time
    
    BACKUP_DB_FILE = app_ctx.get('BACKUP_DB_FILE', '')
    load_backup_database = app_ctx.get('load_backup_database')
    
    if not BACKUP_DB_FILE:
        return jsonify({'exists': False, 'message': 'Backup not configured'}), 400
    
    try:
        if os.path.exists(BACKUP_DB_FILE):
            file_age_days = (time.time() - os.path.getmtime(BACKUP_DB_FILE)) / 86400
            file_size_mb = os.path.getsize(BACKUP_DB_FILE) / (1024 * 1024)
            
            station_count = 0
            if load_backup_database:
                stations = load_backup_database()
                station_count = len(stations) if stations else 0
            
            return jsonify({
                'exists': True,
                'age_days': round(file_age_days, 1),
                'size_mb': round(file_size_mb, 1),
                'stations_count': station_count,
                'file_path': BACKUP_DB_FILE
            })
        else:
            return jsonify({
                'exists': False,
                'message': 'No backup database found. Click "Download Backup" to get one.'
            })
    except Exception as e:
        return jsonify({'exists': False, 'error': str(e)}), 500


def get_radio_stations_handler(app_ctx):
    """Get radio stations from Radio Browser API with country filtering."""
    radio_stations_cache = app_ctx.get('radio_stations_cache', {})
    CACHE_DURATION = app_ctx.get('CACHE_DURATION', 3600)
    load_backup_database = app_ctx.get('load_backup_database')
    
    try:
        country = request.args.get('country', 'US')
        limit = request.args.get('limit', '50')
        name_search = request.args.get('name', '')
        bypass_cache = request.args.get('nocache', None)
        
        cache_key = f"{country}:{name_search}:{limit}"
        
        # Check cache first
        if not bypass_cache:
            import time
            current_time = time.time()
            if cache_key in radio_stations_cache:
                cached_data, cache_time = radio_stations_cache[cache_key]
                if current_time - cache_time < CACHE_DURATION:
                    print(f"[Radio API] Returning cached response for {cache_key}")
                    return jsonify(cached_data)
        
        # Query Radio Browser API with country filter
        import requests
        import random
        
        print(f"[Radio API] Fetching stations for country: {country}")
        
        # Radio Browser API servers
        api_servers = [
            'https://de1.api.radio-browser.info',
            'https://nl1.api.radio-browser.info',
            'https://at1.api.radio-browser.info'
        ]
        random.shuffle(api_servers)
        
        # Build endpoint based on search type
        if name_search:
            endpoint = f'/json/stations/byname/{requests.utils.quote(name_search)}'
            params = {
                'limit': limit,
                'hidebroken': 'true'
            }
        else:
            # Get stations by country code (properly filtered!)
            endpoint = f'/json/stations/bycountrycodeexact/{country}'
            params = {
                'limit': limit,
                'order': 'votes',
                'reverse': 'true',
                'hidebroken': 'true'
            }
        
        last_error = None
        stations = []
        
        # Try each API server
        for api_server in api_servers:
            try:
                api_url = api_server + endpoint
                response = requests.get(api_url, params=params, timeout=7, headers={'User-Agent': 'Maestro-MPD'})
                
                if response.status_code == 200:
                    stations = response.json()
                    print(f"[Radio API] Successfully fetched {len(stations)} stations for {country}")
                    break
                else:
                    last_error = f"API returned {response.status_code}"
                    
            except requests.exceptions.Timeout:
                last_error = "Request timeout"
            except requests.exceptions.RequestException as e:
                last_error = str(e)
        
        # If API fails, fall back to backup database
        if not stations and load_backup_database:
            print(f"[Radio API] All servers failed, trying backup database")
            backup_stations = load_backup_database()
            if backup_stations:
                # Filter the backup by country (since API failed)
                filter_func = app_ctx.get('filter_backup_stations')
                if filter_func:
                    stations = filter_func(backup_stations, country=country, name_search=name_search, limit=int(limit))
                else:
                    # Manual filter if function not available
                    filtered = []
                    for station in backup_stations:
                        if station.get('iso_3166_1', '').upper() != country.upper():
                            continue
                        if name_search and name_search.lower() not in station.get('name', '').lower():
                            continue
                        filtered.append({
                            'name': station.get('name', 'Unknown'),
                            'url_stream': station.get('url_stream', station.get('url_resolved', '')),
                            'url_favicon': station.get('url_favicon', ''),
                            'tags': station.get('tags', ''),
                            'iso_3166_1': station.get('iso_3166_1', ''),
                            'bitrate': station.get('bitrate', 0)
                        })
                        if len(filtered) >= int(limit):
                            break
                    stations = filtered
        
        if not stations:
            error_msg = last_error or 'No stations available'
            return jsonify({
                'status': 'error',
                'message': f'Failed to fetch stations: {error_msg}',
                'stations': [],
                'count': 0
            }), 503
        
        # Format response
        response = {
            'status': 'success',
            'stations': stations if isinstance(stations, list) else [stations],
            'count': len(stations) if isinstance(stations, list) else 1
        }
        
        # Cache the response
        import time
        radio_stations_cache[cache_key] = (response, time.time())
        
        return jsonify(response)
        
    except Exception as e:
        print(f"[Radio API] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e), 'stations': [], 'count': 0}), 500


def play_radio_station_handler(app_ctx):
    """Play a radio station by clearing queue and adding stream."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    socketio = app_ctx['socketio']
    get_mpd_status_for_display = app_ctx['get_mpd_status_for_display']
    stream_favicon_cache = app_ctx.get('stream_favicon_cache', {})
    stream_name_cache = app_ctx.get('stream_name_cache', {})
    
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        name = data.get('name', 'Radio Station')
        favicon = data.get('favicon', '').strip()
        
        if not url:
            return jsonify({'status': 'error', 'message': 'URL required'}), 400
        
        if not url.startswith(('http://', 'https://')):
            return jsonify({'status': 'error', 'message': 'Invalid URL'}), 400
        
        if favicon and favicon.startswith('http'):
            stream_favicon_cache[url] = favicon
            print(f"Cached favicon for {url}: {favicon}")
        
        if name:
            stream_name_cache[url] = name
            print(f"Cached station name for {url}: {name}")
        
        client = connect_mpd_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
        
        try:
            client.clear()
            client.add(url)
            client.play(0)
            
            socketio.emit('server_message', {
                'type': 'success',
                'text': f'📻 Now playing: {name}'
            })
            
            socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
            
            return jsonify({'status': 'success', 'message': f'Playing {name}'})
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'MPD error: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def get_manual_stations_handler(app_ctx):
    """Get list of manually added radio stations."""
    load_manual_stations = app_ctx['load_manual_stations']
    
    try:
        stations = load_manual_stations()
        return jsonify(stations)
    except Exception as e:
        print(f"Error listing manual stations: {e}")
        return jsonify({'error': str(e)}), 500


def save_manual_station_handler(app_ctx):
    """Save a manually added radio station."""
    add_manual_station = app_ctx['add_manual_station']
    
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        url = data.get('url', '').strip()
        favicon = data.get('favicon', '').strip()
        
        if not name:
            return jsonify({'status': 'error', 'message': 'Station name required'}), 400
        if not url:
            return jsonify({'status': 'error', 'message': 'Station URL required'}), 400
        
        if not url.startswith(('http://', 'https://')):
            return jsonify({'status': 'error', 'message': 'Invalid URL - must start with http:// or https://'}), 400
        
        success, message = add_manual_station(name, url, favicon)
        if success:
            return jsonify({'status': 'success', 'message': message})
        else:
            return jsonify({'status': 'error', 'message': message}), 400
            
    except Exception as e:
        print(f"Error saving manual station: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def remove_manual_station_handler(app_ctx):
    """Remove a manually added station by URL."""
    remove_manual_station = app_ctx['remove_manual_station']
    
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'status': 'error', 'message': 'URL required'}), 400
        
        success, message = remove_manual_station(url)
        if success:
            return jsonify({'status': 'success', 'message': message})
        else:
            return jsonify({'status': 'error', 'message': message}), 404
            
    except Exception as e:
        print(f"Error removing manual station: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
