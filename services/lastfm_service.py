"""
LastfmService - Encapsulates Last.fm API integration.

Handles:
- Album artwork fetching via album.getinfo
- Track artwork fetching via track.getinfo (for streams)
- Scrobbling (sending plays to Last.fm)
- Now playing updates (current track notifications)
- OAuth token request and session key exchange
- User charts (top artists, albums, tracks)
- Image size selection (mega, extralarge, large, medium)
- Caching and error handling
"""

import logging
import requests
import hashlib
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Default HTTP headers for outbound requests
DEFAULT_HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


class LastfmService:
    """
    Service for Last.fm API integration.
    
    Provides:
    - Album artwork fetching with configurable sizes
    - Track artwork fetching for streams
    - Scrobbling and now playing updates
    - Connection testing
    - Image URL extraction with size preference
    """
    
    LASTFM_API_URL = "https://ws.audioscrobbler.com/2.0/"
    
    def __init__(self, api_key: str = '', shared_secret: str = '', session_key: str = '', auth_url: str = ''):
        """
        Initialize LastfmService.
        
        Args:
            api_key: Last.fm API key for authentication
            shared_secret: Shared secret for API signing (needed for scrobbling)
            session_key: User's Last.fm session key (needed for authenticated endpoints)
            auth_url: Last.fm authorization base URL (for OAuth flow)
        """
        self.api_key = api_key
        self.shared_secret = shared_secret
        self.session_key = session_key
        self.auth_url = auth_url or 'https://www.last.fm/api/auth/'
        self.auth_token = None  # Temporary token during OAuth flow
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
    
    def _sign_request(self, params: dict) -> str:
        """
        Create Last.fm API signature (MD5 of concatenated sorted params + shared secret).
        
        Args:
            params: Request parameters to sign
            
        Returns:
            MD5 signature hex string
        """
        # Exclude 'format', 'callback', and 'api_sig' from signature
        sign_items = [(k, v) for k, v in params.items() if k not in ['format', 'callback', 'api_sig']]
        sign_items.sort(key=lambda x: x[0])
        concat = ''.join([f"{k}{v}" for k, v in sign_items]) + self.shared_secret
        return hashlib.md5(concat.encode('utf-8')).hexdigest()
    
    def _api_post(self, method: str, extra_params: dict) -> dict:
        """
        Make authenticated POST request to Last.fm API.
        
        Args:
            method: Last.fm API method name (e.g., 'track.updateNowPlaying')
            extra_params: Additional parameters for the request
            
        Returns:
            JSON response from Last.fm
            
        Raises:
            RuntimeError: If API key/secret not set or if Last.fm returns error
        """
        if not self.api_key or not self.shared_secret:
            raise RuntimeError('Last.fm API key/secret not configured')
        
        params = {'method': method, 'api_key': self.api_key}
        params.update(extra_params)
        params['api_sig'] = self._sign_request(params)
        params['format'] = 'json'
        
        try:
            response = requests.post(self.LASTFM_API_URL, data=params, timeout=8, headers=DEFAULT_HTTP_HEADERS)
            response.raise_for_status()
            data = response.json()
            
            # Check for Last.fm API errors in response
            if 'error' in data:
                error_code = data.get('error', 0)
                error_msg = data.get('message', 'Unknown error')
                raise RuntimeError(f'Last.fm API error {error_code}: {error_msg}')
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during Last.fm API call: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during Last.fm API call: {e}")
            raise
    
    def update_now_playing(self, artist: str, track: str, album: str = '', duration: int = None) -> bool:
        """
        Send now playing update to Last.fm.
        
        Args:
            artist: Artist name
            track: Track title
            album: Album name (optional)
            duration: Track duration in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.session_key:
            logger.debug("Session key not set, skipping now playing update")
            return False
        
        params = {
            'artist': artist or '',
            'track': track or '',
            'sk': self.session_key
        }
        
        if album:
            params['album'] = album
        
        if isinstance(duration, (int, float)) and duration > 0:
            params['duration'] = int(duration)
        
        try:
            self._api_post('track.updateNowPlaying', params)
            logger.info(f"Now playing update sent: {artist} - {track}")
            return True
        except Exception as e:
            logger.error(f"Failed to update now playing for {artist} - {track}: {e}")
            return False
    
    def scrobble(self, artist: str, track: str, album: str, timestamp_unix: int, duration: int = None) -> bool:
        """
        Scrobble (submit) a track to Last.fm.
        
        Args:
            artist: Artist name
            track: Track title
            album: Album name
            timestamp_unix: Unix timestamp of when the track started playing
            duration: Track duration in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.session_key:
            logger.debug("Session key not set, skipping scrobble")
            return False
        
        # Use array-style parameters as recommended by Last.fm for scrobble batches
        params = {
            'artist[0]': artist or '',
            'track[0]': track or '',
            'timestamp[0]': int(timestamp_unix),
            'sk': self.session_key
        }
        
        if album:
            params['album[0]'] = album
        
        if isinstance(duration, (int, float)) and duration > 0:
            params['duration[0]'] = int(duration)
        
        try:
            self._api_post('track.scrobble', params)
            logger.info(f"Track scrobbled: {artist} - {track}")
            return True
        except Exception as e:
            logger.error(f"Failed to scrobble {artist} - {track}: {e}")
            return False
    
    def request_token(self) -> str:
        """
        Request OAuth token from Last.fm (first step of OAuth flow).
        
        Returns:
            OAuth token string
            
        Raises:
            RuntimeError: If API key not set or if Last.fm returns error
        """
        try:
            data = self._api_post('auth.getToken', {})
            token = data.get('token')
            if not token:
                raise RuntimeError('Failed to obtain Last.fm token')
            self.auth_token = token
            logger.info("OAuth token requested successfully")
            return token
        except Exception as e:
            logger.error(f"Failed to request Last.fm OAuth token: {e}")
            raise
    
    def authorize_url(self) -> str:
        """
        Build Last.fm authorization URL for user to grant permission.
        
        Returns:
            Full authorization URL (user should be directed to this URL)
            
        Raises:
            RuntimeError: If token or API key not set
        """
        if not self.auth_token:
            raise RuntimeError("No auth token available. Request a token first.")
        if not self.api_key:
            raise RuntimeError("API key not configured")
        
        url = f"{self.auth_url}?api_key={self.api_key}&token={self.auth_token}"
        logger.info("Authorization URL generated")
        return url
    
    def get_session(self, token: str) -> str:
        """
        Exchange OAuth token for session key (final step of OAuth flow).
        
        Args:
            token: OAuth token from request_token()
            
        Returns:
            Session key for authenticated requests
            
        Raises:
            RuntimeError: If token exchange fails
        """
        try:
            data = self._api_post('auth.getSession', {'token': token})
            sess = data.get('session', {})
            sk = sess.get('key')
            if not sk:
                raise RuntimeError('Failed to obtain Last.fm session key')
            self.session_key = sk
            self.auth_token = None  # Clear temp token after successful exchange
            logger.info("Session key obtained successfully")
            return sk
        except Exception as e:
            logger.error(f"Failed to get Last.fm session: {e}")
            raise
    
    def get_user_charts(self, chart_type: str, period: str = 'overall', limit: int = 50) -> list:
        """
        Fetch user's top charts from Last.fm (artists, albums, or tracks).
        
        Args:
            chart_type: 'artists', 'albums', or 'tracks'
            period: '7day', '1month', '3month', '6month', '12month', 'overall'
            limit: Number of items to return (max 50)
            
        Returns:
            List of chart items with name, playcount, and metadata
            
        Raises:
            RuntimeError: If session key not set or if API call fails
        """
        if not self.session_key:
            raise RuntimeError('Last.fm session key not set')
        
        # Map chart_type to Last.fm method
        method_map = {
            'artists': 'user.getTopArtists',
            'albums': 'user.getTopAlbums',
            'tracks': 'user.getTopTracks'
        }
        method = method_map.get(chart_type)
        if not method:
            raise ValueError(f"Invalid chart_type: {chart_type}. Must be 'artists', 'albums', or 'tracks'")
        
        # Validate period
        valid_periods = ['7day', '1month', '3month', '6month', '12month', 'overall']
        if period not in valid_periods:
            logger.warning(f"Invalid period '{period}', using 'overall'")
            period = 'overall'
        
        # Build parameters
        params = {
            'sk': self.session_key,
            'period': period,
            'limit': str(limit)
        }
        
        try:
            logger.info(f"Fetching {chart_type} charts for period '{period}'")
            response = self._api_post(method, params)
            
            # Parse response based on chart type
            if chart_type == 'artists':
                artists_data = response.get('topartists', {}).get('artist', [])
                return [{
                    'name': item.get('name', 'Unknown'),
                    'playcount': item.get('playcount', '0'),
                    'url': item.get('url', '')
                } for item in artists_data]
            
            elif chart_type == 'albums':
                albums_data = response.get('topalbums', {}).get('album', [])
                return [{
                    'name': item.get('name', 'Unknown Album'),
                    'artist': item.get('artist', {}).get('name', 'Unknown Artist') if isinstance(item.get('artist'), dict) else item.get('artist', 'Unknown Artist'),
                    'playcount': item.get('playcount', '0'),
                    'url': item.get('url', '')
                } for item in albums_data]
            
            elif chart_type == 'tracks':
                tracks_data = response.get('toptracks', {}).get('track', [])
                return [{
                    'name': item.get('name', 'Unknown Track'),
                    'artist': item.get('artist', {}).get('name', 'Unknown Artist') if isinstance(item.get('artist'), dict) else item.get('artist', 'Unknown Artist'),
                    'playcount': item.get('playcount', '0'),
                    'url': item.get('url', '')
                } for item in tracks_data]
            
            return []
        except Exception as e:
            logger.error(f"Failed to fetch {chart_type} charts: {e}")
            raise
