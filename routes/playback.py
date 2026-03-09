"""
Playback control routes - play, pause, seek, volume, next/previous
"""
from flask import jsonify, redirect, url_for, request
import subprocess
import time

def play_handler(app_ctx):
    """Handle /play route"""
    connect_mpd_client = app_ctx['connect_mpd_client']
    
    client = None
    try:
        client = connect_mpd_client()
        if client:
            status = client.status()
            playlist_length = int(status.get('playlistlength', 0))
            
            if playlist_length == 0:
                error_msg = 'Cannot play: playlist is empty'
                if request.args.get('ajax') == '1' or request.method == 'POST':
                    if client:
                        try:
                            client.disconnect()
                        except:
                            pass
                    return jsonify({'status': 'error', 'message': error_msg})
                if client:
                    try:
                        client.disconnect()
                    except:
                        pass
                return redirect(url_for('index'))
            
            client.play()
        if request.args.get('ajax') == '1' or request.method == 'POST':
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            return jsonify({'status': 'success', 'message': 'Play command sent'})
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        print(f"Error playing: {e}")
        if request.args.get('ajax') == '1' or request.method == 'POST':
            return jsonify({'status': 'error', 'message': f'Error playing: {e}'})
    
    if client:
        try:
            client.disconnect()
        except:
            pass
    return redirect(url_for('index'))


def pause_handler(app_ctx):
    """Handle /pause route"""
    connect_mpd_client = app_ctx['connect_mpd_client']
    client = None
    
    try:
        client = connect_mpd_client()
        if client:
            client.pause()
        if request.args.get('ajax') == '1':
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            return jsonify({'status': 'success', 'message': 'Pause command sent'})
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        print(f"Error pausing: {e}")
        if request.args.get('ajax') == '1':
            return jsonify({'status': 'error', 'message': f'Error pausing: {e}'})
    
    if client:
        try:
            client.disconnect()
        except:
            pass
    return redirect(url_for('index'))


def stop_handler(app_ctx):
    """Handle /stop route"""
    connect_mpd_client = app_ctx['connect_mpd_client']
    client = None
    
    try:
        client = connect_mpd_client()
        if client:
            client.stop()
        if request.args.get('ajax') == '1':
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            return jsonify({'status': 'success', 'message': 'Stop command sent'})
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        print(f"Error stopping: {e}")
        if request.args.get('ajax') == '1':
            return jsonify({'status': 'error', 'message': f'Error stopping: {e}'})
    
    if client:
        try:
            client.disconnect()
        except:
            pass
    return redirect(url_for('index'))


def next_song_handler(app_ctx):
    """Handle /next route"""
    connect_mpd_client = app_ctx['connect_mpd_client']
    client = None
    
    try:
        client = connect_mpd_client()
        if client:
            client.next()
        if request.args.get('ajax') == '1':
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            return jsonify({'status': 'success', 'message': 'Next command sent'})
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        print(f"Error nexting: {e}")
        if request.args.get('ajax') == '1':
            return jsonify({'status': 'error', 'message': f'Error nexting: {e}'})
    
    if client:
        try:
            client.disconnect()
        except:
            pass
    return redirect(url_for('index'))


def previous_song_handler(app_ctx):
    """Handle /previous route"""
    connect_mpd_client = app_ctx['connect_mpd_client']
    client = None
    
    try:
        client = connect_mpd_client()
        if client:
            client.previous()
        if request.args.get('ajax') == '1':
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            return jsonify({'status': 'success', 'message': 'Previous command sent'})
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        print(f"Error previousing: {e}")
        if request.args.get('ajax') == '1':
            return jsonify({'status': 'error', 'message': f'Error previousing: {e}'})
    
    if client:
        try:
            client.disconnect()
        except:
            pass
    return redirect(url_for('index'))


