"""Unit tests for MPDService."""

import pytest
from unittest.mock import patch, MagicMock, call
from services.mpd_service import MPDService


class TestMPDServiceInit:
    """Test MPDService initialization."""
    
    def test_init_with_host_port(self):
        """Test initialization with host and port."""
        service = MPDService(host='localhost', port=6600)
        assert service.host == 'localhost'
        assert service.port == 6600
        assert service.client is None
    
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        service = MPDService()
        assert service.host == 'localhost'
        assert service.port == 6600
    
    def test_init_with_timeout(self):
        """Test initialization with custom timeout."""
        service = MPDService(timeout=10, idletimeout=5)
        assert service.timeout == 10
        assert service.idletimeout == 5
    
    @patch('services.mpd_service.MPDClient')
    def test_get_client_new_connection(self, mock_mpd_client):
        """Test getting a new MPD client connection."""
        mock_instance = MagicMock()
        mock_mpd_client.return_value = mock_instance
        
        service = MPDService(host='localhost', port=6600)
        client = service.get_client()
        
        assert client is not None
        mock_instance.connect.assert_called_once_with('localhost', 6600)
    
    @patch('services.mpd_service.MPDClient')
    def test_get_client_uses_existing_connection(self, mock_mpd_client):
        """Test get_client reuses existing connection."""
        mock_instance = MagicMock()
        mock_mpd_client.return_value = mock_instance
        
        service = MPDService()
        service.client = mock_instance
        
        client = service.get_client()
        
        assert client is mock_instance
        # Should ping to verify connection
        mock_instance.ping.assert_called_once()


class TestPlaybackControl:
    """Test playback control functionality."""
    
    @patch('services.mpd_service.MPDClient')
    def test_play_with_position(self, mock_mpd):
        """Test playing a song at specific position."""
        mock_instance = MagicMock()
        mock_mpd.return_value = mock_instance
        service = MPDService()
        service.client = mock_instance
        
        result = service.play(0)
        
        assert result is True
        mock_instance.play.assert_called_once_with(0)
    
    @patch('services.mpd_service.MPDClient')
    def test_play_resume(self, mock_mpd):
        """Test resuming playback (no position)."""
        mock_instance = MagicMock()
        mock_mpd.return_value = mock_instance
        service = MPDService()
        service.client = mock_instance
        
        result = service.play()
        
        assert result is True
        mock_instance.play.assert_called_once()
    
    @patch('services.mpd_service.MPDClient')
    def test_pause_success(self, mock_mpd):
        """Test pausing playback."""
        mock_instance = MagicMock()
        mock_mpd.return_value = mock_instance
        service = MPDService()
        service.client = mock_instance
        
        result = service.pause()
        
        assert result is True
        mock_instance.pause.assert_called_once()
    
    @patch('services.mpd_service.MPDClient')
    def test_next_success(self, mock_mpd):
        """Test playing next song."""
        mock_instance = MagicMock()
        mock_mpd.return_value = mock_instance
        service = MPDService()
        service.client = mock_instance
        
        result = service.next()
        
        assert result is True
        mock_instance.next.assert_called_once()
    
    @patch('services.mpd_service.MPDClient')
    def test_previous_success(self, mock_mpd):
        """Test playing previous song."""
        mock_instance = MagicMock()
        mock_mpd.return_value = mock_instance
        service = MPDService()
        service.client = mock_instance
        
        result = service.previous()
        
        assert result is True
        mock_instance.previous.assert_called_once()
    
    @patch('services.mpd_service.MPDClient')
    def test_stop_success(self, mock_mpd):
        """Test stopping playback."""
        mock_instance = MagicMock()
        mock_mpd.return_value = mock_instance
        service = MPDService()
        service.client = mock_instance
        
        result = service.stop()
        
        assert result is True
        mock_instance.stop.assert_called_once()
    
    @patch('services.mpd_service.MPDClient')
    def test_play_without_client(self, mock_mpd):
        """Test play fails gracefully without connection."""
        service = MPDService()
        service.client = None
        
        with patch.object(service, 'get_client', return_value=None):
            result = service.play(0)
            assert result is False


