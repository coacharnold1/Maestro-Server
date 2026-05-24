"""
Playlist management routes - add, remove, save, load playlists
"""
from flask import jsonify, request, render_template, redirect, url_for
from mpd import CommandError
import os
import time
import re


def add_album_to_playlist_handler(app_ctx):
    """Add an entire album to the playlist."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    socketio = app_ctx['socketio']
    get_mpd_status_for_display = app_ctx['get_mpd_status_for_display']
    organize_album_by_disc = app_ctx['organize_album_by_disc']
    
    client = None
    try:
        def _norm(s: str) -> str:
            """Normalize strings for fuzzy comparison: lowercase and strip non-alnum."""
            if not s:
                return ''
            return re.sub(r"[^a-z0-9]+", "", s.lower())
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            artist = data.get('original_artist') or data.get('artist')
            album = data.get('album')
            disc_number = data.get('disc_number')
            album_dir = data.get('album_dir')
        else:
            artist = request.form.get('original_artist') or request.form.get('artist')
            album = request.form.get('album')
            disc_number = request.form.get('disc_number')
            album_dir = request.form.get('album_dir')
        
        if not artist or not album:
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Artist and album are required'}), 400
            return redirect(url_for('index'))

        client = connect_mpd_client()
        if not client:
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
            return redirect(url_for('index'))

        try:
            print(f"[DEBUG] Searching for album: artist='{artist}', album='{album}'" + 
                  (f", disc={disc_number}" if disc_number else "") +
                  (f", dir='{album_dir}'" if album_dir else ""), flush=True)
            songs = []
            try:
                songs = client.find('albumartist', artist, 'album', album)
                if songs:
                    print(f"[DEBUG] Found {len(songs)} songs using AlbumArtist", flush=True)
                    if album_dir:
                        original_count = len(songs)
                        songs = [s for s in songs if s.get('file', '').startswith(album_dir + '/')]
                        print(f"[DEBUG] Filtered by directory '{album_dir}': {original_count} -> {len(songs)} songs", flush=True)
            except Exception as e:
                print(f"[DEBUG] AlbumArtist search failed: {e}", flush=True)
                    
            if not songs:
                songs = client.find('artist', artist, 'album', album)
                if songs:
                    print(f"[DEBUG] Found {len(songs)} songs using Artist", flush=True)
                    if album_dir:
                        original_count = len(songs)
                        songs = [s for s in songs if s.get('file', '').startswith(album_dir + '/')]
                        print(f"[DEBUG] Filtered by directory '{album_dir}': {original_count} -> {len(songs)} songs", flush=True)
                else:
                    print(f"[DEBUG] No songs found with Artist search either", flush=True)

            if not songs:
                try:
                    candidates = client.search('album', album) or []
                    print(f"[DEBUG] Fallback search('album', '{album}') returned {len(candidates)} tracks", flush=True)
                    if candidates and artist:
                        na = _norm(artist)
                        filtered = [t for t in candidates
                                    if (_norm(t.get('artist', '')) == na or _norm(t.get('albumartist', '')) == na)
                                    and _norm(t.get('album', '')) == _norm(album)]
                        if not filtered:
                            filtered = [t for t in candidates
                                        if (_norm(t.get('artist', '')) == na or _norm(t.get('albumartist', '')) == na)
                                        and (_norm(album) in _norm(t.get('album', '')) or _norm(t.get('album', '')) in _norm(album))]
                        if filtered:
                            songs = filtered
                            print(f"[DEBUG] Fallback1 matched {len(songs)} tracks after filtering by artist", flush=True)
                        elif candidates:
                            exact_album = [t for t in candidates if _norm(t.get('album', '')) == _norm(album)]
                            if exact_album:
                                songs = exact_album
                                print(f"[DEBUG] Fallback1 matched {len(songs)} tracks by album-only exact norm", flush=True)
                except Exception as e:
                    print(f"[DEBUG] Fallback search error: {e}", flush=True)

            if not songs and artist:
                try:
                    artist_albums = client.list('album', 'artist', artist) or []
                    norm_target = _norm(album)
                    best = None
                    for entry in artist_albums:
                        name = entry.get('album') if isinstance(entry, dict) else entry
                        if not name:
                            continue
                        if _norm(name) == norm_target:
                            best = name
                            break
                    if not best:
                        for entry in artist_albums:
                            name = entry.get('album') if isinstance(entry, dict) else entry
                            if not name:
                                continue
                            nn = _norm(name)
                            if norm_target in nn or nn in norm_target:
                                best = name
                                break
                    if best:
                        print(f"[DEBUG] Fallback2 selected album name '{best}' for artist '{artist}'", flush=True)
                        songs = client.find('artist', artist, 'album', best)
                        if songs:
                            print(f"[DEBUG] Fallback2 found {len(songs)} tracks with adjusted album name", flush=True)
                except Exception as e:
                    print(f"[DEBUG] Fallback2 error while listing artist albums: {e}", flush=True)
                
            if not songs:
                print(f"[DEBUG] Total failure - no songs found for '{album}' by '{artist}'", flush=True)
                if request.is_json:
                    return jsonify({'status': 'error', 'message': f'No songs found for "{album}" by {artist}'}), 404
                return redirect(url_for('index'))
                
            print(f"[DEBUG] Found {len(songs)} total songs before disc detection", flush=True)
            if songs and len(songs) > 0:
                print(f"[DEBUG] Sample song: disc={songs[0].get('disc', 'NONE')}, file={songs[0].get('file', 'NONE')}", flush=True)
            
            disc_structure = organize_album_by_disc(songs)
            if disc_structure:
                print(f"[DEBUG] Disc structure found: {list(disc_structure.keys())} with {sum(len(v) for v in disc_structure.values())} total tracks", flush=True)
            else:
                print(f"[DEBUG] No disc structure detected (organize_album_by_disc returned None)", flush=True)
                
            if disc_number:
                disc_num = int(disc_number)
                if disc_structure and disc_num in disc_structure:
                    songs = disc_structure[disc_num]
                    print(f"[DISC] Adding only Disc {disc_num} with {len(songs)} tracks", flush=True)
                elif not disc_structure:
                    print(f"[DISC] WARNING: No disc structure found when adding Disc {disc_num}, adding all {len(songs)} songs", flush=True)
                else:
                    print(f"[DISC] ERROR: Disc {disc_number} not found. Available: {sorted(disc_structure.keys())}", flush=True)
                    if request.is_json:
                        return jsonify({'status': 'error', 'message': f'Disc {disc_number} not found. Available discs: {sorted(disc_structure.keys())}'}), 404
                    return redirect(url_for('index'))
            else:
                if disc_structure:
                    disc_count = len(disc_structure)
                    track_info = ", ".join([f"Disc {d}: {len(disc_structure[d])} tracks" for d in sorted(disc_structure.keys())])
                    print(f"[DISC] Multi-disc album detected: {disc_count} discs - {track_info}", flush=True)
                else:
                    print(f"[DISC] Single-disc album (or no disc metadata) - all tracks on one disc", flush=True)
                
            added_count = 0
            for song in songs:
                file_path = song.get('file')
                if file_path:
                    try:
                        client.add(file_path)
                        added_count += 1
                    except CommandError as e:
                        print(f"Error adding {file_path}: {e}")
            
            status = client.status()
            mpd_state = status.get('state', 'stop')
            should_auto_play = mpd_state in ['stop', 'pause']
            
            if should_auto_play and added_count > 0:
                try:
                    client.play()
                    print(f"[DEBUG] Auto-started playback after adding album", flush=True)
                except Exception as e:
                    print(f"[DEBUG] Error auto-playing: {e}", flush=True)
            
            if added_count > 0:
                if should_auto_play:
                    success_message = f'Added {added_count} songs from "{album}" by {artist} and started playing.'
                else:
                    success_message = f'Added {added_count} songs from "{album}" by {artist} to playlist.'
                socketio.emit('server_message', {'type': 'success', 'text': success_message})
                socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
                
                if request.is_json:
                    return jsonify({'status': 'success', 'message': success_message})
                return redirect(url_for('index'))
            else:
                if request.is_json:
                    return jsonify({'status': 'error', 'message': 'No songs were added to playlist'}), 500
                return redirect(url_for('index'))
                
        except Exception as e:
            print(f"Error adding album songs: {e}")
            if request.is_json:
                return jsonify({'status': 'error', 'message': f'Error adding album: {str(e)}'}), 500
            return redirect(url_for('index'))
                
    except Exception as e:
        print(f"Error in add_album_to_playlist: {e}")
        if request.is_json:
            return jsonify({'status': 'error', 'message': f'Error processing request: {str(e)}'}), 500
        return redirect(url_for('index'))
    finally:
        # Always disconnect MPD client after request completes
        if client:
            try:
                client.disconnect()
            except:
                pass


def clear_and_add_album_handler(app_ctx):
    """Clear playlist and add an entire album (or just a disc)."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    socketio = app_ctx['socketio']
    get_mpd_status_for_display = app_ctx['get_mpd_status_for_display']
    organize_album_by_disc = app_ctx['organize_album_by_disc']
    
    client = None
    try:
        if request.is_json:
            data = request.get_json()
            artist = data.get('original_artist') or data.get('artist')
            album = data.get('album')
            disc_number = data.get('disc_number')
        else:
            artist = request.form.get('original_artist') or request.form.get('artist')
            album = request.form.get('album')
            disc_number = request.form.get('disc_number')
        
        if not artist or not album:
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Artist and album are required'}), 400
            return redirect(url_for('index'))

        client = connect_mpd_client()
        if not client:
            if request.is_json:
                return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
            return redirect(url_for('index'))

        try:
            print(f"[DEBUG] Clear+Add - Searching for album: artist='{artist}', album='{album}'" + 
                  (f", disc={disc_number}" if disc_number else ""), flush=True)
            current_playlist = client.playlist()
            tracks_cleared = len(current_playlist)
            
            client.clear()
            
            songs = []
            try:
                songs = client.find('albumartist', artist, 'album', album)
                if songs:
                    print(f"[DEBUG] Clear+Add - Found {len(songs)} songs using AlbumArtist", flush=True)
            except Exception as e:
                print(f"[DEBUG] Clear+Add - AlbumArtist search failed: {e}", flush=True)
                
            if not songs:
                songs = client.find('artist', artist, 'album', album)
                if songs:
                    print(f"[DEBUG] Clear+Add - Found {len(songs)} songs using Artist", flush=True)
                else:
                    print(f"[DEBUG] Clear+Add - No songs found with Artist search either", flush=True)
            
            if not songs:
                if client:
                    try:
                        client.disconnect()
                    except:
                        pass
                if request.is_json:
                    return jsonify({'status': 'error', 'message': f'No songs found for "{album}" by {artist}'}), 404
                return redirect(url_for('index'))
            
            if disc_number:
                disc_structure = organize_album_by_disc(songs)
                disc_num = int(disc_number)
                if disc_structure and disc_num in disc_structure:
                    songs = disc_structure[disc_num]
                    print(f"[DISC] Clear+Add - Adding only Disc {disc_num} with {len(songs)} tracks", flush=True)
                elif not disc_structure:
                    print(f"[DISC] Clear+Add - WARNING: No disc structure found, adding all {len(songs)} songs", flush=True)
                else:
                    print(f"[DISC] Clear+Add - ERROR: Disc {disc_number} not found. Available: {sorted(disc_structure.keys())}", flush=True)
                    if client:
                        try:
                            client.disconnect()
                        except:
                            pass
                    if request.is_json:
                        return jsonify({'status': 'error', 'message': f'Disc {disc_number} not found. Available discs: {sorted(disc_structure.keys())}'}), 404
                    return redirect(url_for('index'))
            
            added_count = 0
            for song in songs:
                file_path = song.get('file')
                if file_path:
                    try:
                        client.add(file_path)
                        added_count += 1
                    except CommandError as e:
                        print(f"Error adding {file_path}: {e}")
            
            if added_count > 0:
                try:
                    client.play(0)
                    print(f"[DEBUG] Started playing playlist after replacing with album")
                except Exception as e:
                    print(f"Error starting playback: {e}")
            
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            
            if added_count > 0:
                disc_text = f" (Disc {disc_number})" if disc_number else ""
                socketio.emit('server_message', {'type': 'success', 'text': f'Playlist cleared and added {added_count} songs from "{album}"{disc_text} by {artist}. Now playing!'})
                socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
                
                if request.is_json:
                    return jsonify({'status': 'success', 'message': f'Playlist replaced with {added_count} songs from album and started playing', 'tracks_cleared': tracks_cleared})
                return redirect(url_for('index'))
            else:
                if request.is_json:
                    return jsonify({'status': 'error', 'message': 'No songs were added to playlist'}), 500
                return redirect(url_for('index'))
                
        except Exception as e:
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            print(f"Error clearing and adding album songs: {e}")
            if request.is_json:
                return jsonify({'status': 'error', 'message': f'Error replacing playlist: {str(e)}'}), 500
            return redirect(url_for('index'))
            
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        print(f"Error in clear_and_add_album: {e}")
        if request.is_json:
            return jsonify({'status': 'error', 'message': f'Error processing request: {str(e)}'}), 500
        return redirect(url_for('index'))

        try:
            print(f"[DEBUG] Clear+Add - Searching for album: artist='{artist}', album='{album}'" + 
                  (f", disc={disc_number}" if disc_number else ""), flush=True)
            current_playlist = client.playlist()
            tracks_cleared = len(current_playlist)
            
            client.clear()
            
            songs = []
            try:
                songs = client.find('albumartist', artist, 'album', album)
                if songs:
                    print(f"[DEBUG] Clear+Add - Found {len(songs)} songs using AlbumArtist", flush=True)
            except Exception as e:
                print(f"[DEBUG] Clear+Add - AlbumArtist search failed: {e}", flush=True)
                
            if not songs:
                songs = client.find('artist', artist, 'album', album)
                if songs:
                    print(f"[DEBUG] Clear+Add - Found {len(songs)} songs using Artist", flush=True)
                else:
                    print(f"[DEBUG] Clear+Add - No songs found with Artist search either", flush=True)
            
            if not songs:
                if request.is_json:
                    return jsonify({'status': 'error', 'message': f'No songs found for "{album}" by {artist}'}), 404
                return redirect(url_for('index'))
            
            if disc_number:
                disc_structure = organize_album_by_disc(songs)
                disc_num = int(disc_number)
                if disc_structure and disc_num in disc_structure:
                    songs = disc_structure[disc_num]
                    print(f"[DISC] Clear+Add - Adding only Disc {disc_num} with {len(songs)} tracks", flush=True)
                elif not disc_structure:
                    print(f"[DISC] Clear+Add - WARNING: No disc structure found, adding all {len(songs)} songs", flush=True)
                else:
                    print(f"[DISC] Clear+Add - ERROR: Disc {disc_number} not found. Available: {sorted(disc_structure.keys())}", flush=True)
                    if request.is_json:
                        return jsonify({'status': 'error', 'message': f'Disc {disc_number} not found. Available discs: {sorted(disc_structure.keys())}'}), 404
                    return redirect(url_for('index'))
            
            added_count = 0
            for song in songs:
                file_path = song.get('file')
                if file_path:
                    try:
                        client.add(file_path)
                        added_count += 1
                    except CommandError as e:
                        print(f"Error adding {file_path}: {e}")
            
            if added_count > 0:
                try:
                    client.play(0)
                    print(f"[DEBUG] Started playing playlist after replacing with album")
                except Exception as e:
                    print(f"Error starting playback: {e}")
            
            if added_count > 0:
                disc_text = f" (Disc {disc_number})" if disc_number else ""
                socketio.emit('server_message', {'type': 'success', 'text': f'Playlist cleared and added {added_count} songs from "{album}"{disc_text} by {artist}. Now playing!'})
                socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
                
                if request.is_json:
                    return jsonify({'status': 'success', 'message': f'Playlist replaced with {added_count} songs from album and started playing', 'tracks_cleared': tracks_cleared})
                return redirect(url_for('index'))
            else:
                if request.is_json:
                    return jsonify({'status': 'error', 'message': 'No songs were added to playlist'}), 500
                return redirect(url_for('index'))
                
        except Exception as e:
            print(f"Error clearing and adding album songs: {e}")
            if request.is_json:
                return jsonify({'status': 'error', 'message': f'Error replacing playlist: {str(e)}'}), 500
            return redirect(url_for('index'))
            
    except Exception as e:
        print(f"Error in clear_and_add_album: {e}")
        if request.is_json:
            return jsonify({'status': 'error', 'message': f'Error processing request: {str(e)}'}), 500
        return redirect(url_for('index'))