def seek_position_handler(app_ctx):
    """Handle /seek route - seek to a specific position in current song"""
    from mpd import CommandError
    connect_mpd_client = app_ctx['connect_mpd_client']
    
    try:
        data = request.get_json()
        if not data or 'position' not in data:
            return jsonify({'status': 'error', 'message': 'Position required'}), 400
        
        position = float(data['position'])
        
        if position < 0:
            return jsonify({'status': 'error', 'message': 'Position must be >= 0'}), 400
        
        client = connect_mpd_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
        
        try:
            status = client.status()
            if status.get('state') not in ['play', 'pause']:
                return jsonify({'status': 'error', 'message': 'No song playing'}), 400
            
            current_song = int(status.get('song', 0))
            client.seek(current_song, position)
            
            return jsonify({
                'status': 'success',
                'message': f'Seeked to {position:.1f}s',
                'position': position
            })
        
        except CommandError as e:
            print(f"MPD CommandError seeking: {e}")
            return jsonify({'status': 'error', 'message': f'MPD error: {e}'}), 500
        except Exception as e:
            print(f"Error seeking: {e}")
            return jsonify({'status': 'error', 'message': f'Error: {e}'}), 500
    
    except Exception as e:
        print(f"Error processing seek request: {e}")
        return jsonify({'status': 'error', 'message': f'Error: {e}'}), 500


def set_volume_handler(app_ctx):
    """Handle /set_volume route - set volume 0-100 or relative change"""
    connect_mpd_client = app_ctx['connect_mpd_client']
    socketio = app_ctx['socketio']
    get_mpd_status_for_display = app_ctx['get_mpd_status_for_display']
    
    volume = request.form.get('volume', type=int, default=None)
    change = request.form.get('change', type=int, default=None)
    
    # If using relative change, fetch current volume first
    if change is not None and volume is None:
        try:
            client = connect_mpd_client()
            if client:
                status = client.status()
                current_vol = int(status.get('volume', '0'))
                volume = current_vol + change
            else:
                print("Failed to connect to MPD for relative volume adjustment.")
                return 'Error: MPD connection failed', 500
        except Exception as e:
            print(f"Error fetching current volume for relative adjustment: {e}")
            return f'Error: {e}', 500
    
    # Validate volume is set
    if volume is None:
        print("No volume or change parameter provided")
        return 'Error: Missing volume or change parameter', 400
    
    # Clamp volume between 0 and 100
    volume = max(0, min(100, volume))
    
    try:
        client = connect_mpd_client()
        if client:
            client.setvol(volume)
            print(f"[Volume Control] Set volume to {volume}%")
            # After setting volume, immediately trigger an update
            socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
            return 'OK', 200
        else:
            print("Failed to connect to MPD for set_volume.")
            return 'Error: MPD connection failed', 500
    except Exception as e:
        print(f"Error setting volume: {e}")
        return f'Error setting volume: {e}', 500


def restart_mpd_handler(app_ctx):
    """Handle /restart_mpd route - restart MPD service"""
    socketio = app_ctx['socketio']
    get_mpd_status_for_display = app_ctx['get_mpd_status_for_display']
    
    try:
        # Try to restart MPD service with timeout
        result = subprocess.run(['sudo', 'systemctl', 'restart', 'mpd.service'], 
                              check=True, capture_output=True, text=True, timeout=10)
        print("MPD service restart command sent successfully.")
        
        # Wait a moment for MPD to restart before checking status
        time.sleep(2)
        
        # Emit success message and trigger status update
        socketio.emit('server_message', {'type': 'success', 'text': 'MPD service restarted successfully'})
        socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
        
        return redirect(url_for('index'))
        
    except subprocess.TimeoutExpired:
        error_msg = "MPD restart timed out"
        print(f"Error restarting MPD service: {error_msg}")
        socketio.emit('server_message', {'type': 'error', 'text': error_msg})
        return redirect(url_for('index'))
        
    except subprocess.CalledProcessError as e:
        error_msg = f"MPD restart failed: {e.stderr.strip() if e.stderr else 'Unknown error'}"
        print(f"Error restarting MPD service: {error_msg}")
        socketio.emit('server_message', {'type': 'error', 'text': error_msg})
        return redirect(url_for('index'))
        
    except Exception as e:
        error_msg = f"General error restarting MPD: {str(e)}"
        print(error_msg)
        socketio.emit('server_message', {'type': 'error', 'text': error_msg})
        return redirect(url_for('index'))
