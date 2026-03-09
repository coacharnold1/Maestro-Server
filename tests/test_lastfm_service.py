"""Unit tests for LastfmService."""

import pytest
from unittest.mock import patch, MagicMock
from services.lastfm_service import LastfmService


class TestLastfmServiceInit:
    """Test LastfmService initialization."""
    
    def test_init_with_all_parameters(self):
        """Test initialization with all parameters."""
        service = LastfmService(
            api_key='test_key',
            shared_secret='test_secret',
            session_key='test_session',
            auth_url='https://test.example.com'
        )
        assert service.api_key == 'test_key'
        assert service.shared_secret == 'test_secret'
        assert service.session_key == 'test_session'
        assert service.auth_url == 'https://test.example.com'
        assert service.auth_token is None
    
    def test_init_with_minimal_parameters(self):
        """Test initialization with minimal parameters."""
        service = LastfmService()
        assert service.api_key == ''
        assert service.shared_secret == ''
        assert service.session_key == ''
        assert service.auth_url == 'https://www.last.fm/api/auth/'


class TestAlbumArtwork:
    """Test album artwork fetching."""
    
    @patch('services.lastfm_service.requests.get')
    def test_fetch_album_artwork_success(self, mock_get, mock_lastfm_api):
        """Test successful album artwork fetch."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_lastfm_api('album.getinfo', {})
        mock_get.return_value = mock_response
        
        # Create service
        service = LastfmService(api_key='test_key', shared_secret='test_secret')
        
        # Fetch artwork
        url = service.fetch_album_artwork('Test Artist', 'Test Album')
        
        # Verify
        assert url == 'https://example.com/image_mega.jpg'
        mock_get.assert_called_once()
    
    @patch('services.lastfm_service.requests.get')
    def test_fetch_album_artwork_missing_parameters(self, mock_get):
        """Test fetch with missing parameters."""
        service = LastfmService(api_key='test_key', shared_secret='test_secret')
        
        # Should return None for missing artist
        url = service.fetch_album_artwork('', 'Album')
        assert url is None
        
        # Should return None for missing album
        url = service.fetch_album_artwork('Artist', '')
        assert url is None
        
        # Should return None for missing API key
        service.api_key = ''
        url = service.fetch_album_artwork('Artist', 'Album')
        assert url is None
    
    @patch('services.lastfm_service.requests.get')
    def test_fetch_track_artwork_success(self, mock_get, mock_lastfm_api):
        """Test successful track artwork fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_lastfm_api('track.getinfo', {})
        mock_get.return_value = mock_response
        
        service = LastfmService(api_key='test_key', shared_secret='test_secret')
        url = service.fetch_track_artwork('Test Artist', 'Test Track')
        
        assert url == 'https://example.com/track_image.jpg'


class TestScrobbling:
    """Test scrobbling functionality."""
    
    @patch('services.lastfm_service.requests.post')
    def test_update_now_playing_success(self, mock_post, mock_lastfm_api):
        """Test sending now playing update."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_lastfm_api('track.updateNowPlaying', {})
        mock_post.return_value = mock_response
        
        service = LastfmService(
            api_key='test_key',
            shared_secret='test_secret',
            session_key='test_sk'
        )
        
        result = service.update_now_playing('Artist', 'Track', 'Album', 180)
        assert result is True
        mock_post.assert_called_once()
    
    @patch('services.lastfm_service.requests.post')
    def test_update_now_playing_no_session_key(self, mock_post):
        """Test now playing without session key."""
        service = LastfmService(api_key='test_key', shared_secret='test_secret')
        
        result = service.update_now_playing('Artist', 'Track')
        assert result is False
        mock_post.assert_not_called()
    
    @patch('services.lastfm_service.requests.post')
    def test_scrobble_success(self, mock_post, mock_lastfm_api):
        """Test successful scrobble."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_lastfm_api('track.scrobble', {})
        mock_post.return_value = mock_response
        
        service = LastfmService(
            api_key='test_key',
            shared_secret='test_secret',
            session_key='test_sk'
        )
        
        result = service.scrobble('Artist', 'Track', 'Album', 1234567890, 180)
        assert result is True
        mock_post.assert_called_once()
    
    @patch('services.lastfm_service.requests.post')
    def test_scrobble_no_session_key(self, mock_post):
        """Test scrobble without session key."""
        service = LastfmService(api_key='test_key', shared_secret='test_secret')
        
        result = service.scrobble('Artist', 'Track', 'Album', 1234567890)
        assert result is False
        mock_post.assert_not_called()


