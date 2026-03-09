"""
BandcampService - Encapsulates Bandcamp API integration.

Handles:
- Authentication with Bandcamp
- Collection browsing and album/track lookups
- Track streaming URL fetching
- Metadata caching for queue display
- Artwork URL generation
"""

import logging
from typing import Dict, List, Optional
from bandcamp_client import BandcampClient

logger = logging.getLogger(__name__)


class BandcampService:
    """
    Service for Bandcamp integration.
    
    Wraps BandcampClient with caching and metadata management.
    """
    
    def __init__(self, username: str = '', identity_token: str = ''):
        """
        Initialize Bandcamp service.
        
        Args:
            username: Bandcamp username
            identity_token: Identity token from cookies
        """
        self.username = username
        self.identity_token = identity_token
        self.client = None
        self.metadata_cache = {}  # Cache for track metadata
        self._enabled = bool(username and identity_token)
        
        if self._enabled:
            try:
                self.client = BandcampClient(username, identity_token)
                logger.info(f"BandcampService initialized for user: {username}")
            except Exception as e:
                logger.error(f"Failed to initialize BandcampClient: {e}")
                self.client = None
                self._enabled = False
    
    @property
    def is_enabled(self) -> bool:
        """Check if Bandcamp service is enabled and ready."""
        return self._enabled and self.client is not None
    
    def get_collection(self, count: int = 5000, older_than_token: Optional[str] = None) -> List[Dict]:
        """
        Get user's Bandcamp collection.
        
        Args:
            count: Number of items to fetch
            older_than_token: Pagination token
            
        Returns:
            List of album dictionaries
        """
        if not self.is_enabled:
            logger.warning("Bandcamp service not enabled")
            return []
        
        try:
            collection = self.client.get_collection(count=count, older_than_token=older_than_token)
            
            # Log diagnostics about artwork availability
            items_without_art = [a for a in collection if not a.get('art_id')]
            if items_without_art:
                logger.warning(
                    f"Collection: {len(items_without_art)} of {len(collection)} items missing artwork. "
                    f"Examples: {[a.get('album_title', 'Unknown')[:30] for a in items_without_art[:3]]}"
                )
            
            return collection
        except Exception as e:
            logger.error(f"Error getting Bandcamp collection: {e}")
            return []
    
    def get_album_info(self, album_id: int) -> Optional[Dict]:
        """
        Get detailed information about an album including tracks.
        
        Args:
            album_id: Bandcamp album ID
            
        Returns:
            Album info dict with tracks, or None on error
        """
        if not self.is_enabled:
            logger.warning("Bandcamp service not enabled")
            return None
        
        try:
            album_info = self.client.get_album_info(album_id)
            
            # Log diagnostic info about tracks without streaming URLs
            if album_info:
                streamable_tracks = len(album_info.get('tracks', []))
                # Query raw API to count total tracks vs streamable
                from bandcamp_client import BandcampClient
                # The BandcampClient filters tracks, so we note this in logs
                if streamable_tracks == 0:
                    logger.warning(
                        f"Album {album_id} ({album_info.get('title', 'Unknown')}): "
                        f"No tracks with streaming URLs found - likely unreleased, preview, or DRM content"
                    )
            
            return album_info
        except Exception as e:
            logger.error(f"Error getting album info for {album_id}: {e}")
            return None
    
    def get_track_info(self, track_id: int) -> Optional[Dict]:
        """
        Get information about a specific track.
        
        Args:
            track_id: Bandcamp track ID
            
        Returns:
            Track info dict with streaming URL, or None on error
        """
        if not self.is_enabled:
            logger.warning("Bandcamp service not enabled")
            return None
        
        try:
            return self.client.get_track_info(track_id)
        except Exception as e:
            logger.error(f"Error getting track info for {track_id}: {e}")
            return None
    
    def get_artwork_url(self, art_id: int, size: int = 5) -> str:
        """
        Generate artwork URL from art ID.
        
        Args:
            art_id: Bandcamp artwork ID
            size: Size code (2=350x350, 5=700x700, 10=1200x1200)
            
        Returns:
            Artwork URL string
        """
        if not art_id:
            return ''
        
        if not self.is_enabled:
            logger.warning("Bandcamp service not enabled")
            return ''
        
        try:
            return self.client.get_artwork_url(art_id, size)
        except Exception as e:
            logger.error(f"Error generating artwork URL for {art_id}: {e}")
            return ''
    
    def cache_track_metadata(self, streaming_url: str, track_id: Optional[int] = None,
                            title: str = '', artist: str = '', album: str = '',
                            artwork_url: str = '') -> None:
        """
        Cache metadata for a track.
        
        Used when adding tracks to ensure Queue display has proper metadata.
        
        Args:
            streaming_url: Bandcamp streaming URL
            track_id: Optional Bandcamp track ID
            title: Track title
            artist: Artist name
            album: Album name
            artwork_url: Artwork URL
        """
        metadata = {
            'artist': artist,
            'title': title,
            'album': album,
            'artwork_url': artwork_url
        }
        
        # Cache by streaming URL (most reliable lookup during playback)
        self.metadata_cache[streaming_url] = metadata
        
        # Also cache by track_id if available
        if track_id:
            cache_key = f"track_{track_id}"
            self.metadata_cache[cache_key] = metadata
            logger.debug(f"Cached track metadata: {cache_key} + {streaming_url}")
        else:
            logger.debug(f"Cached track metadata: {streaming_url}")
    
    def get_cached_metadata(self, key: str) -> Optional[Dict]:
        """
        Get cached metadata for a track.
        
        Args:
            key: Streaming URL or track_id cache key
            
        Returns:
            Metadata dict or None if not cached
        """
        return self.metadata_cache.get(key)
    
    def clear_cache(self) -> None:
        """Clear the metadata cache."""
        self.metadata_cache.clear()
        logger.info("BandcampService metadata cache cleared")
    
    def search(self, query: str, search_type: str = 'albums') -> List[Dict]:
        """
        Search Bandcamp (placeholder - not yet implemented).
        
        Args:
            query: Search query
            search_type: Type of search ('albums', 'artists', 'tracks')
            
        Returns:
            List of search results (empty for now)
        """
        if not self.is_enabled:
            logger.warning("Bandcamp service not enabled")
            return []
        
        logger.debug(f"Bandcamp search not yet implemented: {query}")
        return []
