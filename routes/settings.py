"""
Settings routes - handles user preferences, theme, API credentials
"""
from flask import render_template, redirect, url_for, request, flash
from utils.settings import load_settings, save_settings

def settings_page_handler(app_ctx):
    """
    Handle GET/POST for /settings route
    
    Args:
        app_ctx: dict with 'app' and 'globals' references
    """
    app = app_ctx['app']
    globals_ref = app_ctx['globals']
    
    current = load_settings()
    if request.method == 'POST':
        theme = request.form.get('theme', current.get('theme', 'dark')).strip() or 'dark'
        lastfm_key = request.form.get('lastfm_api_key', '').strip()
        lastfm_secret = request.form.get('lastfm_shared_secret', '').strip()
        recent_albums_dir = request.form.get('recent_albums_dir', '').strip()
        scrobble_flag = request.form.get('enable_scrobbling') == 'on'
        show_toasts_flag = request.form.get('show_scrobble_toasts') == 'on'
        hide_volume_flag = request.form.get('hide_volume_controls') == 'on'

        # Update in-memory and persisted settings. Environment variables still take precedence at runtime
        current['theme'] = theme
        current['enable_scrobbling'] = scrobble_flag
        globals_ref['scrobbling_enabled'] = scrobble_flag
        current['show_scrobble_toasts'] = show_toasts_flag
        globals_ref['show_scrobble_toasts'] = show_toasts_flag
        current['hide_volume_controls'] = hide_volume_flag
        
        # Handle Recent Albums Directory
        if recent_albums_dir:
            current['recent_albums_dir'] = recent_albums_dir
            print(f"[Settings] Recent albums directory updated to: {recent_albums_dir}", flush=True)
        elif 'recent_albums_dir' in current:
            # If user cleared it, remove from settings
            del current['recent_albums_dir']
            print(f"[Settings] Recent albums directory cleared", flush=True)
        
        # Handle Last.fm API Key
        # If user submitted a value that's not the masked placeholder, update it
        import os
        masked_placeholder = '•' * 10
        if lastfm_key and lastfm_key != masked_placeholder:
            current['lastfm_api_key'] = lastfm_key
            # Update runtime value only if not set via environment
            if not os.environ.get('LASTFM_API_KEY'):
                globals_ref['LASTFM_API_KEY'] = lastfm_key
            print(f"[Settings] Last.fm API key updated", flush=True)
        
        # Handle Last.fm Shared Secret
        if lastfm_secret and lastfm_secret != masked_placeholder:
            current['lastfm_shared_secret'] = lastfm_secret
            if not os.environ.get('LASTFM_SHARED_SECRET'):
                globals_ref['LASTFM_SHARED_SECRET'] = lastfm_secret
            print(f"[Settings] Last.fm shared secret updated", flush=True)

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
                           hide_volume_controls=bool(current.get('hide_volume_controls', False)),
                           recent_albums_dir=current.get('recent_albums_dir', ''),
                           lastfm_api_key_masked=masked_key,
                           lastfm_shared_secret_masked=masked_secret,
                           genius_client_id=current.get('genius_client_id', ''),
                           genius_client_secret=current.get('genius_client_secret', ''),
                           genius_access_token=current.get('genius_access_token', ''))


def settings_genius_page_handler(app_ctx):
    """
    Handle POST for /settings/genius route
    Persist Genius API credentials and reload runtime values.
    
    Args:
        app_ctx: dict with 'app' and 'globals' references
    """
    import os
    app = app_ctx['app']
    globals_ref = app_ctx['globals']
    
    current = load_settings()
    client_id = request.form.get('genius_client_id', '').strip()
    client_secret = request.form.get('genius_client_secret', '').strip()
    access_token = request.form.get('genius_access_token', '').strip()

    if client_id:
        current['genius_client_id'] = client_id
        if not os.environ.get('GENIUS_CLIENT_ID'):
            globals_ref['GENIUS_CLIENT_ID'] = client_id
    if client_secret:
        current['genius_client_secret'] = client_secret
        if not os.environ.get('GENIUS_CLIENT_SECRET'):
            globals_ref['GENIUS_CLIENT_SECRET'] = client_secret
    if access_token:
        current['genius_access_token'] = access_token
        if not os.environ.get('GENIUS_ACCESS_TOKEN'):
            globals_ref['GENIUS_ACCESS_TOKEN'] = access_token

    if save_settings(current):
        flash('Genius settings saved.', 'success')
    else:
        flash('Failed to save Genius settings.', 'error')
    return redirect(url_for('settings_page'))
