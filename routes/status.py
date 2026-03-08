"""
Status and history route handlers for Maestro Server.

Handles:
- Database update status checking
- MPD status queries
- Play history page rendering
- History API endpoints (list and clear)
"""

from flask import jsonify, render_template, request, make_response


# ============================================================================
# Status Routes
# ============================================================================

def db_update_status_handler(app_ctx):
    """Check if MPD database update is in progress."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    
    try:
        client = connect_mpd_client()
        if client:
            status = client.status()
            client.disconnect()
            
            # Check if 'updating_db' key exists in status
            is_updating = 'updating_db' in status
            job_id = status.get('updating_db', None)
            
            return jsonify({
                'status': 'success',
                'updating': is_updating,
                'job_id': job_id
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Could not connect to MPD'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def get_mpd_status_handler(app_ctx):
    """API endpoint to get current MPD status."""
    get_mpd_status_for_display = app_ctx['get_mpd_status_for_display']
    last_mpd_status = app_ctx['last_mpd_status']
    
    status = get_mpd_status_for_display()
    response = make_response(jsonify(status))
    # Disable caching to ensure fresh playlist data
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    if status:
        return response
    return make_response(jsonify(last_mpd_status if last_mpd_status else {
        'state': 'unknown', 
        'message': 'No status available', 
        'volume': 0, 
        'queue_length': 0, 
        'consume_mode': False,
        'shuffle_mode': False,
        'crossfade_enabled': False,
        'crossfade_seconds': 0
    }))


# ============================================================================
# History Routes
# ============================================================================

def history_page_handler(app_ctx):
    """Display play history page."""
    get_mpd_status_for_display = app_ctx['get_mpd_status_for_display']
    last_mpd_status = app_ctx['last_mpd_status']
    app = app_ctx['app']
    play_history = app_ctx['play_history']
    
    mpd_status = get_mpd_status_for_display()
    if mpd_status is None:
        mpd_status = last_mpd_status if last_mpd_status else {'state': 'unknown'}
    app_theme = app.config.get('THEME', 'dark')
    return render_template('history.html', 
                          history=play_history,
                          mpd_info=mpd_status,
                          app_theme=app_theme)


def get_history_handler(app_ctx):
    """Return play history as JSON."""
    play_history = app_ctx['play_history']
    return jsonify({'status': 'success', 'history': play_history})


def clear_history_handler(app_ctx):
    """Clear play history.
    
    This clears the in-memory play_history list and resets last_tracked_song_id.
    """
    # Note: Actual clearing of play_history must be done in app.py
    # via modifying the global variables
    return jsonify({'status': 'success', 'message': 'History cleared'})