class TestOAuth:
    """Test OAuth flow."""
    
    @patch('services.lastfm_service.requests.post')
    def test_request_token_success(self, mock_post, mock_lastfm_api):
        """Test requesting OAuth token."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_lastfm_api('auth.getToken', {})
        mock_post.return_value = mock_response
        
        service = LastfmService(api_key='test_key', shared_secret='test_secret')
        token = service.request_token()
        
        assert token == 'test_token_12345'
        assert service.auth_token == 'test_token_12345'
    
    @patch('services.lastfm_service.requests.post')
    def test_request_token_no_api_key(self, mock_post):
        """Test token request without API key."""
        service = LastfmService()  # No API key
        
        with pytest.raises(RuntimeError):
            service.request_token()
    
    def test_authorize_url_success(self):
        """Test building authorization URL."""
        service = LastfmService(api_key='test_key')
        service.auth_token = 'test_token'
        
        url = service.authorize_url()
        
        assert 'https://www.last.fm/api/auth/' in url
        assert 'api_key=test_key' in url
        assert 'token=test_token' in url
    
    def test_authorize_url_no_token(self):
        """Test authorize_url without token."""
        service = LastfmService(api_key='test_key')
        
        with pytest.raises(RuntimeError):
            service.authorize_url()
    
    @patch('services.lastfm_service.requests.post')
    def test_get_session_success(self, mock_post, mock_lastfm_api):
        """Test exchanging token for session."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_lastfm_api('auth.getSession', {})
        mock_post.return_value = mock_response
        
        service = LastfmService(api_key='test_key', shared_secret='test_secret')
        session_key = service.get_session('test_token')
        
        assert session_key == 'test_session_key_67890'
        assert service.session_key == 'test_session_key_67890'
        assert service.auth_token is None  # Cleared after exchange


class TestCharts:
    """Test user charts functionality."""
    
    @patch('services.lastfm_service.requests.post')
    def test_get_user_charts_artists(self, mock_post, mock_lastfm_api):
        """Test fetching top artists."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_lastfm_api('user.getTopArtists', {})
        mock_post.return_value = mock_response
        
        service = LastfmService(
            api_key='test_key',
            shared_secret='test_secret',
            session_key='test_sk'
        )
        
        charts = service.get_user_charts('artists', period='overall', limit=50)
        
        assert len(charts) == 2
        assert charts[0]['name'] == 'Artist 1'
        assert charts[0]['playcount'] == '100'
    
    @patch('services.lastfm_service.requests.post')
    def test_get_user_charts_albums(self, mock_post, mock_lastfm_api):
        """Test fetching top albums."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_lastfm_api('user.getTopAlbums', {})
        mock_post.return_value = mock_response
        
        service = LastfmService(
            api_key='test_key',
            shared_secret='test_secret',
            session_key='test_sk'
        )
        
        charts = service.get_user_charts('albums')
        
        assert len(charts) == 1
        assert charts[0]['name'] == 'Album 1'
        assert charts[0]['artist'] == 'Artist 1'
    
    @patch('services.lastfm_service.requests.post')
    def test_get_user_charts_tracks(self, mock_post, mock_lastfm_api):
        """Test fetching top tracks."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_lastfm_api('user.getTopTracks', {})
        mock_post.return_value = mock_response
        
        service = LastfmService(
            api_key='test_key',
            shared_secret='test_secret',
            session_key='test_sk'
        )
        
        charts = service.get_user_charts('tracks')
        
        assert len(charts) == 1
        assert charts[0]['name'] == 'Track 1'
    
    def test_get_user_charts_no_session(self):
        """Test charts request without session key."""
        service = LastfmService(api_key='test_key')
        
        with pytest.raises(RuntimeError):
            service.get_user_charts('artists')
    
    def test_get_user_charts_invalid_type(self):
        """Test charts with invalid chart type."""
        service = LastfmService(
            api_key='test_key',
            shared_secret='test_secret',
            session_key='test_sk'
        )
        
        with pytest.raises(ValueError):
            service.get_user_charts('invalid_type')


class TestConnectionTesting:
    """Test Last.fm connectivity."""
    
    @patch('services.lastfm_service.requests.get')
    def test_connection_success(self, mock_get):
        """Test successful connection test."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'similarartists': {'artist': []}}
        mock_get.return_value = mock_response
        
        service = LastfmService(api_key='test_key', shared_secret='test_secret')
        success, message = service.test_connection()
        
        assert success is True
        mock_get.assert_called_once()
    
    def test_connection_no_api_key(self):
        """Test connection test without API key."""
        service = LastfmService()
        success, message = service.test_connection()
        
        assert success is False
        assert 'No API key' in message
    
    @patch('services.lastfm_service.requests.get')
    def test_connection_network_error(self, mock_get):
        """Test connection with network error."""
        import requests
        mock_get.side_effect = requests.RequestException('Connection failed')
        
        service = LastfmService(api_key='test_key', shared_secret='test_secret')
        success, message = service.test_connection()
        
        assert success is False
        assert 'error' in message.lower()
