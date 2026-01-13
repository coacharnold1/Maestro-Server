#!/usr/bin/env python3
"""
Test exact artist name matching between Last.fm and MPD
"""
import requests
import os
import json
from musicpd import MPDClient

# Load Last.fm API key
settings_path = '/home/fausto/maestro/settings.json'
LASTFM_API_KEY = ''
if os.path.exists(settings_path):
    with open(settings_path, 'r') as f:
        settings = json.load(f)
        LASTFM_API_KEY = settings.get('lastfm_api_key', '')

LASTFM_API_URL = 'https://ws.audioscrobbler.com/2.0/'

def get_similar_artists(artist_name, limit=30):
    params = {
        'method': 'artist.getsimilar',
        'artist': artist_name,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': limit
    }
    response = requests.get(LASTFM_API_URL, params=params, timeout=10)
    data = response.json()
    
    artists = []
    if 'similarartists' in data and 'artist' in data['similarartists']:
        for artist_data in data['similarartists']['artist']:
            artists.append(artist_data.get('name', 'Unknown'))
    return artists

def connect_mpd():
    client = MPDClient()
    client.connect('localhost', 6600)
    return client

def normalize(name):
    """Simple normalization - lowercase, strip, remove 'the'"""
    n = name.lower().strip()
    if n.startswith('the '):
        n = n[4:]
    return n

def test_exact_matches(seed_artist):
    print(f"\n{'='*80}")
    print(f"EXACT NAME MATCHING TEST")
    print(f"{'='*80}\n")
    
    # Get similar artists from Last.fm
    similar_artists = get_similar_artists(seed_artist, limit=30)
    print(f"Last.fm returned {len(similar_artists)} similar artists\n")
    
    # Connect to MPD and get all artists
    client = connect_mpd()
    all_mpd_artists = client.list('artist')
    print(f"MPD has {len(all_mpd_artists)} total artists\n")
    
    # Create normalized lookup
    mpd_normalized = {}
    for artist in all_mpd_artists:
        if artist:
            mpd_normalized[normalize(artist)] = artist
    
    print(f"{'Last.fm Name':<45} {'Exact?':<8} {'MPD Has':<8} {'MPD Name'}")
    print(f"{'-'*80}")
    
    exact_matches = 0
    fuzzy_matches = 0
    no_matches = 0
    
    for lastfm_artist in similar_artists:
        # Try exact match first
        try:
            tracks_exact = client.find('artist', lastfm_artist)
            if tracks_exact:
                exact_matches += 1
                print(f"{lastfm_artist:<45} {'✓':<8} {'Yes':<8} {lastfm_artist}")
                continue
        except:
            pass
        
        # Try normalized/fuzzy match
        norm_lastfm = normalize(lastfm_artist)
        if norm_lastfm in mpd_normalized:
            fuzzy_matches += 1
            mpd_name = mpd_normalized[norm_lastfm]
            print(f"{lastfm_artist:<45} {'✗':<8} {'Fuzzy':<8} {mpd_name}")
        else:
            no_matches += 1
            print(f"{lastfm_artist:<45} {'✗':<8} {'No':<8} -")
    
    client.disconnect()
    
    print(f"\n{'-'*80}")
    print(f"Summary:")
    print(f"  • Exact matches (code will find): {exact_matches}")
    print(f"  • Fuzzy matches (code will miss): {fuzzy_matches}")
    print(f"  • Not in library: {no_matches}")
    print(f"  • Total: {exact_matches + fuzzy_matches + no_matches}")
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    import sys
    artist = sys.argv[1] if len(sys.argv) > 1 else "Supertramp"
    test_exact_matches(artist)
