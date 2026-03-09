"""
Integration route handlers for Maestro Server.

Handles:
- Lyrics (Genius integration)
- Last.fm integration (OAuth, charts, scrobbling)
- Bandcamp integration
- LMS (Logitech Squeezebox) integration
"""

from flask import jsonify, request, render_template


# ============================================================================
# LYRICS HANDLERS
# ============================================================================

def api_get_lyrics_handler(app_ctx):
    """
    Fetch lyrics for a track (delegates to app.py helper functions)
    Expected JSON: {"artist": "...", "title": "..."}
    """
    _try_lyrics_providers = app_ctx['_try_lyrics_providers']
    _is_likely_instrumental = app_ctx['_is_likely_instrumental']
    
    data = request.get_json() or {}
    artist = data.get('artist', '').strip()
    title = data.get('title', '').strip()
    
    if not artist or not title:
        return jsonify({'status': 'error', 'message': 'Artist and title required'}), 400
    
    try:
        is_instrumental = _is_likely_instrumental(title)
        
        if is_instrumental:
            return jsonify({
                'status': 'success',
                'lyrics': None,
                'message': f'🎼 Instrumental Track: "{title}" appears to be an instrumental piece. No lyrics available.'
            })
        
        lyrics = _try_lyrics_providers(artist, title)
        
        if lyrics:
            return jsonify({
                'status': 'success',
                'lyrics': lyrics,
                'artist': artist,
                'title': title
            })
        
        return jsonify({
            'status': 'success',
            'lyrics': None,
            'message': 'No lyrics found. This track may be instrumental, a live recording, or not available in our database.'
        })
        
    except Exception as e:
        print(f"Error fetching lyrics: {e}")
        return jsonify({
            'status': 'success',
            'lyrics': None,
            'message': 'Could not retrieve lyrics at this time. Please try again later.'
        })


def api_test_genius_handler(app_ctx):
    """Quick check that Genius search + scrape works."""
    _fetch_lyrics_genius = app_ctx['_fetch_lyrics_genius']
    
    try:
        artist = request.form.get('artist', 'The Beatles')
        title = request.form.get('title', 'Hey Jude')
        lyrics = _fetch_lyrics_genius(artist, title)
        if lyrics:
            snippet = (lyrics[:160] + '...') if len(lyrics) > 160 else lyrics
            return jsonify({'status': 'success', 'message': 'Genius reachable and returned lyrics.', 'snippet': snippet})
        return jsonify({'status': 'error', 'message': 'No lyrics returned. Verify track spelling or try another song.'}), 502
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Genius test failed: {e}'}), 502


# ============================================================================
# LAST.FM HANDLERS
# ============================================================================

def api_test_lastfm_handler(app_ctx):
    """Test Last.fm API connectivity."""
    LASTFM_API_KEY = app_ctx['LASTFM_API_KEY']
    LASTFM_API_URL = app_ctx['LASTFM_API_URL']
    DEFAULT_HTTP_HEADERS = app_ctx['DEFAULT_HTTP_HEADERS']
    
    import requests
    
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