class TestStatusAndInfo:
    """Test status and information queries."""
    
    @patch('services.mpd_service.MPDClient')
    def test_get_status(self, mock_mpd):
        """Test getting playback status."""
        mock_instance = MagicMock()
        mock_instance.status.return_value = {
            'state': 'play',
            'song': '0',
            'time': '10:180',
            'bitrate': '320'
        }
        service = MPDService()
        service.client = mock_instance
        
        status = service.status()
        
        assert status['state'] == 'play'
        assert status['song'] == '0'
        mock_instance.status.assert_called_once()
    
    @patch('services.mpd_service.MPDClient')
    def test_status_empty_on_no_client(self, mock_mpd):
        """Test status returns empty dict without client."""
        service = MPDService()
        
        with patch.object(service, 'get_client', return_value=None):
            status = service.status()
            assert status == {}
    
    @patch('services.mpd_service.MPDClient')
    def test_status_error_handling(self, mock_mpd):
        """Test status handles errors gracefully."""
        mock_instance = MagicMock()
        mock_instance.status.side_effect = Exception('MPD error')
        service = MPDService()
        service.client = mock_instance
        
        status = service.status()
        
        assert status == {}


class TestQueueManagement:
    """Test queue/playlist management."""
    
    @patch('services.mpd_service.MPDClient')
    def test_get_playlist(self, mock_mpd):
        """Test getting playlist queue (filenames only)."""
        mock_instance = MagicMock()
        mock_instance.playlist.return_value = [
            'Music/artist/album/song1.mp3',
            'Music/artist/album/song2.mp3'
        ]
        service = MPDService()
        service.client = mock_instance
        
        playlist = service.playlist()
        
        assert len(playlist) == 2
        assert playlist[0] == 'Music/artist/album/song1.mp3'
    
    @patch('services.mpd_service.MPDClient')
    def test_add_to_queue(self, mock_mpd):
        """Test adding song to queue."""
        mock_instance = MagicMock()
        mock_mpd.return_value = mock_instance
        service = MPDService()
        service.client = mock_instance
        
        result = service.add('Music/artist/album/song.mp3')
        
        assert result is True
        mock_instance.add.assert_called_once_with('Music/artist/album/song.mp3')
    
    @patch('services.mpd_service.MPDClient')
    def test_remove_from_queue(self, mock_mpd):
        """Test removing song from queue."""
        mock_instance = MagicMock()
        mock_mpd.return_value = mock_instance
        service = MPDService()
        service.client = mock_instance
        
        result = service.delete(0)
        
        assert result is True
        mock_instance.delete.assert_called_once_with(0)
    
    @patch('services.mpd_service.MPDClient')
    def test_clear_queue(self, mock_mpd):
        """Test clearing queue."""
        mock_instance = MagicMock()
        mock_mpd.return_value = mock_instance
        service = MPDService()
        service.client = mock_instance
        
        result = service.clear()
        
        assert result is True
        mock_instance.clear.assert_called_once()
    
    @patch('services.mpd_service.MPDClient')
    def test_get_playlist_info(self, mock_mpd):
        """Test getting playlist with full song info."""
        mock_instance = MagicMock()
        mock_instance.playlistinfo.return_value = [
            {
                'artist': 'Artist 1',
                'title': 'Song 1',
                'album': 'Album 1',
                'file': 'Music/artist/song1.mp3',
                'pos': '0'
            },
            {
                'artist': 'Artist 2',
                'title': 'Song 2',
                'album': 'Album 2',
                'file': 'Music/artist/song2.mp3',
                'pos': '1'
            }
        ]
        service = MPDService()
        service.client = mock_instance
        
        playlist = service.playlistinfo()
        
        assert len(playlist) == 2
        assert playlist[0]['title'] == 'Song 1'
        assert playlist[1]['artist'] == 'Artist 2'
    
    @patch('services.mpd_service.MPDClient')
    def test_get_playlist_info_with_range(self, mock_mpd):
        """Test getting playlist info with start/end range."""
        mock_instance = MagicMock()
        mock_instance.playlistinfo.return_value = [
            {'artist': 'Artist 1', 'title': 'Song 1', 'pos': '0'}
        ]
        service = MPDService()
        service.client = mock_instance
        
        playlist = service.playlistinfo(start=0, end=1)
        
        assert len(playlist) == 1
        mock_instance.playlistinfo.assert_called_once_with('0:1')
    
    @patch('services.mpd_service.MPDClient')
    def test_move_in_queue(self, mock_mpd):
        """Test moving song in queue."""
        mock_instance = MagicMock()
        mock_mpd.return_value = mock_instance
        service = MPDService()
        service.client = mock_instance
        
        result = service.move(0, 2)
        
        assert result is True
        mock_instance.move.assert_called_once_with(0, 2)


