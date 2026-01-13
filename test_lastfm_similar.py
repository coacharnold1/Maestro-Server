#!/usr/bin/env python3
"""
Test Last.fm Similar Artists API for debugging autofill issues
"""
import requests
import sys
import os
import json

# Try multiple sources for API key
LASTFM_API_KEY = ''

# 1. Try environment variable
LASTFM_API_KEY = os.environ.get('LASTFM_API_KEY', '')

# 2. Try config.env
if not LASTFM_API_KEY:
    try:
        from dotenv import load_dotenv
        load_dotenv('config.env')
        LASTFM_API_KEY = os.environ.get('LASTFM_API_KEY', '')
    except ImportError:
        pass

# 3. Try live settings.json
if not LASTFM_API_KEY:
    try:
        settings_path = '/home/fausto/maestro/settings.json'
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = json.load(f)
                LASTFM_API_KEY = settings.get('lastfm_api_key', '')
    except Exception as e:
        print(f"Note: Could not read live settings: {e}")

LASTFM_API_URL = 'https://ws.audioscrobbler.com/2.0/'

def test_similar_artists(artist_name, limit=20):
    """Test the similar artists endpoint"""
    
    if not LASTFM_API_KEY:
        print("ERROR: LASTFM_API_KEY not set in config.env")
        print("Please set it in config.env or export LASTFM_API_KEY=your_key")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"Testing Last.fm Similar Artists API")
    print(f"{'='*70}")
    print(f"Artist: {artist_name}")
    print(f"Limit: {limit}")
    print(f"{'='*70}\n")
    
    params = {
        'method': 'artist.getsimilar',
        'artist': artist_name,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': limit
    }
    
    try:
        print(f"Making request to Last.fm API...")
        response = requests.get(LASTFM_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'similarartists' in data and 'artist' in data['similarartists']:
            artists = data['similarartists']['artist']
            
            print(f"\n✓ SUCCESS: Found {len(artists)} similar artists\n")
            print(f"{'Rank':<6} {'Match %':<10} {'Artist Name'}")
            print(f"{'-'*70}")
            
            for idx, artist_data in enumerate(artists, 1):
                name = artist_data.get('name', 'Unknown')
                match = artist_data.get('match', '0')
                # Convert match to percentage
                match_pct = float(match) * 100
                print(f"{idx:<6} {match_pct:>6.2f}%    {name}")
            
            print(f"\n{'-'*70}")
            print(f"Total: {len(artists)} artists returned")
            print(f"{'='*70}\n")
            
            return artists
        else:
            print(f"\n✗ ERROR: Unexpected response format")
            print(f"Response: {data}")
            return []
            
    except requests.exceptions.HTTPError as he:
        print(f"\n✗ HTTP ERROR: {he}")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 403:
            print("This might be an invalid API key or rate limit issue")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    artist = sys.argv[1] if len(sys.argv) > 1 else "Supertramp"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    test_similar_artists(artist, limit)
