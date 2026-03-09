"""
Debug route handlers for Maestro Server.

Handles development/debugging endpoints for:
- Album artist inspection
- Album metadata tags
- Genre organization
- Album search debugging
"""


# ============================================================================
# Debug Routes
# ============================================================================

def debug_albumartists_handler(app_ctx):
    """Debug route to see what AlbumArtist values MPD has."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    
    client = None
    try:
        client = connect_mpd_client()
        if not client:
            return "Could not connect to MPD"
        
        # Get all AlbumArtist values
        all_albumartists_raw = client.list('albumartist')
        
        # Handle both string and dict responses
        all_albumartists = []
        for item in all_albumartists_raw:
            if isinstance(item, dict):
                albumartist = item.get('albumartist', '')
            else:
                albumartist = item
            if albumartist:
                all_albumartists.append(str(albumartist))
        
        output = f"Total AlbumArtist entries: {len(all_albumartists)}<br><br>"
        for aa in sorted(set(all_albumartists)):
            output += f"'{aa}'<br>"
        
        return output
    except Exception as e:
        return f"Error: {e}"
    finally:
        if client:
            try:
                client.disconnect()
            except:
                pass


def debug_album_handler(app_ctx, album_name):
    """Debug specific album to see its Artist vs AlbumArtist tags."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    
    client = None
    try:
        client = connect_mpd_client()
        if not client:
            return "Could not connect to MPD"
        
        # Find all songs from this album
        songs = client.find('album', album_name)
        
        output = f"<h2>Debug: '{album_name}'</h2>"
        output += f"Found {len(songs)} songs<br><br>"
        
        artists = set()
        albumartists = set()
        
        for i, song in enumerate(songs[:10]):  # Show first 10 tracks
            artist = song.get('artist', 'N/A')
            albumartist = song.get('albumartist', 'N/A')
            title = song.get('title', 'N/A')
            
            artists.add(artist)
            albumartists.add(albumartist)
            
            output += f"Track {i+1}: {title}<br>"
            output += f"&nbsp;&nbsp;Artist: '{artist}'<br>"
            output += f"&nbsp;&nbsp;AlbumArtist: '{albumartist}'<br><br>"
        
        output += f"<h3>Summary:</h3>"
        output += f"Unique Artists: {list(artists)}<br>"
        output += f"Unique AlbumArtists: {list(albumartists)}<br>"
        
        return output
    except Exception as e:
        return f"Error: {e}"
    finally:
        if client:
            try:
                client.disconnect()
            except:
                pass


def debug_album_genre_handler(app_ctx, album_name):
    """Debug what genre(s) an album is tagged with."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    
    client = None
    try:
        client = connect_mpd_client()
        if not client:
            return "Could not connect to MPD"
        
        # Find all songs from this album
        songs = client.find('album', album_name)
        
        output = f"<h2>Genre Debug: '{album_name}'</h2>"
        output += f"Found {len(songs)} songs<br><br>"
        
        genres = set()
        artists = set()
        albumartists = set()
        
        for i, song in enumerate(songs[:10]):  # Show first 10 tracks
            genre = song.get('genre', 'N/A')
            artist = song.get('artist', 'N/A')
            albumartist = song.get('albumartist', 'N/A')
            title = song.get('title', 'N/A')
            
            genres.add(genre)
            artists.add(artist)
            albumartists.add(albumartist)
            
            output += f"Track {i+1}: {title}<br>"
            output += f"&nbsp;&nbsp;Genre: '{genre}'<br>"
            output += f"&nbsp;&nbsp;Artist: '{artist}'<br>"
            output += f"&nbsp;&nbsp;AlbumArtist: '{albumartist}'<br><br>"
        
        output += f"<h3>Summary:</h3>"
        output += f"Unique Genres: {list(genres)}<br>"
        output += f"Unique Artists: {list(artists)}<br>"
        output += f"Unique AlbumArtists: {list(albumartists)}<br>"
        
        return output
    except Exception as e:
        return f"Error: {e}"
    finally:
        if client:
            try:
                client.disconnect()
            except:
                pass


def debug_album_search_handler(app_ctx, search_term):
    """Debug albums containing a search term to see their tags."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    
    client = None
    try:
        client = connect_mpd_client()
        if not client:
            return "Could not connect to MPD"
        
        # Find songs with album names containing the search term
        all_songs = client.search('album', search_term)
        
        output = f"<h2>Album Search Debug: '{search_term}'</h2>"
        output += f"Found {len(all_songs)} songs<br><br>"
        
        albums_info = {}  # album_name -> {genres, artists, albumartists}
        
        for song in all_songs:
            album = song.get('album', 'Unknown Album')
            genre = song.get('genre', 'N/A')
            artist = song.get('artist', 'N/A')
            albumartist = song.get('albumartist', 'N/A')
            
            if album not in albums_info:
                albums_info[album] = {'genres': set(), 'artists': set(), 'albumartists': set()}
            
            albums_info[album]['genres'].add(genre)
            albums_info[album]['artists'].add(artist)
            albums_info[album]['albumartists'].add(albumartist)
        
        for album, info in albums_info.items():
            output += f"<h3>Album: '{album}'</h3>"
            output += f"Genres: {list(info['genres'])}<br>"
            output += f"Artists: {list(info['artists'])[:10]}{'...' if len(info['artists']) > 10 else ''}<br>"
            output += f"AlbumArtists: {list(info['albumartists'])}<br><br>"
        
        return output
    except Exception as e:
        return f"Error: {e}"
    finally:
        if client:
            try:
                client.disconnect()
            except:
                pass


def debug_genre_various_artists_handler(app_ctx, genre_name):
    """Debug which Various Artists albums are in a specific genre."""
    connect_mpd_client = app_ctx['connect_mpd_client']
    
    client = None
    try:
        client = connect_mpd_client()
        if not client:
            return "Could not connect to MPD"
        
        # Find all songs in this genre where AlbumArtist = "Various Artists"
        all_songs = client.find('genre', genre_name, 'albumartist', 'Various Artists')
        
        output = f"<h2>Various Artists Albums in '{genre_name}' Genre</h2>"
        output += f"Found {len(all_songs)} songs<br><br>"
        
        albums_info = {}  # album_name -> song count
        
        for song in all_songs:
            album = song.get('album', 'Unknown Album')
            if album not in albums_info:
                albums_info[album] = 0
            albums_info[album] += 1
        
        output += f"<h3>Albums found:</h3>"
        for album, song_count in albums_info.items():
            output += f"• <strong>{album}</strong> ({song_count} songs)<br>"
        
        if not albums_info:
            output += "<em>No Various Artists albums found in this genre.</em><br><br>"
        
        return output
    except Exception as e:
        return f"Error: {e}"
    finally:
        if client:
            try:
                client.disconnect()
            except:
                pass
