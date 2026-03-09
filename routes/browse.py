"""
Browse and search routes - genres, artists, albums, tracks
"""
from flask import jsonify, request, render_template
import os
import random
import time

def search_autocomplete_handler(app_ctx):
    """Handle /api/search/autocomplete route"""
    connect_mpd_client = app_ctx['connect_mpd_client']
    client = None
    
    try:
        client = connect_mpd_client()
        if not client:
            return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500
        
        # Get all unique artists, albums, and titles with fallback for malformed metadata
        artists = []
        albums = []
        titles = []
        
        # Try to get artists list
        try:
            artists_raw = client.list('artist')
            artists = sorted(set([
                (a if isinstance(a, str) else a.get('artist', '')) 
                for a in artists_raw if a
            ]))
        except Exception as artist_error:
            print(f"[DEBUG] client.list('artist') failed, falling back to song scan: {artist_error}", flush=True)
            # Fallback: scan all songs to extract unique artists
            try:
                all_songs = client.listallinfo()
                artist_set = set()
                for song in all_songs:
                    artist = song.get('artist', '').strip()
                    if artist:
                        artist_set.add(artist)
                artists = sorted(list(artist_set))
            except Exception as fallback_error:
                print(f"[DEBUG] Artist fallback also failed: {fallback_error}", flush=True)
                artists = []
        
        # Try to get albums list
        try:
            albums_raw = client.list('album')
            albums = sorted(set([
                (a if isinstance(a, str) else a.get('album', '')) 
                for a in albums_raw if a
            ]))
        except Exception as album_error:
            print(f"[DEBUG] client.list('album') failed, falling back to song scan: {album_error}", flush=True)
            # Fallback: scan all songs to extract unique albums
            try:
                all_songs = client.listallinfo()
                album_set = set()
                for song in all_songs:
                    album = song.get('album', '').strip()
                    if album:
                        album_set.add(album)
                albums = sorted(list(album_set))
            except Exception as fallback_error:
                print(f"[DEBUG] Album fallback also failed: {fallback_error}", flush=True)
                albums = []
        
        # Try to get titles list
        try:
            titles_raw = client.list('title')
            titles = sorted(set([
                (t if isinstance(t, str) else t.get('title', '')) 
                for t in titles_raw if t
            ]))[:1000]  # Limit to 1000
        except Exception as title_error:
            print(f"[DEBUG] client.list('title') failed, falling back to song scan: {title_error}", flush=True)
            # Fallback: scan all songs to extract unique titles
            try:
                all_songs = client.listallinfo()
                title_set = set()
                for song in all_songs:
                    title = song.get('title', '').strip()
                    if title:
                        title_set.add(title)
                titles = sorted(list(title_set))[:1000]
            except Exception as fallback_error:
                print(f"[DEBUG] Title fallback also failed: {fallback_error}", flush=True)
                titles = []
        
        # Disconnect BEFORE returning
        if client:
            try:
                client.disconnect()
            except:
                pass
        
        return jsonify({
            'status': 'success',
            'artists': [a for a in artists if a],
            'albums': [a for a in albums if a],
            'titles': [t for t in titles if t]
        })
    except Exception as e:
        # Disconnect on error too
        if client:
            try:
                client.disconnect()
            except:
                pass
        
        print(f"Error fetching autocomplete data: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


def search_handler(app_ctx):
    """Handle /search route"""
    connect_mpd_client = app_ctx['connect_mpd_client']
    perform_search = app_ctx['perform_search']
    bandcamp_service = app_ctx.get('bandcamp_service')
    client = None
    
    print(f"Request method: {request.method}, Request form: {dict(request.form)}, Request args: {dict(request.args)}", flush=True)
    
    # Handle both POST and GET requests
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        search_tag = request.form.get('search_tag', 'any')
    else:  # GET request
        query = request.args.get('query', '').strip()
        search_tag = request.args.get('search_tag') or request.args.get('type', 'any')
    
    # If there's a query, perform the search
    if query:
        try:
            print(f"Received search request for tag: {search_tag} with query: {query}")

            client = connect_mpd_client()
            if not client:
                return render_template('search.html', error="Could not connect to MPD")

            try:
                search_results = perform_search(client, search_tag, query, bandcamp_service)
                
                # Disconnect before returning template
                if client:
                    try:
                        client.disconnect()
                    except:
                        pass
                
                result = render_template('search_results.html', 
                                     results=search_results, 
                                     query=query, 
                                     search_tag=search_tag)
                return result
            except Exception as e:
                # Disconnect on error
                if client:
                    try:
                        client.disconnect()
                    except:
                        pass
                
                import traceback
                return render_template('search.html', error=f"Search failed: {e}")

        except Exception as e:
            print(f"Error processing search: {e}")
            return render_template('search.html', error="An error occurred while processing your search")
    
    # No query provided, just show the search page
    return render_template('search.html')


def random_albums_handler(app_ctx):
    """Handle /random_albums route"""
    connect_mpd_client = app_ctx['connect_mpd_client']
    client = None
    
    try:
        client = connect_mpd_client()
        if not client:
            return render_template('search.html', error="Could not connect to MPD")
        
        try:
            # Get all unique albums efficiently
            all_albums_raw = client.list('album')
            
            # Filter out empty album names and normalize
            valid_albums = []
            for album_item in all_albums_raw:
                if isinstance(album_item, dict):
                    album_name = album_item.get('album', '')
                else:
                    album_name = album_item
                if album_name and str(album_name).strip():
                    valid_albums.append(album_name)
            
            print(f"[DEBUG] Total albums in library: {len(valid_albums)}", flush=True)
            
            # Get 25 random albums
            num_to_select = min(25, len(valid_albums))
            random_album_names = random.sample(valid_albums, num_to_select)
            print(f"[DEBUG] Selected {num_to_select} random albums", flush=True)
            
            albums_list = []
            for album_name in random_album_names:
                try:
                    # Use find for exact match
                    songs = client.find('album', album_name)
                    if songs:
                        first_song = songs[0]
                        artist_name = first_song.get('artist', 'Unknown Artist')
                        song_file = first_song.get('file', '')
                        genre = first_song.get('genre', 'Unknown Genre')
                        
                        albums_list.append({
                            'item_type': 'album',
                            'artist': artist_name,
                            'album': album_name,
                            'genre': genre,
                            'track_count': len(songs),
                            'sample_file': song_file
                        })
                        print(f"[DEBUG] Added album: {album_name} by {artist_name} ({len(songs)} tracks)", flush=True)
                    else:
                        print(f"[DEBUG] No songs found for album: {album_name}", flush=True)
                except Exception as e:
                    print(f"[DEBUG] Error getting info for album '{album_name}': {e}", flush=True)
                    continue
            
            print(f"[DEBUG] Returning {len(albums_list)} albums", flush=True)
            # Disconnect before returning template
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            
            return render_template('search_results.html', 
                                 results=albums_list, 
                                 query='Random Selection', 
                                 search_tag='album')
        except Exception as e:
            # Disconnect on error
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            
            import traceback
            traceback.print_exc()
            return render_template('search.html', error=f"Random albums failed: {e}")
            
    except Exception as e:
        # Disconnect on error
        if client:
            try:
                client.disconnect()
            except:
                pass
        
        print(f"Error in random_albums: {e}")
        return render_template('search.html', error=f"Error: {e}")


def browse_genres_page_handler(app_ctx):
    """Handle /browse route"""
    return render_template('browse_genres.html')


def browse_artists_page_handler(app_ctx):
    """Handle /browse/artists route"""
    return render_template('browse_artists.html')


def browse_albums_page_handler(app_ctx):
    """Handle /browse/albums route"""
    return render_template('browse_albums.html')


def api_browse_genres_handler(app_ctx):
    """Handle /api/browse/genres route"""
    connect_mpd_client = app_ctx['connect_mpd_client']
    
    print("[DEBUG] /api/browse/genres called", flush=True)
    
    # Retry logic with exponential backoff to handle race condition on first load
    max_retries = 3
    retry_delay = 0.1  # Start with 100ms
    
    for attempt in range(max_retries):
        client = None
        try:
            client = connect_mpd_client()
            if not client:
                print("[DEBUG] Could not connect to MPD")
                return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500

            # Try to get genres from MPD list command
            genres = []
            try:
                print("[DEBUG] Attempting client.list('genre')...", flush=True)
                genres = client.list('genre')
                print(f"[DEBUG] Found {len(genres)} genres using list command", flush=True)
            except Exception as list_error:
                # If list fails (due to malformed genres in DB), fallback to getting genres from all songs
                print(f"[DEBUG] list('genre') failed ({type(list_error).__name__}: {list_error}), falling back to scanning all songs", flush=True)
                try:
                    all_songs = client.listallinfo()
                    genre_set = set()
                    for song in all_songs:
                        genre = song.get('genre', '').strip()
                        if genre:
                            genre_set.add(genre)
                    genres = sorted(list(genre_set))
                    print(f"[DEBUG] Found {len(genres)} genres from song scan fallback", flush=True)
                except Exception as fallback_error:
                    print(f"[DEBUG] Fallback also failed ({fallback_error}), ", end="", flush=True)
                    # If this is not the last retry, wait and try again
                    if attempt < max_retries - 1:
                        print(f"retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})", flush=True)
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        print("returning error", flush=True)
                        raise
            
            genre_data = []
            
            for genre_item in genres:
                # Handle both string and dict responses from MPD
                if isinstance(genre_item, dict):
                    genre = genre_item.get('genre', '')
                else:
                    genre = str(genre_item).strip()
                    
                if not genre:
                    continue  # Skip empty genres
                    
                genre_data.append({
                    'name': genre,
                    'artist_count': '?',
                    'album_count': '?'
                })

            # Sort genres alphabetically
            genre_data.sort(key=lambda x: x['name'].lower())
            print(f"[DEBUG] Returning {len(genre_data)} genres", flush=True)
            
            # Disconnect BEFORE returning to avoid response corruption
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            
            return jsonify({'status': 'success', 'genres': genre_data, 'count': len(genre_data)})

        except Exception as e:
            # Disconnect on error too
            if client:
                try:
                    client.disconnect()
                except:
                    pass
            
            import traceback
            print(f"[DEBUG] Exception in /api/browse/genres (attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {e}", flush=True)
            
            # If this is not the last retry, wait and try again
            if attempt < max_retries - 1:
                print(f"[DEBUG] Retrying in {retry_delay}s...", flush=True)
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                # Last retry failed, return error
                traceback.print_exc()
                return jsonify({'status': 'error', 'message': f'Error fetching genres: {str(e)}'}), 500
                return jsonify({'status': 'error', 'message': f'Error fetching genres: {str(e)}'}), 500


def api_browse_artists_handler(app_ctx):
    """Handle /api/browse/artists route"""
    connect_mpd_client = app_ctx['connect_mpd_client']
    
    genre = request.args.get('genre', '').strip()
    print(f"[DEBUG] /api/browse/artists called with genre='{genre}'", flush=True)
    
    if not genre:
        return jsonify({'status': 'error', 'message': 'Missing genre parameter'}), 400

    client = connect_mpd_client()
    if not client:
        return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500

    try:
        # Get all songs for this genre
        all_songs = client.find('genre', genre)
        print(f"[DEBUG] Found {len(all_songs)} songs for genre '{genre}'", flush=True)
        
        artist_albums = {}  # artist_name -> set of albums
        
        for song in all_songs:
            # Prefer AlbumArtist over Artist
            albumartist_raw = song.get('albumartist')
            artist_raw = song.get('artist', 'Unknown Artist')
            
            # Handle cases where MPD returns lists
            if isinstance(albumartist_raw, list):
                albumartist_name = albumartist_raw[0] if albumartist_raw else None
            else:
                albumartist_name = albumartist_raw
            
            if isinstance(artist_raw, list):
                artist_name = artist_raw[0] if artist_raw else 'Unknown Artist'
            else:
                artist_name = artist_raw
            
            # Use AlbumArtist if available
            final_artist_name = albumartist_name or artist_name
            album_name = song.get('album', 'Unknown Album')
            
            # Handle album name if it's a list
            if isinstance(album_name, list):
                album_name = album_name[0] if album_name else 'Unknown Album'
            
            if final_artist_name not in artist_albums:
                artist_albums[final_artist_name] = set()
            artist_albums[final_artist_name].add(album_name)
        
        all_artists = list(artist_albums.keys())
        print(f"[DEBUG] Total unique artists: {len(all_artists)}", flush=True)
        
        artist_data = []
        
        for artist in all_artists:
            if not artist or str(artist).strip() == '':
                continue
                
            artist_data.append({
                'name': str(artist),
                'album_count': '?',
                'song_count': '?'
            })

        # Sort by name, ignoring leading "The"
        def sort_key_ignore_the(artist_dict):
            name = artist_dict['name'].lower()
            if name.startswith('the '):
                return name[4:]
            return name
            
        artist_data.sort(key=sort_key_ignore_the)
        print(f"[DEBUG] Returning {len(artist_data)} artists", flush=True)
        
        # Disconnect BEFORE returning
        if client:
            try:
                client.disconnect()
            except:
                pass
        
        return jsonify({'status': 'success', 'artists': artist_data, 'count': len(artist_data)})
        
    except Exception as e:
        # Disconnect on error too
        if client:
            try:
                client.disconnect()
            except:
                pass
        
        print(f"[DEBUG] Exception in /api/browse/artists: {e}", flush=True)
        return jsonify({'status': 'error', 'message': f'Error fetching artists: {str(e)}'}), 500


def api_browse_albums_handler(app_ctx):
    """Handle /api/browse/albums route"""
    connect_mpd_client = app_ctx['connect_mpd_client']
    
    artist = request.args.get('artist', '').strip()
    genre = request.args.get('genre', '').strip()
    print(f"[DEBUG] /api/browse/albums called with artist='{artist}', genre='{genre}'", flush=True)
    
    if not artist:
        return jsonify({'status': 'error', 'message': 'Missing artist parameter'}), 400

    client = connect_mpd_client()
    if not client:
        return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500

    try:
        # If genre specified, filter by it
        if genre:
            try:
                albums_by_albumartist = client.list('album', 'albumartist', artist, 'genre', genre)
                print(f"[DEBUG] Found {len(albums_by_albumartist)} albums by AlbumArtist for '{artist}' in genre '{genre}'", flush=True)
            except:
                albums_by_albumartist = []
            
            albums_by_artist = client.list('album', 'artist', artist, 'genre', genre)
            print(f"[DEBUG] Found {len(albums_by_artist)} albums by Artist for '{artist}' in genre '{genre}'", flush=True)
        else:
            try:
                albums_by_albumartist = client.list('album', 'albumartist', artist)
                print(f"[DEBUG] Found {len(albums_by_albumartist)} albums by AlbumArtist for '{artist}'", flush=True)
            except:
                albums_by_albumartist = []
            
            albums_by_artist = client.list('album', 'artist', artist)
            print(f"[DEBUG] Found {len(albums_by_artist)} albums by Artist for '{artist}'", flush=True)
        
        # Combine and deduplicate
        all_albums_raw = albums_by_albumartist + albums_by_artist
        all_albums = []
        seen_albums = set()
        
        for album_item in all_albums_raw:
            if isinstance(album_item, dict):
                album_name = album_item.get('album', '')
            else:
                album_name = album_item
            
            if album_name and album_name.lower() not in seen_albums:
                all_albums.append(album_name)
                seen_albums.add(album_name.lower())
                
        print(f"[DEBUG] Total unique albums: {len(all_albums)}", flush=True)
        
        # Group albums by directory
        album_data = []
        for album in all_albums:
            if not album or str(album).strip() == '':
                continue
                
            try:
                # Try AlbumArtist first
                songs_by_albumartist = []
                try:
                    songs_by_albumartist = client.find('albumartist', artist, 'album', album)
                except:
                    pass
                    
                if not songs_by_albumartist:
                    songs = client.find('artist', artist, 'album', album)
                else:
                    songs = songs_by_albumartist
                
                # Group songs by directory
                albums_by_dir = {}
                for song in songs:
                    song_file = song.get('file', '')
                    album_dir = os.path.dirname(song_file) if song_file else ''
                    
                    if album_dir not in albums_by_dir:
                        albums_by_dir[album_dir] = {
                            'songs': [],
                            'date': song.get('date', ''),
                            'sample_file': song_file
                        }
                    albums_by_dir[album_dir]['songs'].append(song)
                
                # Add entry for each directory
                for album_dir, dir_data in albums_by_dir.items():
                    album_data.append({
                        'album': str(album),
                        'artist': str(artist),
                        'track_count': len(dir_data['songs']),
                        'date': str(dir_data['date']),
                        'sample_file': str(dir_data['sample_file'])
                    })
                    
            except Exception as e:
                print(f"[DEBUG] Error getting info for album '{album}': {e}")
                continue
        
        # Sort by album name
        album_data.sort(key=lambda x: x['album'].lower())
        
        # Disconnect BEFORE returning
        if client:
            try:
                client.disconnect()
            except:
                pass
        
        return jsonify({'status': 'success', 'albums': album_data, 'count': len(album_data)})
        
    except Exception as e:
        # Disconnect on error too
        if client:
            try:
                client.disconnect()
            except:
                pass
        
        print(f"[DEBUG] Exception in /api/browse/albums: {e}", flush=True)
        return jsonify({'status': 'error', 'message': f'Error fetching albums: {str(e)}'}), 500


def api_album_tracks_handler(app_ctx):
    """Handle /api/album_tracks route"""
    connect_mpd_client = app_ctx['connect_mpd_client']
    organize_album_by_disc = app_ctx['organize_album_by_disc']
    
    album = request.args.get('album', '')
    artist = request.args.get('artist', '').strip()
    print(f"[DEBUG] /api/album_tracks called with album='{album}', artist='{artist}'")
    
    if not album or not album.strip():
        print("[DEBUG] Missing album parameter")
        return jsonify({'status': 'error', 'message': 'Missing album parameter'}), 400

    client = None
    try:
        client = connect_mpd_client()
        if not client:
            print("[DEBUG] Could not connect to MPD")
            return jsonify({'status': 'error', 'message': 'Could not connect to MPD'}), 500

        # If artist specified, search by both
        if artist:
            tracks = client.find('album', album, 'artist', artist)
            print(f"[DEBUG] Album+Artist exact search returned {len(tracks) if tracks else 0} tracks")
            
            # If no exact match, try with trailing space
            if not tracks:
                tracks = client.find('album', album + ' ', 'artist', artist)
                print(f"[DEBUG] Album+Artist search with trailing space returned {len(tracks) if tracks else 0} tracks")
        else:
            # No artist - search by album only
            tracks = client.find('album', album)
            print(f"[DEBUG] Album-only exact search returned {len(tracks) if tracks else 0} tracks")
            
            # If no results, try with trailing space
            if not tracks:
                tracks = client.find('album', album + ' ')
                print(f"[DEBUG] Album-only search with trailing space returned {len(tracks) if tracks else 0} tracks")
        
        print(f"[DEBUG] Final track count: {len(tracks) if tracks else 0}", flush=True)
        
        if not tracks:
            print("[DEBUG] No tracks found for given album", flush=True)
            return jsonify({'status': 'error', 'message': 'No tracks found for this album'}), 404
        
        # Check if multi-disc
        disc_structure = organize_album_by_disc(tracks)
        
        # Sort tracks by track number
        def get_track_number(track):
            track_num = track.get('track', '0')
            try:
                return int(track_num.split('/')[0])
            except (ValueError, AttributeError):
                return 0
        
        tracks.sort(key=get_track_number)
        
        # Only return relevant fields
        track_list = []
        for idx, track in enumerate(tracks):
            track_list.append({
                'title': track.get('title', f'Track {idx+1}'),
                'file': track.get('file', ''),
                'time': track.get('time', None),
                'artist': track.get('artist', ''),
                'track': track.get('track', str(idx+1))
            })
        
        # Build response
        response = {
            'status': 'success',
            'tracks': track_list
        }
        
        if disc_structure and len(disc_structure) > 1:
            print(f"[DEBUG] Multi-disc album detected: {len(disc_structure)} discs", flush=True)
            # Convert to serializable format
            disc_structure_serializable = {}
            for disc_num, disc_tracks in disc_structure.items():
                disc_structure_serializable[str(disc_num)] = [
                    {
                        'title': track.get('title', ''),
                        'file': track.get('file', ''),
                        'time': track.get('time', None),
                        'artist': track.get('artist', ''),
                        'track': track.get('track', '')
                    }
                    for track in disc_tracks
                ]
            response['disc_structure'] = disc_structure_serializable
        
        print(f"[DEBUG] Returning {len(track_list)} tracks" + 
              (f" organized into {len(disc_structure)} discs" if disc_structure and len(disc_structure) > 1 else ""), 
              flush=True)
        
        # Disconnect BEFORE returning
        if client:
            try:
                client.disconnect()
            except:
                pass
        
        return jsonify(response)
        
    except Exception as e:
        # Disconnect on error too
        if client:
            try:
                client.disconnect()
            except:
                pass
        
        print(f"[DEBUG] Exception in /api/album_tracks: {e}", flush=True)
        return jsonify({'status': 'error', 'message': f'Error fetching tracks: {str(e)}'}), 500


def recent_albums_page_handler(app_ctx):
    """Display the recent albums page."""
    return render_template('recent_albums.html')