def add_song_to_playlist_handler(app_ctx):
    """Add a single song to the playlist."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    socketio = app_ctx['socketio']
    get_mpd_status_for_display = app_ctx['get_mpd_status_for_display']
    
    client = None
    try:
        file_path = request.form.get('file')
        
        if not file_path:
            print("[DEBUG] No file path provided for add_song_to_playlist")
            if request.is_json or request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                return jsonify({'status': 'error', 'message': 'No file path provided'}), 400
            return redirect(url_for('index'))

        print(f"[DEBUG] Adding song to playlist: {file_path}")
        client = connect_mpd_client()
        if not client:
            print("[DEBUG] Could not connect to MPD in add_song_to_playlist")
            if request.is_json or request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
            return redirect(url_for('index'))

        try:
            client.add(file_path)
            
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            
            print(f"[DEBUG] Successfully added song to playlist: {file_path}")
            socketio.emit('server_message', {'type': 'info', 'text': 'Song added to playlist.'})
            socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
            
            if request.is_json or request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                return jsonify({'status': 'success', 'message': 'Song added to playlist'}), 200
            return redirect(url_for('index'))
            
        except CommandError as e:
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            print(f"[DEBUG] MPD CommandError in add_song_to_playlist: {e}")
            if request.is_json or request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                return jsonify({'status': 'error', 'message': f'MPD error: {str(e)}'}), 500
            return redirect(url_for('index'))
        except Exception as e:
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            print(f"[DEBUG] Exception in add_song_to_playlist: {e}")
            if request.is_json or request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                return jsonify({'status': 'error', 'message': f'Error adding song: {str(e)}'}), 500
            return redirect(url_for('index'))
            
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        print(f"Error in add_song_to_playlist: {e}")
        if request.is_json or request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 500
        return redirect(url_for('index'))


def get_mpd_playlist_helper(connect_mpd_client, bandcamp_service=None):
    """Fetches the current MPD playlist and enriches with Bandcamp metadata."""
    import re
    
    client = connect_mpd_client()
    if not client:
        return []
    try:
        playlist = client.playlistinfo()
        
        # Enrich with Bandcamp metadata if available
        if bandcamp_service and bandcamp_service.is_enabled:
            for i, song in enumerate(playlist):
                song['pos'] = i
                song_file = song.get('file', '')
                
                # Check if this is a Bandcamp stream and look up metadata
                if song_file and 'bandcamp.com' in song_file:
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
                        song['artist'] = bc_meta.get('artist', song.get('artist', 'Unknown Artist'))
                        song['title'] = bc_meta.get('title', song.get('title', 'Unknown Title'))
                        song['album'] = bc_meta.get('album', song.get('album', 'Unknown Album'))
        else:
            for i, song in enumerate(playlist):
                song['pos'] = i
        
        if client:
            try:
                client.disconnect()
            except:
                pass
        
        return playlist
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        print(f"Error fetching playlist: {e}")
        return []


def playlist_page_handler(app_ctx):
    """Renders the playlist HTML page."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    bandcamp_service = app_ctx.get('bandcamp_service')
    
    playlist = get_mpd_playlist_helper(connect_mpd_client, bandcamp_service)
    return render_template('playlist.html', playlist=playlist)


