#!/usr/bin/env python3
"""
Bandcamp API Client for Maestro
Handles authentication and API calls to Bandcamp
"""

import requests
import json
import hashlib
from typing import Dict, List, Optional
import time

class BandcampClient:
    """Client for interacting with Bandcamp API"""
    
    BASE_URL = 'https://bandcamp.com/'
    API_COLLECTION = BASE_URL + 'api/fancollection/1/'
    API_ALBUM = BASE_URL + 'api/album/2/info'
    API_TRACK = BASE_URL + 'api/track/3/info'
    API_KEY = 'perladruslasaemingserligr'  # From LMS Bandcamp plugin
    
    def __init__(self, username: str, identity_token: str):
        """
        Initialize Bandcamp client
        
        Args:
            username: Bandcamp username
            identity_token: Identity token from browser cookies
        """
        self.username = username
        self.identity_token = identity_token
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://bandcamp.com/',
        })
        # Set the identity cookie for all requests
        self.session.cookies.set('identity', identity_token, domain='bandcamp.com', path='/')
        self._cache = {}
        self._fan_id = None  # Cache the fan_id
    
    def _make_request(self, url: str, method: str = 'GET', data: Optional[Dict] = None, 
                      cookies: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request to Bandcamp API
        
        Args:
            url: API endpoint URL
            method: HTTP method (GET or POST)
            data: Request data for POST
            cookies: Cookies to include
            
        Returns:
            JSON response dict or None on error
        """
        try:
            # Always include identity cookie in header
            headers = {
                'Cookie': f'identity={self.identity_token}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            if method == 'POST':
                headers['Content-Type'] = 'application/json'
                response = self.session.post(
                    url, 
                    json=data,
                    headers=headers,
                    timeout=10
                )
            else:
                response = self.session.get(url, headers=headers, timeout=10)
            
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                print(f"Non-JSON response from {url}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Bandcamp API error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return None
    
    def get_fan_id(self) -> Optional[str]:
        """
        Get fan ID from Bandcamp API using collection_summary endpoint
        
        Returns:
            Fan ID string or None
        """
        # Check cache first
        if self._fan_id:
            return self._fan_id
            
        try:
            # Call collection_summary to get the actual fan_id
            url = self.BASE_URL + 'api/fan/2/collection_summary'
            
            # Set cookie in header
            headers = {
                'Cookie': f'identity={self.identity_token}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            response = self.session.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"[ERROR] Failed to get collection_summary: {response.status_code}")
                return None
            
            result = response.json()
            
            if result.get('error'):
                print(f"[ERROR] API error: {result.get('error_message')}")
                return None
            
            fan_id = result.get('fan_id')
            if fan_id:
                print(f"[DEBUG] Got fan_id from API: {fan_id}")
                self._fan_id = str(fan_id)
                return self._fan_id
            
            print("[ERROR] No fan_id in response")
            return None
            
        except Exception as e:
            print(f"[ERROR] Exception getting fan_id: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_collection(self, count: int = 5000, older_than_token: Optional[str] = None) -> List[Dict]:
        """
        Get user's purchased album collection
        
        Args:
            count: Number of items to fetch
            older_than_token: Pagination token
            
        Returns:
            List of album dictionaries
        """
        fan_id = self.get_fan_id()
        if not fan_id:
            return []
        
        if older_than_token is None:
            older_than_token = f"{int(time.time())}:0:a::"
        
        url = self.API_COLLECTION + 'collection_items'
        data = {
            'fan_id': fan_id,
            'older_than_token': older_than_token,
            'count': count
        }
        
        result = self._make_request(url, method='POST', data=data)
        
        if not result:
            return []
        
        albums = []
        items = result.get('items', [])
        
        for item in items:
            # Extract album info
            album_data = {
                'type': 'album',
                'band_name': item.get('band_name', ''),
                'album_title': item.get('album_title', ''),
                'item_title': item.get('item_title', ''),
                'item_url': item.get('item_url', ''),
                'album_id': item.get('album_id'),
                'band_id': item.get('band_id'),
                'tralbum_type': item.get('tralbum_type', 'a'),  # 'a' for album, 't' for track
                'art_id': item.get('item_art_id'),
                'purchased': item.get('purchased'),
            }
            albums.append(album_data)
        
        return albums
    
    def get_album_info(self, album_id: int) -> Optional[Dict]:
        """
        Get detailed information about an album including tracks
        
        Args:
            album_id: Bandcamp album ID
            
        Returns:
            Album info dict with tracks
        """
        url = f"{self.API_ALBUM}?key={self.API_KEY}&album_id={album_id}"
        result = self._make_request(url)
        
        if not result:
            return None
        
        # Parse album data
        album = {
            'album_id': result.get('id'),
            'title': result.get('title', ''),
            'artist': result.get('artist', ''),
            'band_id': result.get('band_id'),
            'url': result.get('url', ''),
            'art_id': result.get('art_id'),
            'tracks': []
        }
        
        # Parse tracks - streaming URLs are already included!
        tracks_data = result.get('tracks', [])
        for track in tracks_data:
            streaming_url = track.get('streaming_url')
            if streaming_url:
                track_info = {
                    'track_id': track.get('track_id'),
                    'title': track.get('title', ''),
                    'track_num': track.get('number'),
                    'duration': track.get('duration'),
                    'streaming_url': streaming_url,
                    'album': album['title'],
                    'artist': album['artist'],
                }
                album['tracks'].append(track_info)
        
        return album
    
    def get_track_info(self, track_id: int) -> Optional[Dict]:
        """
        Get information about a specific track
        
        Args:
            track_id: Bandcamp track ID
            
        Returns:
            Track info dict with streaming URL
        """
        url = f"{self.API_TRACK}?key={self.API_KEY}&track_id={track_id}"
        result = self._make_request(url)
        
        if not result:
            return None
        
        # Extract streaming URL
        streaming_url = None
        if result.get('streaming_url'):
            streaming_url = result['streaming_url']
        elif result.get('file'):
            # Try to get MP3-128 stream
            file_data = result['file']
            if isinstance(file_data, dict):
                streaming_url = file_data.get('mp3-128')
        
        track = {
            'track_id': result.get('id'),
            'title': result.get('title', ''),
            'artist': result.get('artist', ''),
            'album': result.get('album_title', ''),
            'track_num': result.get('track_num'),
            'duration': result.get('duration'),
            'streaming_url': streaming_url,
            'art_id': result.get('art_id'),
        }
        
        return track
    
    def get_artwork_url(self, art_id: int, size: int = 5) -> str:
        """
        Generate artwork URL from art ID
        
        Args:
            art_id: Bandcamp artwork ID
            size: Size code (2=350x350, 5=700x700, 10=1200x1200)
            
        Returns:
            Artwork URL
        """
        if not art_id:
            return ''
        
        # Pad art_id to 10 digits
        padded_id = str(art_id).zfill(10)
        return f"https://f4.bcbits.com/img/a{padded_id}_{size}.jpg"
    
    def search(self, query: str, search_type: str = 'albums') -> List[Dict]:
        """
        Search Bandcamp (placeholder - would require web scraping)
        
        Args:
            query: Search query
            search_type: Type of search ('albums', 'artists', 'tracks')
            
        Returns:
            List of search results
        """
        # TODO: Implement search via web scraping or discover API
        # Bandcamp doesn't have a public search API
        print(f"Search not yet implemented: {query}")
        return []


def test_client():
    """Test the Bandcamp client"""
    # This would use credentials from settings
    client = BandcampClient("test_user", "test_token")
    
    # Test collection fetch
    collection = client.get_collection(count=10)
    print(f"Found {len(collection)} items in collection")
    
    for item in collection[:3]:
        print(f"  - {item['band_name']}: {item['album_title']}")


if __name__ == '__main__':
    test_client()
