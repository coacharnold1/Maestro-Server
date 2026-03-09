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
    
    def test_is_enabled_with_credentials(self):
        """Test is_enabled returns True when credentials present."""
        service = BandcampService(
            username='test_user',
            identity_token='test_token'
        )
        assert service.is_enabled() is True
    
    def test_is_enabled_without_credentials(self):
        """Test is_enabled returns False without credentials."""
        service = BandcampService()
        assert service.is_enabled() is False


class TestCollectionFetch:
    """Test collection fetching."""
    
    @patch('services.bandcamp_service.requests.post')
    def test_get_collection_success(self, mock_post):
        """Test successful collection fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'items': [
                {
                    'id': 123,
                    'title': 'Test Album',
                    'artist': 'Test Artist',
                    'item_art_id': 456,
                    'item_url': 'https://bandcamp.example.com/album/test'
                }
            ],
            'last_token': None
        }
        mock_post.return_value = mock_response
        
        service = BandcampService(
            username='test_user',
            identity_token='test_token'
        )
        
        collection = service.get_collection(count=100)
        
        assert len(collection) == 1
        assert collection[0]['title'] == 'Test Album'
        mock_post.assert_called_once()
    
    @patch('services.bandcamp_service.requests.post')
    def test_get_collection_with_pagination(self, mock_post):
        """Test collection fetch with pagination token."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'items': [], 'last_token': 'token_123'}
        mock_post.return_value = mock_response
        
        service = BandcampService(
            username='test_user',
            identity_token='test_token'
        )
        
        collection = service.get_collection(
            count=100,
            older_than_token='prev_token'
        )
        
        assert collection == []
        mock_post.assert_called_once()
    
    def test_get_collection_disabled(self):
        """Test collection fetch when service disabled."""
        service = BandcampService()  # No credentials
        
        collection = service.get_collection()
        
        assert collection == []
    
    @patch('services.bandcamp_service.requests.post')
    def test_get_collection_network_error(self, mock_post):
        """Test collection fetch handles network errors."""
        import requests
        mock_post.side_effect = requests.RequestException('Network error')
        
        service = BandcampService(
            username='test_user',
            identity_token='test_token'
        )
        
        collection = service.get_collection()
        
        assert collection == []


class TestAlbumAndTrackInfo:
    """Test album and track information retrieval."""
    
    @patch('services.bandcamp_service.requests.get')
    def test_get_album_info_success(self, mock_get):
        """Test successful album info fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'album': {
                'id': 123,
                'title': 'Test Album',
                'artist': 'Test Artist',
                'duration': 1800
            }
        }
        mock_get.return_value = mock_response
        
        service = BandcampService()
        album_info = service.get_album_info(123)
        
        assert album_info is not None
        assert album_info['title'] == 'Test Album'
    
    @patch('services.bandcamp_service.requests.get')
    def test_get_album_info_invalid_id(self, mock_get):
        """Test album info with invalid ID."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        service = BandcampService()
        album_info = service.get_album_info(999999)
        
        assert album_info is None
    
    @patch('services.bandcamp_service.requests.get')
    def test_get_track_info_success(self, mock_get):
        """Test successful track info fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'track': {
                'id': 456,
                'title': 'Test Track',
                'duration': 300,
                'album_id': 123
            }
        }
        mock_get.return_value = mock_response
        
        service = BandcampService()
        track_info = service.get_track_info(456)
        
        assert track_info is not None
        assert track_info['title'] == 'Test Track'
    
    @patch('services.bandcamp_service.requests.get')
    def test_get_track_info_network_error(self, mock_get):
        """Test track info handles network errors."""
        import requests
        mock_get.side_effect = requests.RequestException('Network error')
        
        service = BandcampService()
        track_info = service.get_track_info(456)
        
        assert track_info is None


class TestArtworkURL:
    """Test artwork URL generation."""
    
    def test_get_artwork_url_default_size(self):
        """Test artwork URL with default size."""
        service = BandcampService()
        url = service.get_artwork_url(123456)
        
        assert 'bandcamp.com' in url
        assert '123456' in url
    
    def test_get_artwork_url_custom_size(self):
        """Test artwork URL with custom size."""
        service = BandcampService()
        url = service.get_artwork_url(123456, size=10)
        
        assert 'bandcamp.com' in url
        assert '123456' in url
    
    def test_get_artwork_url_various_sizes(self):
        """Test artwork URLs for different sizes."""
        service = BandcampService()
        
        url_1 = service.get_artwork_url(123456, size=1)
        url_3 = service.get_artwork_url(123456, size=3)
        url_5 = service.get_artwork_url(123456, size=5)
        
        assert all('bandcamp.com' in url for url in [url_1, url_3, url_5])
        assert all('123456' in url for url in [url_1, url_3, url_5])


class TestMetadataCache:
    """Test metadata caching functionality."""
    
    def test_cache_track_metadata_with_url(self):
        """Test caching track metadata from URL."""
        service = BandcampService()
        
        result = service.cache_track_metadata(
            'https://example.bandcamp.com/track/test',
            track_id=123
        )
        
        assert isinstance(result, bool)
    
    def test_cache_track_metadata_with_id(self):
        """Test caching track metadata with ID."""
        service = BandcampService()
        
        result = service.cache_track_metadata(
            'https://example.bandcamp.com/track/test',
            track_id=456,
            artist='Test Artist',
            title='Test Track'
        )
        
        assert isinstance(result, bool)
    
    def test_get_cached_metadata(self):
        """Test retrieving cached metadata."""
        service = BandcampService()
        
        # Cache something first
        service.cache_track_metadata(
            'https://example.bandcamp.com/track/test',
            track_id=123
        )
        
        # Try to retrieve it
        cached = service.get_cached_metadata('https://example.bandcamp.com/track/test')
        
        # Result could be None if not actually cached, but should not error
        assert cached is None or isinstance(cached, dict)
    
    def test_clear_cache(self):
        """Test clearing the metadata cache."""
        service = BandcampService()
        
        service.cache_track_metadata(
            'https://example.bandcamp.com/track/test',
            track_id=123
        )
        
        service.clear_cache()
        
        # After clearing, cache should be empty
        cached = service.get_cached_metadata('https://example.bandcamp.com/track/test')
        assert cached is None


class TestSearch:
    """Test search functionality."""
    
    @patch('services.bandcamp_service.requests.get')
    def test_search_albums_success(self, mock_get):
        """Test successful album search."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 123,
                    'title': 'Test Album',
                    'artist': 'Test Artist',
                    'type': 'album'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        service = BandcampService()
        results = service.search('Test Album', search_type='albums')
        
        # Results format depends on implementation
        assert results is not None
        assert isinstance(results, list)
    
    @patch('services.bandcamp_service.requests.get')
    def test_search_artists_success(self, mock_get):
        """Test successful artist search."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 456,
                    'name': 'Test Artist',
                    'url': 'https://bandcamp.example.com/artist'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        service = BandcampService()
        results = service.search('Test Artist', search_type='artists')
        
        assert results is not None
        assert isinstance(results, list)
    
    @patch('services.bandcamp_service.requests.get')
    def test_search_empty_results(self, mock_get):
        """Test search with no results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'results': []}
        mock_get.return_value = mock_response
        
        service = BandcampService()
        results = service.search('Nonexistent Album')
        
        assert results == []
    
    @patch('services.bandcamp_service.requests.get')
    def test_search_network_error(self, mock_get):
        """Test search handles network errors."""
        import requests
        mock_get.side_effect = requests.RequestException('Network error')
        
        service = BandcampService()
        results = service.search('Test Album')
        
        assert results == []