def remove_from_playlist_handler(app_ctx):
    """Removes a song from the playlist by its position."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    socketio = app_ctx['socketio']
    bandcamp_service = app_ctx.get('bandcamp_service')
    
    client = None
    pos = request.form.get('pos', type=int)
    if pos is None:
        return jsonify({'status': 'error', 'message': 'Position not provided'}), 400

    try:
        client = connect_mpd_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
        try:
            client.delete(pos)
            
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            
            socketio.emit('server_message', {'type': 'info', 'text': f'Removed song at position {pos+1} from playlist.'})
            socketio.emit('playlist_updated', get_mpd_playlist_helper(connect_mpd_client, bandcamp_service))
            return jsonify({'status': 'success', 'message': 'Song removed'})
        except CommandError as e:
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            print(f"MPD CommandError removing song at {pos}: {e}")
            return jsonify({'status': 'error', 'message': f'MPD error: {e}'}), 500
        except Exception as e:
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            print(f"Error removing song from playlist at {pos}: {e}")
            return jsonify({'status': 'error', 'message': f'Error removing song: {e}'}), 500
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        print(f"Error in remove_from_playlist_handler: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def move_track_handler(app_ctx):
    """Moves a track up/down or to a specific position in the playlist."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    socketio = app_ctx['socketio']
    
    client = None
    data = request.get_json()
    if not data or 'pos' not in data:
        return jsonify({'status': 'error', 'message': 'Position required'}), 400
    
    pos = data['pos']
    
    try:
        client = connect_mpd_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
        
        try:
            playlist = client.playlistinfo()
            playlist_length = len(playlist)
            
            if 'to' in data:
                new_pos = data['to']
                if new_pos < 0 or new_pos >= playlist_length:
                    if client:
                        try:
                            client.disconnect()
                        except:
                            pass
                    return jsonify({'status': 'error', 'message': 'Invalid target position'}), 400
                if pos == new_pos:
                    if client:
                        try:
                            client.disconnect()
                        except:
                            pass
                    return jsonify({'status': 'success', 'message': 'Track already in position'})
            elif 'direction' in data:
                direction = data['direction']
                if direction not in ['up', 'down']:
                    if client:
                        try:
                            client.disconnect()
                        except:
                            pass
                    return jsonify({'status': 'error', 'message': 'Direction must be "up" or "down"'}), 400
                
                if direction == 'up':
                    if pos == 0:
                        if client:
                            try:
                                client.disconnect()
                            except:
                                pass
                        return jsonify({'status': 'error', 'message': 'Already at top of playlist'}), 400
                    new_pos = pos - 1
                else:
                    if pos >= playlist_length - 1:
                        if client:
                            try:
                                client.disconnect()
                            except:
                                pass
                        return jsonify({'status': 'error', 'message': 'Already at bottom of playlist'}), 400
                    new_pos = pos + 1
            else:
                if client:
                    try:
                        client.disconnect()
                    except:
                        pass
                return jsonify({'status': 'error', 'message': 'Either "direction" or "to" parameter required'}), 400
            
            client.move(pos, new_pos)
            
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            
            socketio.emit('playlist_updated', get_mpd_playlist_helper(connect_mpd_client))
            
            return jsonify({
                'status': 'success',
                'message': 'Track moved',
                'new_pos': new_pos
            })
        
        except CommandError as e:
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            print(f"MPD CommandError moving track: {e}")
            return jsonify({'status': 'error', 'message': f'MPD error: {e}'}), 500
        except Exception as e:
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            print(f"Error moving track: {e}")
            return jsonify({'status': 'error', 'message': f'Error: {e}'}), 500
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        print(f"Error in move_track_handler: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def clear_playlist_handler(app_ctx):
    """Clears the entire MPD playlist."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    socketio = app_ctx['socketio']
    bandcamp_service = app_ctx.get('bandcamp_service')
    
    client = None
    try:
        client = connect_mpd_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
        try:
            client.clear()
            
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            
            socketio.emit('server_message', {'type': 'info', 'text': 'MPD playlist cleared.'})
            socketio.emit('playlist_updated', get_mpd_playlist_helper(connect_mpd_client, bandcamp_service))
            return jsonify({'status': 'success', 'message': 'Playlist cleared'})
        except CommandError as e:
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            print(f"MPD CommandError clearing playlist: {e}")
            return jsonify({'status': 'error', 'message': f'MPD error: {e}'}), 500
        except Exception as e:
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            print(f"Error clearing playlist: {e}")
            return jsonify({'status': 'error', 'message': f'Error clearing playlist: {e}'}), 500
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        print(f"Error in clear_playlist_handler: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def save_playlist_handler(app_ctx):
    """Save the current MPD playlist to an M3U file."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    playlists_dir = app_ctx['playlists_dir']
    
    client = None
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'status': 'error', 'message': 'Playlist name is required'}), 400
    
    playlist_name = data['name'].strip()
    if not playlist_name:
        return jsonify({'status': 'error', 'message': 'Playlist name cannot be empty'}), 400
    
    playlist_name = playlist_name.replace('/', '_').replace('\\', '_')
    
    if not playlist_name.lower().endswith('.m3u'):
        playlist_name += '.m3u'
    
    playlist_path = os.path.join(playlists_dir, playlist_name)
    
    try:
        client = connect_mpd_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
        
        try:
            playlist_songs = client.playlistinfo()
            
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            
            if not playlist_songs:
                return jsonify({'status': 'error', 'message': 'Current playlist is empty'}), 400
            
            with open(playlist_path, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                for song in playlist_songs:
                    artist = song.get('artist', 'Unknown Artist')
                    title = song.get('title', 'Unknown Title')
                    duration = int(song.get('time', '0'))
                    f.write(f'#EXTINF:{duration},{artist} - {title}\n')
                    f.write(f"{song.get('file', '')}\n")
            
            print(f"Saved playlist: {playlist_name} ({len(playlist_songs)} songs)")
            return jsonify({
                'status': 'success',
                'message': f'Playlist "{playlist_name}" saved',
                'song_count': len(playlist_songs)
            })
        
        except Exception as e:
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            print(f"Error saving playlist: {e}")
            return jsonify({'status': 'error', 'message': f'Error saving playlist: {e}'}), 500
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        print(f"Error in save_playlist_handler: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def list_playlists_handler(app_ctx):
    """List all saved M3U playlists."""
    playlists_dir = app_ctx['playlists_dir']
    
    try:
        playlists = []
        if os.path.exists(playlists_dir):
            for filename in sorted(os.listdir(playlists_dir)):
                if filename.lower().endswith('.m3u'):
                    filepath = os.path.join(playlists_dir, filename)
                    stat_info = os.stat(filepath)
                    modified_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat_info.st_mtime))
                    
                    song_count = 0
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.strip() and not line.startswith('#'):
                                    song_count += 1
                    except Exception as e:
                        print(f"Error reading playlist {filename}: {e}")
                    
                    playlists.append({
                        'name': filename,
                        'modified': modified_time,
                        'song_count': song_count
                    })
        
        return jsonify({'status': 'success', 'playlists': playlists})
    
    except Exception as e:
        print(f"Error listing playlists: {e}")
        return jsonify({'status': 'error', 'message': f'Error listing playlists: {e}'}), 500