class TestSearch:
    """Test search functionality."""
    
    @patch('services.mpd_service.MPDClient')
    def test_search_by_artist(self, mock_mpd):
        """Test searching by artist."""
        mock_instance = MagicMock()
        mock_instance.search.return_value = [
            {'artist': 'Test Artist', 'title': 'Song 1', 'album': 'Album 1'},
            {'artist': 'Test Artist', 'title': 'Song 2', 'album': 'Album 2'}
        ]
        service = MPDService()
        service.client = mock_instance
        
        results = service.search('artist', 'Test Artist')
        
        assert len(results) == 2
        assert results[0]['artist'] == 'Test Artist'
        mock_instance.search.assert_called_once_with('artist', 'Test Artist')
    
    @patch('services.mpd_service.MPDClient')
    def test_search_empty_results(self, mock_mpd):
        """Test search with no results."""
        mock_instance = MagicMock()
        mock_instance.search.return_value = []
        service = MPDService()
        service.client = mock_instance
        
        results = service.search('artist', 'Non Existent Artist')
        
        assert len(results) == 0
    
    @patch('services.mpd_service.MPDClient')
    def test_search_error_handling(self, mock_mpd):
        """Test search handles errors gracefully."""
        mock_instance = MagicMock()
        mock_instance.search.side_effect = Exception('MPD error')
        service = MPDService()
        service.client = mock_instance
        
        results = service.search('artist', 'Test')
        
        assert results == []
    
    @patch('services.mpd_service.MPDClient')
    def test_find_songs(self, mock_mpd):
        """Test finding songs with case-sensitive match."""
        mock_instance = MagicMock()
        mock_instance.find.return_value = [
            {'artist': 'Beatles', 'title': 'Help', 'album': 'Help!'}
        ]
        service = MPDService()
        service.client = mock_instance
        
        results = service.find('artist', 'Beatles', 'album', 'Help!')
        
        assert len(results) == 1
        assert results[0]['title'] == 'Help'
        mock_instance.find.assert_called_once_with('artist', 'Beatles', 'album', 'Help!')


class TestBrowsing:
    """Test music library browsing."""
    
    @patch('services.mpd_service.MPDClient')
    def test_list_artists(self, mock_mpd):
        """Test listing all artists."""
        mock_instance = MagicMock()
        mock_instance.list.return_value = ['Artist 1', 'Artist 2', 'Artist 3']
        service = MPDService()
        service.client = mock_instance
        
        artists = service.list('artist')
        
        assert len(artists) == 3
        assert 'Artist 1' in artists
        mock_instance.list.assert_called_once_with('artist')
    
    @patch('services.mpd_service.MPDClient')
    def test_list_albums_by_artist(self, mock_mpd):
        """Test listing albums by a specific artist."""
        mock_instance = MagicMock()
        mock_instance.list.return_value = [
            {'artist': 'Artist 1', 'album': 'Album 1'},
            {'artist': 'Artist 1', 'album': 'Album 2'}
        ]
        service = MPDService()
        service.client = mock_instance
        
        albums = service.list('album', 'artist', 'Artist 1')
        
        assert len(albums) == 2
        mock_instance.list.assert_called_once_with('album', 'artist', 'Artist 1')
    
    @patch('services.mpd_service.MPDClient')
    def test_list_genres(self, mock_mpd):
        """Test listing all genres."""
        mock_instance = MagicMock()
        mock_instance.list.return_value = ['Rock', 'Jazz', 'Classical']
        service = MPDService()
        service.client = mock_instance
        
        genres = service.list('genre')
        
        assert len(genres) == 3
        assert 'Rock' in genres
    
    @patch('services.mpd_service.MPDClient')
    def test_list_all_info(self, mock_mpd):
        """Test listing all songs with full info."""
        mock_instance = MagicMock()
        mock_instance.listallinfo.return_value = [
            {'artist': 'Artist 1', 'title': 'Song 1', 'file': 'Music/artist/song1.mp3'},
            {'artist': 'Artist 2', 'title': 'Song 2', 'file': 'Music/artist/song2.mp3'}
        ]
        service = MPDService()
        service.client = mock_instance
        
        songs = service.listallinfo()
        
        assert len(songs) == 2
        mock_instance.listallinfo.assert_called_once_with('')