def lastfm_request_token_handler(app_ctx):
    """Request Last.fm OAuth token."""
    lastfm_request_token = app_ctx['lastfm_request_token']
    load_settings = app_ctx['load_settings']
    save_settings = app_ctx['save_settings']
    LASTFM_API_KEY = app_ctx['LASTFM_API_KEY']
    LASTFM_AUTH_URL = app_ctx['LASTFM_AUTH_URL']
    
    try:
        token = lastfm_request_token()
        s = load_settings()
        s['lastfm_auth_token'] = token
        save_settings(s)
        auth_url = f"{LASTFM_AUTH_URL}?api_key={LASTFM_API_KEY}&token={token}"
        return jsonify({'status': 'success', 'auth_url': auth_url})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def lastfm_finalize_handler(app_ctx):
    """Finalize Last.fm OAuth and get session key."""
    lastfm_get_session = app_ctx['lastfm_get_session']
    load_settings = app_ctx['load_settings']
    save_settings = app_ctx['save_settings']
    
    try:
        s = load_settings()
        token = s.get('lastfm_auth_token', '')
        if not token:
            return jsonify({'status': 'error', 'message': 'No pending token. Request a token first.'}), 400
        sk = lastfm_get_session(token)
        s['lastfm_session_key'] = sk
        s['lastfm_auth_token'] = ''
        save_settings(s)
        return jsonify({'status': 'success', 'message': 'Last.fm connected successfully.'})
    except Exception as e:
        print(f"[Last.fm] Finalize error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def charts_page_handler(app_ctx):
    """Display the Last.fm charts page."""
    return render_template('charts.html')


def api_charts_handler(app_ctx, chart_type):
    """
    Return Last.fm user charts (artists, albums, or tracks).
    Query params: period (7day, 1month, 3month, 6month, 12month, overall)
    """
    lastfm_session_key = app_ctx['lastfm_session_key']
    lastfm_get_user_charts = app_ctx['lastfm_get_user_charts']
    
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


# ============================================================================
# BANDCAMP HANDLERS
# ============================================================================

def bandcamp_collection_handler(app_ctx):
    """Get user's Bandcamp collection."""
    bandcamp_service = app_ctx.get('bandcamp_service')
    
    try:
        if not bandcamp_service or not bandcamp_service.is_enabled:
            return jsonify({'status': 'error', 'message': 'Bandcamp not configured'}), 400
        
        collection = bandcamp_service.get_collection()
        return jsonify({
            'status': 'success',
            'albums': collection
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def bandcamp_album_handler(app_ctx, album_id):
    """Get album details including tracks."""
    bandcamp_service = app_ctx.get('bandcamp_service')
    
    try:
        if not bandcamp_service or not bandcamp_service.is_enabled:
            return jsonify({'status': 'error', 'message': 'Bandcamp not configured'}), 400
        
        album = bandcamp_service.get_album_info(album_id)
        if not album:
            return jsonify({'status': 'error', 'message': 'Album not found'}), 404
        
        return jsonify({
            'status': 'success',
            'album': album
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def bandcamp_add_track_handler(app_ctx):
    """Add Bandcamp track to MPD playlist."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    bandcamp_service = app_ctx.get('bandcamp_service')
    
    import re
    
    client = None
    try:
        data = request.json
        streaming_url = data.get('streaming_url')
        track_id = data.get('track_id')
        title = data.get('title', 'Unknown')
        artist = data.get('artist', 'Unknown')
        album = data.get('album', 'Unknown')
        artwork_url = data.get('artwork_url', '')
        
        if not streaming_url:
            return jsonify({'status': 'error', 'message': 'Streaming URL required'}), 400
        
        # Cache metadata through the service
        if bandcamp_service and bandcamp_service.is_enabled:
            bandcamp_service.cache_track_metadata(
                streaming_url=streaming_url,
                track_id=track_id,
                title=title,
                artist=artist,
                album=album,
                artwork_url=artwork_url
            )
        
        print(f"Cached Bandcamp metadata")
        print(f"  Track ID: {track_id}, Artist: {artist}, Title: {title}")
        print(f"  Album: {album}, Artwork: {artwork_url}", flush=True)
        
        client = connect_mpd_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'MPD connection failed'}), 500
        
        try:
            client.add(streaming_url)
            
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            
            return jsonify({
                'status': 'success',
                'message': f'Added {artist} - {title} to playlist'
            })
        except Exception as e:
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            return jsonify({'status': 'error', 'message': f'Failed to add track: {str(e)}'}), 500
            
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        return jsonify({'status': 'error', 'message': str(e)}), 500


def bandcamp_artwork_handler(app_ctx, art_id):
    """Proxy Bandcamp artwork."""
    bandcamp_service = app_ctx.get('bandcamp_service')
    
    try:
        if not bandcamp_service or not bandcamp_service.is_enabled:
            return '', 404
        
        size = request.args.get('size', '5')
        url = bandcamp_service.get_artwork_url(art_id, int(size))
        
        if not url:
            return '', 404
        
        import requests
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.content, 200, {'Content-Type': response.headers.get('content-type', 'image/jpeg')}
        return '', 404
    except Exception as e:
        print(f"Error proxying Bandcamp artwork: {e}")
        return '', 404



# ============================================================================
# LMS (LOGITECH SQUEEZEBOX) HANDLERS
# ============================================================================

def api_lms_players_handler(app_ctx):
    """Get list of available Squeezebox players."""
    get_lms_client = app_ctx['get_lms_client']
    
    try:
        client = get_lms_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'LMS not configured or unavailable'}), 400
        
        players = client.get_players()
        return jsonify({'status': 'success', 'players': players})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def api_lms_sync_handler(app_ctx):
    """Sync MPD stream to selected Squeezebox players."""
    get_lms_client = app_ctx['get_lms_client']
    
    try:
        data = request.json
        player_ids = data.get('players', [])
        
        if not player_ids:
            return jsonify({'status': 'error', 'message': 'No players selected'}), 400
        
        client = get_lms_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'LMS not configured'}), 400
        
        mpd_stream_url = f"http://{request.host.split(':')[0]}:8000"
        
        success_count = 0
        failed_players = []
        
        for player_id in player_ids:
            if client.play_url(player_id, mpd_stream_url):
                success_count += 1
            else:
                failed_players.append(player_id)
        
        if success_count > 0:
            message = f'Started streaming to {success_count} player(s)'
            if failed_players:
                message += f', {len(failed_players)} failed'
            return jsonify({'status': 'success', 'message': message})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to start streaming on any player'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def api_lms_unsync_handler(app_ctx):
    """Stop streaming on selected Squeezebox players."""
    get_lms_client = app_ctx['get_lms_client']
    
    try:
        data = request.json
        player_ids = data.get('players', [])
        
        if not player_ids:
            return jsonify({'status': 'error', 'message': 'No players selected'}), 400
        
        client = get_lms_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'LMS not configured'}), 400
        
        success_count = 0
        failed_players = []
        
        for player_id in player_ids:
            if client.stop(player_id):
                success_count += 1
            else:
                failed_players.append(player_id)
        
        if success_count > 0:
            message = f'Stopped streaming on {success_count} player(s)'
            if failed_players:
                message += f', {len(failed_players)} failed'
            return jsonify({'status': 'success', 'message': message})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to stop any player'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def api_lms_status_handler(app_ctx):
    """Get LMS enabled status and player information."""
    load_settings = app_ctx['load_settings']
    get_lms_client = app_ctx['get_lms_client']
    
    try:
        settings = load_settings()
        lms_enabled = settings.get('lms_enabled', False)
        
        if not lms_enabled:
            return jsonify({'status': 'success', 'enabled': False, 'players': []})
        
        client = get_lms_client()
        if not client:
            return jsonify({'status': 'success', 'enabled': True, 'available': False, 'players': []})
        
        players = client.get_players()
        return jsonify({
            'status': 'success',
            'enabled': True,
            'available': True,
            'players': players
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def api_lms_volume_handler(app_ctx):
    """Set volume on a Squeezebox player."""
    get_lms_client = app_ctx['get_lms_client']
    
    try:
        data = request.json
        player_id = data.get('player')
        volume = data.get('volume')
        
        if not player_id:
            return jsonify({'status': 'error', 'message': 'Player ID required'}), 400
        
        if volume is None or not (0 <= volume <= 100):
            return jsonify({'status': 'error', 'message': 'Volume must be between 0 and 100'}), 400
        
        client = get_lms_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'LMS not configured'}), 400
        
        if client.set_volume(player_id, volume):
            return jsonify({'status': 'success', 'message': f'Volume set to {volume}%'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to set volume'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