def load_playlist_handler(app_ctx):
    """Load a saved M3U playlist into MPD, clearing the current playlist."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    socketio = app_ctx['socketio']
    playlists_dir = app_ctx['playlists_dir']
    bandcamp_service = app_ctx.get('bandcamp_service')
    
    client = None
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'status': 'error', 'message': 'Playlist name is required'}), 400
    
    playlist_name = data['name']
    playlist_path = os.path.join(playlists_dir, playlist_name)
    
    if not os.path.exists(playlist_path):
        return jsonify({'status': 'error', 'message': 'Playlist not found'}), 404
    
    try:
        client = connect_mpd_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
        
        try:
            client.clear()
            
            songs_added = 0
            songs_failed = 0
            with open(playlist_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    try:
                        client.add(line)
                        songs_added += 1
                    except CommandError as e:
                        print(f"Failed to add song '{line}': {e}")
                        songs_failed += 1
            
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            
            socketio.emit('server_message', {
                'type': 'info',
                'text': f'Loaded playlist "{playlist_name}" ({songs_added} songs)'
            })
            socketio.emit('playlist_updated', get_mpd_playlist_helper(connect_mpd_client, bandcamp_service))
            
            message = f'Loaded {songs_added} songs'
            if songs_failed > 0:
                message += f' ({songs_failed} songs not found)'
            
            return jsonify({
                'status': 'success',
                'message': message,
                'songs_added': songs_added,
                'songs_failed': songs_failed
            })
        
        except Exception as e:
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            print(f"Error loading playlist: {e}")
            return jsonify({'status': 'error', 'message': f'Error loading playlist: {e}'}), 500
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        print(f"Error in load_playlist_handler: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def delete_playlist_handler(app_ctx):
    """Delete a saved M3U playlist."""
    playlists_dir = app_ctx['playlists_dir']
    
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'status': 'error', 'message': 'Playlist name is required'}), 400
    
    playlist_name = data['name']
    playlist_path = os.path.join(playlists_dir, playlist_name)
    
    if not os.path.exists(playlist_path):
        return jsonify({'status': 'error', 'message': 'Playlist not found'}), 404
    
    try:
        os.remove(playlist_path)
        print(f"Deleted playlist: {playlist_name}")
        return jsonify({'status': 'success', 'message': f'Playlist "{playlist_name}" deleted'})
    
    except Exception as e:
        print(f"Error deleting playlist: {e}")
        return jsonify({'status': 'error', 'message': f'Error deleting playlist: {e}'}), 500


def play_song_at_pos_handler(app_ctx):
    """Plays a song at a specific position in the playlist."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    socketio = app_ctx['socketio']
    get_mpd_status_for_display = app_ctx['get_mpd_status_for_display']
    
    client = None
    pos = request.form.get('pos', type=int)
    if pos is None:
        return jsonify({'status': 'error', 'message': 'Position not provided'}), 400

    try:
        client = connect_mpd_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
        try:
            client.play(pos)
            
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            
            socketio.emit('server_message', {'type': 'info', 'text': f'Playing song at position {pos+1}.'})
            socketio.start_background_task(target=lambda: socketio.emit('mpd_status', get_mpd_status_for_display()))
            return jsonify({'status': 'success', 'message': 'Playing song'})
        except CommandError as e:
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            print(f"MPD CommandError playing song at {pos}: {e}")
            return jsonify({'status': 'error', 'message': f'MPD error: {e}'}), 500
        except Exception as e:
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            print(f"Error playing song from playlist at {pos}: {e}")
            return jsonify({'status': 'error', 'message': f'Error playing song: {e}'}), 500
    except Exception as e:
        if client:
            try:
                client.disconnect()
            except:
                pass
        print(f"Error in play_song_at_pos_handler: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
