"""
Utility route handlers for Maestro Server.

Handles:
- API version and settings info
- Auto-fill configuration and status
- Recent albums retrieval
- Music directory browser
"""

import os
from flask import jsonify, render_template, request


# ============================================================================
# Utility Routes
# ============================================================================

def get_version_info_handler(app_ctx):
    """Get API version and application info."""
    APP_NAME = app_ctx['APP_NAME']
    APP_VERSION = app_ctx['APP_VERSION']
    APP_BUILD_DATE = app_ctx['APP_BUILD_DATE']
    
    return jsonify({
        'app_name': APP_NAME,
        'version': APP_VERSION,
        'build_date': APP_BUILD_DATE,
        'status': 'running'
    })


def get_settings_info_handler(app_ctx):
    """Get public settings info (no sensitive data)."""
    load_settings = app_ctx['load_settings']
    
    settings = load_settings()
    return jsonify({
        'bandcamp_enabled': settings.get('bandcamp_enabled', False),
        'bandcamp_username': settings.get('bandcamp_username', ''),
        'bandcamp_identity_token': bool(settings.get('bandcamp_identity_token', '').strip()),
        'lms_enabled': settings.get('lms_enabled', False),
        'hide_volume_controls': settings.get('hide_volume_controls', False)
    })


def get_auto_fill_status_handler(app_ctx):
    """Get current auto-fill status and configuration."""
    return jsonify({
        'active': app_ctx.get('auto_fill_active', False),
        'min_queue_length': app_ctx.get('auto_fill_min_queue_length', 5),
        'num_tracks_min': app_ctx.get('auto_fill_num_tracks_min', 10),
        'num_tracks_max': app_ctx.get('auto_fill_num_tracks_max', 50),
        'genre_filter_enabled': app_ctx.get('auto_fill_genre_filter_enabled', False),
        'genre_station_mode': app_ctx.get('genre_station_mode', False),
        'genre_station_name': app_ctx.get('genre_station_name', ''),
        'genre_station_genres': app_ctx.get('genre_station_genres', [])
    })


def toggle_auto_fill_handler(app_ctx):
    """Toggle auto-fill on/off - returns data only, wrapper handles state update."""
    socketio = app_ctx['socketio']
    data = request.get_json()
    new_state = data.get('active')
    
    if isinstance(new_state, bool):
        status_text = "enabled" if new_state else "disabled"
        socketio.emit('server_message', {'type': 'info', 'text': f'Auto-fill has been {status_text}.'})
        return jsonify({'status': 'success', 'active': new_state})
    
    return jsonify({'status': 'error', 'message': 'Invalid state'}), 400


def set_auto_fill_settings_handler(app_ctx):
    """Update auto-fill settings - returns data only, wrapper handles state update."""
    socketio = app_ctx['socketio']
    data = request.get_json()

    try:
        # Validate inputs
        min_queue = int(data.get('min_queue_length', app_ctx.get('auto_fill_min_queue_length', 5)))
        num_min = int(data.get('num_tracks_min', app_ctx.get('auto_fill_num_tracks_min', 10)))
        num_max = int(data.get('num_tracks_max', app_ctx.get('auto_fill_num_tracks_max', 50)))
        genre_filter = bool(data.get('genre_filter_enabled', app_ctx.get('auto_fill_genre_filter_enabled', False)))

        socketio.emit('server_message', {'type': 'info', 'text': 'Auto-fill settings updated.'})
        
        return jsonify({
            'status': 'success',
            'min_queue_length': min_queue,
            'num_tracks_min': num_min,
            'num_tracks_max': num_max,
            'genre_filter_enabled': genre_filter
        })
    except ValueError:
        socketio.emit('server_message', {'type': 'error', 'text': 'Invalid auto-fill settings provided.'})
        return jsonify({'status': 'error'}), 400


def recent_albums_handler(app_ctx):
    """Get recently added albums from MPD database."""
    get_recent_albums_from_mpd = app_ctx['get_recent_albums_from_mpd']
    
    try:
        force_refresh = (request.args.get('force', '0') == '1' or 
                        request.args.get('force_refresh', '0') == '1')
        recent_albums_data = get_recent_albums_from_mpd(force_refresh=force_refresh)
        return jsonify({
            'status': 'success',
            'albums': recent_albums_data,
            'count': len(recent_albums_data)
        })
    except Exception as e:
        print(f"Error getting recent albums: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving recent albums: {str(e)}',
            'albums': []
        }), 500


def recent_albums_page_handler(app_ctx):
    """Display the recent albums page."""
    return render_template('recent_albums.html')


def list_music_directories_handler(app_ctx):
    """List available directories within the music library for recent albums browsing."""
    try:
        path = request.args.get('path', '/media/music')
        
        # Security: Only allow browsing within standard music directories
        allowed_root_paths = ['/media/music', '/var/lib/mpd/music', '/mnt/music']
        
        # Validate path is within allowed roots
        if not any(path.startswith(root) for root in allowed_root_paths):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Check if directory exists
        if not os.path.isdir(path):
            return jsonify({'success': False, 'error': f'Directory not found: {path}'}), 404
        
        items = []
        try:
            for entry in os.scandir(path):
                if entry.is_dir(follow_symlinks=False):
                    try:
                        item = {
                            'name': entry.name,
                            'path': entry.path,
                            'is_dir': True,
                            'modified': entry.stat().st_mtime
                        }
                        items.append(item)
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError) as e:
            print(f"Error listing directory {path}: {e}")
        
        # Sort alphabetically
        items.sort(key=lambda x: x['name'].lower())
        
        # Determine parent directory
        parent = None
        if path not in allowed_root_paths:
            parent_path = os.path.dirname(path)
            if any(parent_path.startswith(root) for root in allowed_root_paths):
                parent = parent_path
        
        return jsonify({
            'success': True,
            'path': path,
            'parent': parent,
            'items': items
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
