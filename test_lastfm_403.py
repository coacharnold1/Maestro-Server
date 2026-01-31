#!/usr/bin/env python3
"""
Diagnostic script to test Last.fm API 403 error
"""
import json
import os
import sys
import hashlib
import requests
from datetime import datetime

# Load settings
def load_settings():
    settings_file = 'settings.json'
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            return json.load(f)
    return {}

settings = load_settings()

# Get credentials from env or settings
LASTFM_API_KEY = os.environ.get('LASTFM_API_KEY', '') or settings.get('lastfm_api_key', '')
LASTFM_SHARED_SECRET = os.environ.get('LASTFM_SHARED_SECRET', '') or settings.get('lastfm_shared_secret', '')
LASTFM_SESSION_KEY = os.environ.get('LASTFM_SESSION_KEY', '') or settings.get('lastfm_session_key', '')

LASTFM_API_URL = 'https://ws.audioscrobbler.com/2.0/'

print("=" * 70)
print(f"Last.fm API Diagnostic Test - {datetime.now()}")
print("=" * 70)
print()

# Check credentials
print("Configuration Status:")
print(f"  ✓ API Key set: {bool(LASTFM_API_KEY)}")
print(f"  ✓ Secret set: {bool(LASTFM_SHARED_SECRET)}")
print(f"  ✓ Session Key set: {bool(LASTFM_SESSION_KEY)}")
print()

if not LASTFM_API_KEY:
    print("ERROR: LASTFM_API_KEY not configured!")
    sys.exit(1)

if not LASTFM_SHARED_SECRET:
    print("ERROR: LASTFM_SHARED_SECRET not configured!")
    sys.exit(1)

if not LASTFM_SESSION_KEY:
    print("ERROR: LASTFM_SESSION_KEY not configured!")
    print("You need to authenticate first by visiting /settings and completing Last.fm auth")
    sys.exit(1)

# Test API signature
def sign_params(params):
    """Create Last.fm API signature"""
    sorted_keys = sorted(params.keys())
    string = ''.join([f"{k}{params[k]}" for k in sorted_keys])
    string += LASTFM_SHARED_SECRET
    return hashlib.md5(string.encode()).hexdigest()

# Test 1: Simple API call with session key
print("Test 1: Fetching Top Artists (requires valid session key)...")
params = {
    'method': 'user.getTopArtists',
    'api_key': LASTFM_API_KEY,
    'sk': LASTFM_SESSION_KEY,
    'period': 'overall',
    'limit': '10',
    'format': 'json'
}
params['api_sig'] = sign_params(params)

print(f"  API Key (first 10 chars): {LASTFM_API_KEY[:10]}...")
print(f"  Session Key (first 10 chars): {LASTFM_SESSION_KEY[:10]}...")
print(f"  Request URL: {LASTFM_API_URL}")
print(f"  Method: user.getTopArtists")
print()

try:
    response = requests.post(LASTFM_API_URL, data=params, timeout=10)
    print(f"  HTTP Status: {response.status_code}")
    
    if response.status_code == 403:
        print("  ✗ Got 403 Forbidden!")
        print()
        print("Possible causes:")
        print("  1. API key has been revoked or disabled")
        print("  2. Session key has expired (valid for ~1 month)")
        print("  3. Last.fm account has been locked/limited")
        print()
    elif response.status_code == 400:
        print("  ✗ Got 400 Bad Request!")
    elif response.status_code == 200:
        print("  ✓ Got 200 OK!")
        data = response.json()
        if 'error' in data:
            print(f"  Last.fm API Error: {data.get('error')} - {data.get('message')}")
        else:
            artists = data.get('topartists', {}).get('artist', [])
            print(f"  ✓ Successfully fetched {len(artists)} top artists")
    else:
        print(f"  Unexpected status code!")
    
    print()
    print(f"  Response headers:")
    for k, v in response.headers.items():
        if k.lower() in ['content-type', 'date', 'server', 'connection']:
            print(f"    {k}: {v}")
    
    print()
    print(f"  Response body (first 500 chars):")
    print(f"    {response.text[:500]}")
    
except Exception as e:
    print(f"  ✗ Request failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("Recommendations:")
print("  1. Check if API key is valid: https://www.last.fm/api/account/api_key_create")
print("  2. Regenerate session by visiting /settings → Last.fm Auth")
print("  3. Verify Last.fm account is not restricted")
print("  4. Compare API keys between production and test servers")
print("=" * 70)