class TestVolumeControl:
    """Test volume control."""
    
    @patch('services.mpd_service.MPDClient')
    def test_set_volume(self, mock_mpd):
        """Test setting volume."""
        mock_instance = MagicMock()
        mock_mpd.return_value = mock_instance
        service = MPDService()
        service.client = mock_instance
        
        result = service.setvol(75)
        
        assert result is True
        mock_instance.setvol.assert_called_once_with(75)
    
    @patch('services.mpd_service.MPDClient')
    def test_set_volume_error(self, mock_mpd):
        """Test volume error handling."""
        mock_instance = MagicMock()
        mock_instance.setvol.side_effect = Exception('Volume error')
        service = MPDService()
        service.client = mock_instance
        
        result = service.setvol(75)
        
        assert result is False


class TestSeek:
    """Test seeking functionality."""
    
    @patch('services.mpd_service.MPDClient')
    def test_seek_success(self, mock_mpd):
        """Test seeking to position."""
        mock_instance = MagicMock()
        mock_mpd.return_value = mock_instance
        service = MPDService()
        service.client = mock_instance
        
        result = service.seek(0, 30)
        
        assert result is True
        mock_instance.seek.assert_called_once_with(0, 30)
    
    @patch('services.mpd_service.MPDClient')
    def test_seek_error(self, mock_mpd):
        """Test seek error handling."""
        mock_instance = MagicMock()
        mock_instance.seek.side_effect = Exception('Invalid position')
        service = MPDService()
        service.client = mock_instance
        
        result = service.seek(0, 999)
        
        assert result is False


class TestDatabaseUpdate:
    """Test database update functionality."""
    
    @patch('services.mpd_service.MPDClient')
    def test_update_database(self, mock_mpd):
        """Test updating entire database."""
        mock_instance = MagicMock()
        mock_instance.update.return_value = 123  # Job ID
        service = MPDService()
        service.client = mock_instance
        
        job_id = service.update()
        
        assert job_id == 123
        mock_instance.update.assert_called_once_with()
    
    @patch('services.mpd_service.MPDClient')
    def test_update_specific_path(self, mock_mpd):
        """Test updating specific path in database."""
        mock_instance = MagicMock()
        mock_instance.update.return_value = 456
        service = MPDService()
        service.client = mock_instance
        
        job_id = service.update('Music/artist')
        
        assert job_id == 456
        mock_instance.update.assert_called_once_with('Music/artist')
    
    @patch('services.mpd_service.MPDClient')
    def test_update_error(self, mock_mpd):
        """Test update error handling."""
        mock_instance = MagicMock()
        mock_instance.update.side_effect = Exception('Update error')
        service = MPDService()
        service.client = mock_instance
        
        job_id = service.update()
        
        assert job_id == 0


class TestConnectionManagement:
    """Test connection management."""
    
    @patch('services.mpd_service.MPDClient')
    def test_close_connection(self, mock_mpd):
        """Test closing connection."""
        mock_instance = MagicMock()
        service = MPDService()
        service.client = mock_instance
        
        service.close()
        
        assert service.client is None
        mock_instance.close.assert_called_once()
    
    @patch('services.mpd_service.MPDClient')
    def test_disconnect_alias(self, mock_mpd):
        """Test disconnect is alias for close."""
        mock_instance = MagicMock()
        service = MPDService()
        service.client = mock_instance
        
        service.disconnect()
        
        assert service.client is None
        mock_instance.close.assert_called_once()
    
    @patch('services.mpd_service.MPDClient')
    def test_close_without_client(self, mock_mpd):
        """Test close handles no client gracefully."""
        service = MPDService()
        service.client = None
        
        # Should not raise
        service.close()
        assert service.client is None
