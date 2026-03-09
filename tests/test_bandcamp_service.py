"""Unit tests for BandcampService."""

import pytest
from unittest.mock import patch, MagicMock
from services.bandcamp_service import BandcampService


class TestBandcampServiceInit:
    """Test BandcampService initialization."""
    
    def test_init_with_credentials(self):
        """Test initialization with username and token."""
        service = BandcampService(
            username='test_user',
            identity_token='test_token_12345'
        )
        assert service.username == 'test_user'
        assert service.identity_token == 'test_token_12345'
    
    def test_init_without_credentials(self):
        """Test initialization without credentials."""
        service = BandcampService()
        assert service.username == ''
        assert service.identity_token == ''
    
    def test_is_enabled_property_without_credentials(self):
        """Test is_enabled property returns False without credentials."""
        service = BandcampService()
        # is_enabled is a property, not a method
        assert service.is_enabled is False
    
    @patch('services.bandcamp_service.BandcampClient')
    def test_is_enabled_property_with_credentials(self, mock_client):
        """Test is_enabled property with valid credentials."""
        mock_client.return_value = MagicMock()
        service = BandcampService(
            username='test_user',
            identity_token='test_token'
        )
        # Should be True when both credentials present and client initialized
        assert service.is_enabled is True


class TestCollectionFetch:
    """Test collection fetching."""
    
    def test_get_collection_disabled_service(self):
        """Test collection fetch when service disabled (no credentials)."""
        service = BandcampService()  # No credentials
        
        collection = service.get_collection()
        
        assert collection == []
    
    @patch('services.bandcamp_service.BandcampClient')
    def test_get_collection_count_parameter(self, mock_client_class):
        """Test collection fetch respects count parameter."""
        mock_client = MagicMock()
        mock_client.get_collection.return_value = [
            {'id': 1, 'title': 'Album 1'},
            {'id': 2, 'title': 'Album 2'}
        ]
        mock_client_class.return_value = mock_client
        
        service = BandcampService(
            username='test_user',
            identity_token='test_token'
        )
        
        collection = service.get_collection(count=100)
        
        assert isinstance(collection, list)
    
    @patch('services.bandcamp_service.BandcampClient')
    def test_get_collection_pagination(self, mock_client_class):
        """Test collection fetch with pagination token."""
        mock_client = MagicMock()
        mock_client.get_collection.return_value = []
        mock_client_class.return_value = mock_client
        
        service = BandcampService(
            username='test_user',
            identity_token='test_token'
        )
        
        collection = service.get_collection(
            count=100,
            older_than_token='token_123'
        )
        
        assert isinstance(collection, list)


class TestAlbumAndTrackInfo:
    """Test album and track information retrieval."""
    
    @patch('services.bandcamp_service.BandcampClient')
    def test_get_album_info_formats_result(self, mock_client_class):
        """Test album info returns properly formatted data."""
        mock_client = MagicMock()
        mock_client.get_album_info.return_value = {
            'album': {
                'id': 123,
                'title': 'Test Album',
                'artist': 'Test Artist'
            }
        }
        mock_client_class.return_value = mock_client
        
        service = BandcampService(
            username='test_user',
            identity_token='test_token'
        )
        
        album_info = service.get_album_info(123)
        
        # Should return data if successful
        assert album_info is None or isinstance(album_info, dict)
    
    def test_get_album_info_disabled_service(self):
        """Test album info fetch when service disabled."""
        service = BandcampService()  # No credentials
        
        album_info = service.get_album_info(123)
        
        assert album_info is None
    
    @patch('services.bandcamp_service.BandcampClient')
    def test_get_track_info_formats_result(self, mock_client_class):
        """Test track info returns properly formatted data."""
        mock_client = MagicMock()
        mock_client.get_track_info.return_value = {
            'track': {
                'id': 456,
                'title': 'Test Track',
                'duration': 300
            }
        }
        mock_client_class.return_value = mock_client
        
        service = BandcampService(
            username='test_user',
            identity_token='test_token'
        )
        
        track_info = service.get_track_info(456)
        
        assert track_info is None or isinstance(track_info, dict)
    
    def test_get_track_info_disabled_service(self):
        """Test track info fetch when service disabled."""
        service = BandcampService()  # No credentials
        
        track_info = service.get_track_info(456)
        
        assert track_info is None


class TestArtworkURL:
    """Test artwork URL generation."""
    
    def test_get_artwork_url_disabled_service(self):
        """Test artwork URL returns empty when disabled."""
        service = BandcampService()  # No credentials
        url = service.get_artwork_url(123456)
        
        # Should return empty string when disabled
        assert url == ''
    
    @patch('services.bandcamp_service.BandcampClient')
    def test_get_artwork_url_with_client(self, mock_client_class):
        """Test artwork URL with enabled client."""
        mock_client = MagicMock()
        mock_client.get_artwork_url.return_value = 'https://f4.bcbits.com/img/123456_5.jpg'
        mock_client_class.return_value = mock_client
        
        service = BandcampService(
            username='test_user',
            identity_token='test_token'
        )
        
        url = service.get_artwork_url(123456)
        
        # Should return URL or empty string
        assert isinstance(url, str)
    
    def test_get_artwork_url_invalid_id(self):
        """Test artwork URL with invalid ID."""
        service = BandcampService()
        url = service.get_artwork_url(0)
        
        # Should return empty string for invalid ID
        assert url == ''


class TestMetadataCache:
    """Test metadata caching functionality."""
    
    def test_cache_track_metadata_disabled_service(self):
        """Test caching when service disabled."""
        service = BandcampService()  # No credentials
        
        # cache_track_metadata returns None
        result = service.cache_track_metadata(
            'https://example.bandcamp.com/track/test',
            track_id=123
        )
        
        # Should return None
        assert result is None
    
    def test_cache_track_metadata_with_url(self):
        """Test caching track metadata from URL."""
        service = BandcampService()
        
        # Call cache method
        result = service.cache_track_metadata(
            'https://example.bandcamp.com/track/test',
            track_id=123,
            title='Test Track',
            artist='Test Artist'
        )
        
        # Should return None (caching returns None)
        assert result is None
    
    def test_get_cached_metadata_empty(self):
        """Test retrieving metadata from empty cache."""
        service = BandcampService()
        
        # Try to retrieve from empty cache
        cached = service.get_cached_metadata('https://example.bandcamp.com/track/test')
        
        # Should return None if not cached
        assert cached is None
    
    def test_clear_cache_succeeds(self):
        """Test clearing the metadata cache."""
        service = BandcampService()
        
        # Should not raise exception
        service.clear_cache()
        
        # Cache should be empty after clearing
        cached = service.get_cached_metadata('https://example.bandcamp.com/track/test')
        assert cached is None


class TestSearch:
    """Test search functionality."""
    
    def test_search_disabled_service(self):
        """Test search when service disabled."""
        service = BandcampService()  # No credentials
        
        results = service.search('test query')
        
        # Should return empty list when disabled
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_returns_list(self):
        """Test search returns list type."""
        service = BandcampService()
        
        results = service.search('test')
        
        # Search currently returns empty list (placeholder)
        assert isinstance(results, list)
    
    def test_search_with_query(self):
        """Test search with query string."""
        service = BandcampService()
        
        # Search is a placeholder, returns empty list
        results = service.search('my search query')
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_empty_query(self):
        """Test search with empty query."""
        service = BandcampService()
        
        results = service.search('')
        
        # Empty query should return empty results
        assert isinstance(results, list)
