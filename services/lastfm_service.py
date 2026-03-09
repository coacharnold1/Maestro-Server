"""
LastfmService - Encapsulates Last.fm API integration for album artwork.

Handles:
- Album artwork fetching via album.getinfo
- Track artwork fetching via track.getinfo (for streams)
- Image size selection (mega, extralarge, large, medium)
- Caching and error handling
"""

import logging
import requests
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Default HTTP headers for outbound requests
DEFAULT_HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


class LastfmService:
    """
    Service for Last.fm API integration (album artwork fetching).
    
    Provides:
    - Album artwork fetching with configurable sizes
    - Track artwork fetching for streams
    - Connection testing
    - Image URL extraction with size preference
    """
    
    LASTFM_API_URL = "https://ws.audioscrobbler.com/2.0/"
    
    def __init__(self, api_key: str = ''):
        """
        Initialize LastfmService.
        
        Args:
            api_key: Last.fm API key for authentication
        """
        self.api_key = api_key
        logger.info("LastfmService initialized")
    
    def fetch_album_artwork(self, artist: str, album: str) -> Optional[str]:
        """
        Fetch album artwork URL from Last.fm using album.getinfo.
        
        Args:
            artist: Artist name
            album: Album name
            
        Returns:
            Image URL or None if not found/error
        """
        if not artist or not album or not self.api_key:
            logger.warning(f"Missing parameters for album artwork: artist={bool(artist)}, album={bool(album)}, api_key={bool(self.api_key)}")
            return None
        
        try:
            params = {
                'method': 'album.getinfo',
                'api_key': self.api_key,
                'artist': artist,
                'album': album,
                'format': 'json'
            }
            
            logger.debug(f"Fetching album artwork for {artist} - {album} from Last.fm")
            response = requests.get(self.LASTFM_API_URL, params=params, timeout=5, headers=DEFAULT_HTTP_HEADERS)
            response.raise_for_status()
            data = response.json()
            
            # Extract image URL with size preference
            image_url = self._extract_best_image_url(data.get('album', {}))
            
            if image_url:
                logger.debug(f"Found album artwork for {artist} - {album}")
                return image_url
            else:
                logger.debug(f"No album artwork found for {artist} - {album}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching album artwork for {artist} - {album}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching album artwork for {artist} - {album}: {e}")
            return None
    
    def fetch_track_artwork(self, artist: str, track: str) -> Optional[str]:
        """
        Fetch track artwork URL from Last.fm using track.getinfo (for streams).
        
        Args:
            artist: Artist name
            track: Track title
            
        Returns:
            Image URL or None if not found/error
        """
        if not artist or not track or not self.api_key:
            logger.warning(f"Missing parameters for track artwork: artist={bool(artist)}, track={bool(track)}, api_key={bool(self.api_key)}")
            return None
        
        try:
            params = {
                'method': 'track.getinfo',
                'api_key': self.api_key,
                'artist': artist,
                'track': track,
                'format': 'json'
            }
            
            logger.debug(f"Fetching track artwork for {artist} - {track} from Last.fm")
            response = requests.get(self.LASTFM_API_URL, params=params, timeout=5, headers=DEFAULT_HTTP_HEADERS)
            response.raise_for_status()
            data = response.json()
            
            # Navigate: track -> album -> image
            track_data = data.get('track', {})
            album_data = track_data.get('album', {})
            
            # Extract image URL with size preference
            image_url = self._extract_best_image_url(album_data)
            
            if image_url:
                logger.debug(f"Found track artwork for {artist} - {track}")
                return image_url
            else:
                logger.debug(f"No track artwork found for {artist} - {track}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching track artwork for {artist} - {track}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching track artwork for {artist} - {track}: {e}")
            return None
    
    def _extract_best_image_url(self, image_data: dict) -> Optional[str]:
        """
        Extract the best (largest) available image URL from Last.fm response.
        
        Args:
            image_data: Dict containing 'image' array with size info
            
        Returns:
            Image URL or None
        """
        if 'image' not in image_data:
            return None
        
        images = image_data.get('image', [])
        if not images:
            return None
        
        # Preference order: mega > extralarge > large > medium
        size_preferences = ['mega', 'extralarge', 'large', 'medium']
        
        for size_pref in size_preferences:
            for img in images:
                if img.get('size') == size_pref and img.get('#text'):
                    logger.debug(f"Selected {size_pref} size image")
                    return img['#text']
        
        # Fallback: return any image with URL
        for img in images:
            if img.get('#text'):
                logger.debug(f"Using image with size: {img.get('size', 'unknown')}")
                return img['#text']
        
        return None
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test Last.fm API connectivity.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.api_key:
            return (False, "No API key provided")
        
        try:
            # Try a simple artist.getsimilar call
            params = {
                'method': 'artist.getsimilar',
                'artist': 'Metallica',
                'api_key': self.api_key,
                'format': 'json',
                'limit': 1
            }
            
            response = requests.get(self.LASTFM_API_URL, params=params, timeout=5, headers=DEFAULT_HTTP_HEADERS)
            response.raise_for_status()
            data = response.json()
            
            if 'similarartists' in data:
                logger.info("Last.fm API connection successful")
                return (True, "Last.fm API key appears valid")
            else:
                logger.warning("Unexpected response from Last.fm API")
                return (False, "Unexpected response from Last.fm")
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error testing Last.fm connection: {e}")
            return (False, f"HTTP error: {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error testing Last.fm connection: {e}")
            return (False, f"Network error: {e}")
        except Exception as e:
            logger.error(f"Error testing Last.fm connection: {e}")
            return (False, f"Connection error: {e}")
