from mpd import MPDClient, ConnectionError

def perform_search(client, search_tag, query):
    print(f"DEBUG: Search tag received: '{search_tag}'")
    
    try:
        results = client.search(search_tag, query)
        print(f"DEBUG: MPD returned {len(results)} raw results.")

        if search_tag in ['artist', 'album']:
            print("DEBUG: Processing as album search.")
            unique_albums = {}
            for song in results:
                artist_name_raw = song.get('artist', 'Unknown Artist')
                if isinstance(artist_name_raw, list):
                    artist_name = ", ".join(artist_name_raw)
                else:
                    artist_name = artist_name_raw

                album_name_raw = song.get('album', 'Unknown Album')
                if isinstance(album_name_raw, list):
                    album_name = ", ".join(album_name_raw)
                else:
                    album_name = album_name_raw

                album_key = (artist_name, album_name)
                
                # Store the first song file we find for this album (for album art lookup)
                if album_key not in unique_albums:
                    unique_albums[album_key] = song.get('file', '')

            formatted_results = []
            for (artist, album), sample_file in unique_albums.items():
                formatted_results.append({
                    'item_type': 'album',
                    'artist': artist,
                    'album': album,
                    'sample_file': sample_file
                })
            
            # Sort by artist (ignoring "The"), then by album
            def sort_key_ignore_the(item):
                artist = item['artist'].lower()
                album = item['album'].lower()
                # If artist starts with "the " (case insensitive), ignore it for sorting
                if artist.startswith('the '):
                    artist = artist[4:]  # Remove "the "
                return (artist, album)
                
            formatted_results.sort(key=sort_key_ignore_the)
            print(f"DEBUG: Returning {len(formatted_results)} unique albums.")
            return formatted_results

        else:
            print("DEBUG: Processing as song search.")
            formatted_results = []
            for song in results:
                artist_name_raw = song.get('artist', 'Unknown Artist')
                if isinstance(artist_name_raw, list):
                    artist_name = ", ".join(artist_name_raw)
                else:
                    artist_name = artist_name_raw
                    
                album_name_raw = song.get('album', 'Unknown Album')
                if isinstance(album_name_raw, list):
                    album_name = ", ".join(album_name_raw)
                else:
                    album_name = album_name_raw
                
                formatted_results.append({
                    'item_type': 'song',
                    'artist': artist_name,
                    'title': song.get('title', 'Unknown Title'),
                    'album': album_name,
                    'file': song.get('file', ''),
                    'length': song.get('time', '0'),
                })
            print(f"DEBUG: Returning {len(formatted_results)} songs.")
            return formatted_results
    except Exception as e:
        print(f"An error occurred during MPD search: {e}")
        return []