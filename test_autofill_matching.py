#!/usr/bin/env python3
"""
Test autofill matching - shows which similar artists are in your MPD library
and how many tracks each has
"""
import requests
import sys
import os
import json
from musicpd import MPDClient

# Load Last.fm API key
LASTFM_API_KEY = ''
settings_path = '/home/fausto/maestro/settings.json'
if os.path.exists(settings_path):
    with open(settings_path, 'r') as f:
        settings = json.load(f)
        LASTFM_API_KEY = settings.get('lastfm_api_key', '')

LASTFM_API_URL = 'https://ws.audioscrobbler.com/2.0/'

def get_similar_artists(artist_name, limit=30):
    """Get similar artists from Last.fm"""
    params = {
        'method': 'artist.getsimilar',
        'artist': artist_name,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': limit
    }
    
    response = requests.get(LASTFM_API_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    artists = []
    if 'similarartists' in data and 'artist' in data['similarartists']:
        for artist_data in data['similarartists']['artist']:
            artists.append({
                'name': artist_data.get('name', 'Unknown'),
                'match': float(artist_data.get('match', 0)) * 100
            })
    return artists

def connect_mpd():
    """Connect to MPD"""
    client = MPDClient()
    try:
        client.connect('localhost', 6600)
        return client
    except Exception as e:
        print(f"Error connecting to MPD: {e}")
        return None

def test_autofill_matching(seed_artist):
    """Test which similar artists are available in your library"""
    
    if not LASTFM_API_KEY:
        print("ERROR: LASTFM_API_KEY not set")
        sys.exit(1)
    
    print(f"\n{'='*80}")
    print(f"AUTOFILL MATCHING TEST")
    print(f"{'='*80}")
    print(f"Seed Artist: {seed_artist}")
    print(f"{'='*80}\n")
    
    # Get similar artists from Last.fm
    print("Fetching similar artists from Last.fm...")
    similar_artists = get_similar_artists(seed_artist, limit=30)
    print(f"✓ Found {len(similar_artists)} similar artists\n")
    
    # Connect to MPD
    print("Connecting to MPD...")
    client = connect_mpd()
    if not client:
        print("✗ Could not connect to MPD")
        sys.exit(1)
    print("✓ Connected to MPD\n")
    
    # Check which artists are in your library
    print(f"{'Rank':<6} {'Match %':<10} {'Artist Name':<40} {'Tracks'}")
    print(f"{'-'*80}")
    
    total_available = 0
    artists_with_tracks = []
    
    for idx, artist_data in enumerate(similar_artists, 1):
        artist_name = artist_data['name']
        match_pct = artist_data['match']
        
        try:
            # Search for tracks by this artist
            tracks = client.find('artist', artist_name)
            track_count = len(tracks)
            
            if track_count > 0:
                total_available += 1
                artists_with_tracks.append((artist_name, track_count))
                status = f"{track_count} tracks"
            else:
                status = "Not in library"
            
            print(f"{idx:<6} {match_pct:>6.2f}%    {artist_name:<40} {status}")
            
        except Exception as e:
            print(f"{idx:<6} {match_pct:>6.2f}%    {artist_name:<40} Error: {e}")
    
    client.disconnect()
    
    print(f"\n{'-'*80}")
    print(f"Summary:")
    print(f"  • Similar artists from Last.fm: {len(similar_artists)}")
    print(f"  • Available in your library: {total_available} ({total_available/len(similar_artists)*100:.1f}%)")
    print(f"{'='*80}\n")
    
    if artists_with_tracks:
        print("Top 10 similar artists by track count in your library:")
        print(f"{'Artist':<50} {'Tracks'}")
        print(f"{'-'*80}")
        artists_with_tracks.sort(key=lambda x: x[1], reverse=True)
        for artist_name, track_count in artists_with_tracks[:10]:
            print(f"{artist_name:<50} {track_count}")
        print()

if __name__ == '__main__':
    artist = sys.argv[1] if len(sys.argv) > 1 else "Supertramp"
    test_autofill_matching(artist)
