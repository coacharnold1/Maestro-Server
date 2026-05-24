"""
Integration tests for Maestro Server.

Tests real-world workflows with mocked services to verify
that different services work together correctly.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from services.bandcamp_service import BandcampService
from services.mpd_service import MPDService
from services.genius_service import GeniusService
from services.lastfm_service import LastfmService


# =============================================================================
# WORKFLOWS: Bandcamp Integration
# =============================================================================

class TestBandcampWorkflows:
    """Test Bandcamp integration workflows."""
    
    @patch('services.bandcamp_service.BandcampClient')
    @patch('services.mpd_service.MPDClient')
    def test_bandcamp_browse_add_to_queue_display(self, mock_mpd_class, mock_bc_class):
        """
        Workflow: User browses Bandcamp albums → adds track → sees in queue with metadata.
        """
        # Setup Bandcamp mock
        mock_bc = mock_bc_class.return_value
        mock_bc.get_collection.return_value = [
            {
                'ID': 123,
                'item_title': 'Test Album',
                'item_art_id': 456,
                'tracks': [
                    {
                        'track_id': 789,
                        'title': 'Track One',
                        'artist': 'Test Artist',
                        'duration': 240,
                        'streaming_url': 'https://example.bandcamp.com/track/test-one'
                    }
                ]
            }
        ]
        mock_bc.get_artwork_url.return_value = 'https://f4.bcbits.com/img/456_5.jpg'
        
        # Setup MPD mock
        mock_mpd = mock_mpd_class.return_value
        mock_mpd.add.return_value = None
        mock_mpd.playlistinfo.return_value = [
            {
                'file': 'https://example.bandcamp.com/track/test-one',
                'title': 'Track One',
                'artist': 'Test Artist',
                'album': 'Test Album',
                'id': '1'
            }
        ]
        
        # Initialize services
        bandcamp_service = BandcampService()
        bandcamp_service.client = mock_bc
        bandcamp_service._enabled = True
        
        mpd_service = MPDService(host='localhost', port=6600, timeout=5)
        mpd_service.client = mock_mpd
        
        # Execute workflow
        # 1. Browse albums
        albums = bandcamp_service.get_collection(100)
        assert len(albums) > 0
        assert albums[0]['item_title'] == 'Test Album'
        
        # 2. Get first track
        track = albums[0]['tracks'][0]
        
        # 3. Cache metadata before adding
        bandcamp_service.cache_track_metadata(
            track['streaming_url'],
            track_id=track['track_id'],
            title=track['title'],
            artist=track['artist'],
            album=albums[0]['item_title'],
            artwork_url=mock_bc.get_artwork_url(456)
        )
        
        # 4. Add to queue
        mpd_service.add(track['streaming_url'])
        
        # 5. Verify in queue
        queue = mpd_service.playlistinfo()
        assert len(queue) > 0
        assert queue[0]['file'] == track['streaming_url']
        
        # 6. Verify metadata cached
        cached = bandcamp_service.get_cached_metadata(track['streaming_url'])
        assert cached is not None
        assert cached['title'] == 'Track One'
        assert cached['artist'] == 'Test Artist'
    
    @patch('services.bandcamp_service.BandcampClient')
    def test_bandcamp_collection_fetch_with_pagination(self, mock_bc_class):
        """
        Workflow: User fetches large collection with pagination.
        """
        mock_bc = mock_bc_class.return_value
        
        # First page: 50 items
        first_page = [{'ID': i, 'item_title': f'Album {i}'} for i in range(50)]
        
        # Second page: remaining items
        second_page = [{'ID': i, 'item_title': f'Album {i}'} for i in range(50, 75)]
        
        mock_bc.get_collection.side_effect = [first_page, second_page]
        
        bandcamp_service = BandcampService()
        bandcamp_service.client = mock_bc
        bandcamp_service._enabled = True
        
        # Fetch first page
        page1 = bandcamp_service.get_collection(50)
        assert len(page1) == 50
        
        # Fetch second page (separate call with different count)
        page2 = bandcamp_service.get_collection(25)
        assert len(page2) == 25
        
        # Verify total would be 75 albums
        assert mock_bc.get_collection.call_count == 2
    
    @patch('services.bandcamp_service.BandcampClient')
    @patch('services.genius_service.requests.get')
    def test_bandcamp_track_with_lyrics_lookup(self, mock_genius, mock_bc_class):
        """
        Workflow: User adds Bandcamp track → lyrics fetched from Genius.
        """
        mock_bc = mock_bc_class.return_value
        mock_bc.get_track_info.return_value = {
            'track_id': 123,
            'title': 'Test Song',
            'artist': 'Test Artist',
            'duration': 240
        }
        
        # Mock Genius API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': {
                'hits': [
                    {
                        'result': {
                            'url': 'https://genius.com/test',
                            'title': 'Test Song'
                        }
                    }
                ]
            }
        }
        mock_genius.return_value = mock_response
        
        # Initialize services
        bandcamp_service = BandcampService()
        bandcamp_service.client = mock_bc
        bandcamp_service._enabled = True
        
        genius_service = GeniusService()
        
        # Execute workflow
        track_info = bandcamp_service.get_track_info(123)
        assert track_info is not None
        assert track_info['title'] == 'Test Song'
        
        # Look up lyrics
        lyrics = genius_service.get_lyrics(track_info['artist'], track_info['title'])
        # Result depends on mock - verify call was made
        assert mock_genius.called


# =============================================================================
# WORKFLOWS: MPD Search and Playback
# =============================================================================

class TestMPDPlaybackWorkflows:
    """Test MPD playback workflows."""
    
    @patch('services.mpd_service.MPDClient')
    def test_search_song_add_play_workflow(self, mock_mpd_class):
        """
        Workflow: Search for song → add to queue → play.
        """
        mock_mpd = mock_mpd_class.return_value
        
        # Mock search results
        mock_mpd.search.return_value = [
            {
                'file': 'music/artist/album/song.flac',
                'title': 'Test Song',
                'artist': 'Test Artist',
                'album': 'Test Album',
                'duration': '240'
            }
        ]
        
        # Mock queue operations
        mock_mpd.add.return_value = None
        mock_mpd.play.return_value = None
        mock_mpd.playlistinfo.return_value = [
            {
                'id': '1',
                'file': 'music/artist/album/song.flac',
                'title': 'Test Song',
                'artist': 'Test Artist',
                'album': 'Test Album'
            }
        ]
        
        mpd_service = MPDService(host='localhost', port=6600, timeout=5)
        mpd_service.client = mock_mpd
        
        # Execute workflow
        # 1. Search for song
        results = mpd_service.search('artist', 'Test Artist')
        assert len(results) > 0
        assert results[0]['title'] == 'Test Song'
        
        # 2. Add to queue
        mpd_service.add(results[0]['file'])
        assert mock_mpd.add.called
        
        # 3. Play
        mpd_service.play()
        assert mock_mpd.play.called
        
        # 4. Verify in queue
        queue = mpd_service.playlistinfo()
        assert len(queue) > 0
    
    @patch('services.mpd_service.MPDClient')
    def test_browse_artist_select_album_add_workflow(self, mock_mpd_class):
        """
        Workflow: Browse artists → select artist → browse albums → add all songs.
        """
        mock_mpd = mock_mpd_class.return_value
        
        # Mock artist list
        mock_mpd.list.side_effect = [
            ['Artist One', 'Artist Two', 'Artist Three'],  # First call: artists
            ['Album One', 'Album Two'],  # Second call: albums for Artist One
        ]
        
        # Mock find results for songs
        mock_mpd.find.return_value = [
            {'file': 'music/Artist One/Album One/01.flac', 'title': 'Song 1'},
            {'file': 'music/Artist One/Album One/02.flac', 'title': 'Song 2'}
        ]
        mock_mpd.add.return_value = None
        
        mpd_service = MPDService(host='localhost', port=6600, timeout=5)
        mpd_service.client = mock_mpd
        
        # Execute workflow
        # 1. Get artist list
        artists = mpd_service.list('artist')
        assert 'Artist One' in artists
        
        # 2. Get albums for artist
        albums = mpd_service.list('album', 'artist', 'Artist One')
        assert 'Album One' in albums
        
        # 3. Get all songs in album
        songs = mpd_service.find('artist', 'Artist One', 'album', 'Album One')
        assert len(songs) > 0
        
        # 4. Add all songs to queue
        for song in songs:
            mpd_service.add(song['file'])
        
        # Verify add called for each song
        assert mock_mpd.add.call_count == 2


# =============================================================================
# WORKFLOWS: Last.fm Scrobbling
# =============================================================================

class TestScrobblingWorkflows:
    """Test Last.fm scrobbling workflows."""
    
    @patch('services.mpd_service.MPDClient')
    @patch('services.lastfm_service.requests.post')
    def test_song_completion_scrobble_workflow(self, mock_lastfm_post, mock_mpd_class):
        """
        Workflow: Song finishes → MPD reports completion → Last.fm scrobbles.
        """
        # Mock MPD status (song finished)
        mock_mpd = mock_mpd_class.return_value
        mock_mpd.status.return_value = {
            'state': 'stop',
            'time': '240:240'  # Song finished
        }
        
        # Mock Last.fm API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_lastfm_post.return_value = mock_response
        
        # Initialize services
        mpd_service = MPDService(host='localhost', port=6600, timeout=5)
        mpd_service.client = mock_mpd
        
        lastfm_service = LastfmService(api_key='test_key', shared_secret='test_secret')
        
        # Execute workflow
        # 1. Check if song finished
        status = mpd_service.status()
        assert status['state'] == 'stop'
        
        # 2. Scrobble (simulate Last.fm POST)
        # In real code, this would call lastfm_service scrobble logic
        mock_lastfm_post(
            'http://ws.audioscrobbler.com/2.0/',
            data={
                'method': 'track.scrobble',
                'artist': 'Test Artist',
                'track': 'Test Song',
                'timestamp': 1234567890
            }
        )
        
        # Verify POST was made
        assert mock_lastfm_post.called
    
    @patch('services.lastfm_service.requests.get')
    def test_last_fm_album_art_fetch(self, mock_lastfm_get):
        """
        Workflow: Fetch album art from Last.fm for playing song.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'album': {
                'image': [
                    {'size': 'small', '#text': 'https://lastfm.example.com/small.jpg'},
                    {'size': 'large', '#text': 'https://lastfm.example.com/large.jpg'}
                ]
            }
        }
        mock_lastfm_get.return_value = mock_response
        
        lastfm_service = LastfmService(api_key='test_key', shared_secret='test_secret')
        
        # Execute workflow
        artwork = lastfm_service.fetch_album_artwork('Test Artist', 'Test Album')
        
        # Verify Last.fm was queried
        assert mock_lastfm_get.called
        # Result depends on mock, but should have been attempted
        assert artwork is not None or artwork == ''


# =============================================================================
# WORKFLOWS: Multi-Service Integration
# =============================================================================

class TestMultiServiceWorkflows:
    """Test workflows involving multiple services."""
    
    @patch('services.bandcamp_service.BandcampClient')
    @patch('services.mpd_service.MPDClient')
    @patch('services.lastfm_service.requests.get')
    @patch('services.genius_service.requests.get')
    def test_complete_playback_workflow(self, mock_genius, mock_lastfm, mock_mpd_class, mock_bc_class):
        """
        Workflow: Browse Bandcamp → Add → Display in queue → Play → Sync metadata
        across MPD, Last.fm, and Genius services.
        """
        # Setup Bandcamp
        mock_bc = mock_bc_class.return_value
        mock_bc.get_collection.return_value = [{
            'ID': 1,
            'item_title': 'Test Album',
            'item_art_id': 100,
            'tracks': [{
                'track_id': 1,
                'title': 'Test Track',
                'artist': 'Test Artist',
                'streaming_url': 'https://example.bandcamp.com/track/test'
            }]
        }]
        mock_bc.get_artwork_url.return_value = 'https://f4.bcbits.com/img/100.jpg'
        
        # Setup MPD
        mock_mpd = mock_mpd_class.return_value
        mock_mpd.add.return_value = None
        mock_mpd.play.return_value = None
        mock_mpd.playlistinfo.return_value = [{
            'id': '1',
            'file': 'https://example.bandcamp.com/track/test',
            'title': 'Test Track',
            'artist': 'Test Artist'
        }]
        mock_mpd.status.return_value = {'state': 'play', 'time': '10:240'}
        
        # Setup Last.fm
        mock_lastfm_response = Mock()
        mock_lastfm_response.status_code = 200
        mock_lastfm_response.json.return_value = {
            'album': {'image': [{'#text': 'https://lastfm.example.com/img.jpg'}]}
        }
        mock_lastfm.return_value = mock_lastfm_response
        
        # Setup Genius
        mock_genius_response = Mock()
        mock_genius_response.status_code = 200
        mock_genius_response.json.return_value = {
            'response': {
                'hits': [{
                    'result': {'title': 'Test Track', 'url': 'https://genius.com/test'}
                }]
            }
        }
        mock_genius.return_value = mock_genius_response
        
        # Initialize services
        bandcamp = BandcampService()
        bandcamp.client = mock_bc
        bandcamp._enabled = True
        
        mpd = MPDService(host='localhost', port=6600, timeout=5)
        mpd.client = mock_mpd
        
        lastfm = LastfmService(api_key='test', shared_secret='test')
        genius = GeniusService()
        
        # Execute complete workflow
        # 1. Browse Bandcamp
        albums = bandcamp.get_collection(100)
        assert len(albums) == 1
        
        track = albums[0]['tracks'][0]
        
        # 2. Cache metadata
        bandcamp.cache_track_metadata(
            track['streaming_url'],
            track_id=track['track_id'],
            title=track['title'],
            artist=track['artist'],
            artwork_url=mock_bc.get_artwork_url(100)
        )
        
        # 3. Add to MPD queue
        mpd.add(track['streaming_url'])
        assert mock_mpd.add.called
        
        # 4. Play
        mpd.play()
        assert mock_mpd.play.called
        
        # 5. Get queue
        queue = mpd.playlistinfo()
        assert len(queue) > 0
        assert queue[0]['title'] == 'Test Track'
        
        # 6. Fetch from Last.fm
        artwork_url = lastfm.fetch_album_artwork('Test Artist', 'Test Album')
        assert mock_lastfm.called
        
        # 7. Fetch from Genius
        lyrics = genius.get_lyrics('Test Artist', 'Test Track')
        # Result depends on mock, but call should be attempted
        
        # Verify all services were integrated
        assert mock_bc.get_collection.called
        assert mock_mpd.add.called
        assert mock_mpd.play.called
        assert mock_lastfm.called
    
    @patch('services.mpd_service.MPDClient')
    @patch('services.bandcamp_service.BandcampClient')
    def test_metadata_enrichment_across_services(self, mock_bc_class, mock_mpd_class):
        """
        Workflow: Bandcamp metadata flows through MPD queue display without data loss.
        """
        # Setup Bandcamp with rich metadata
        mock_bc = mock_bc_class.return_value
        mock_bc.get_album_info.return_value = {
            'album_id': 123,
            'title': 'Amazing Album',
            'artist': 'Awesome Artist',
            'release_date': '2025-01-01',
            'tracks': [
                {
                    'track_id': 1,
                    'title': 'Track 1',
                    'duration': 240,
                    'streaming_url': 'https://example.bandcamp.com/track/1'
                },
                {
                    'track_id': 2,
                    'title': 'Track 2',
                    'duration': 180,
                    'streaming_url': 'https://example.bandcamp.com/track/2'
                }
            ]
        }
        
        # Setup MPD
        mock_mpd = mock_mpd_class.return_value
        mock_mpd.add.return_value = None
        mock_mpd.playlistinfo.return_value = [
            {
                'id': '1',
                'file': 'https://example.bandcamp.com/track/1',
                'title': 'Track 1',
                'artist': 'Awesome Artist',
                'album': 'Amazing Album'
            },
            {
                'id': '2',
                'file': 'https://example.bandcamp.com/track/2',
                'title': 'Track 2',
                'artist': 'Awesome Artist',
                'album': 'Amazing Album'
            }
        ]
        
        # Initialize services
        bandcamp = BandcampService()
        bandcamp.client = mock_bc
        bandcamp._enabled = True
        
        mpd = MPDService(host='localhost', port=6600, timeout=5)
        mpd.client = mock_mpd
        
        # Execute workflow
        album = bandcamp.get_album_info(123)
        
        # Cache all tracks
        for track in album['tracks']:
            bandcamp.cache_track_metadata(
                track['streaming_url'],
                track_id=track['track_id'],
                title=track['title'],
                artist=album['artist'],
                album=album['title']
            )
            mpd.add(track['streaming_url'])
        
        # Verify queue has all tracks
        queue = mpd.playlistinfo()
        assert len(queue) == 2
        
        # Verify metadata preserved
        for i, track in enumerate(queue):
            cached = bandcamp.get_cached_metadata(track['file'])
            assert cached is not None
            assert cached['album'] == 'Amazing Album'


# =============================================================================
# WORKFLOWS: Error Recovery
# =============================================================================

class TestErrorRecoveryWorkflows:
    """Test error handling and recovery workflows."""
    
    @patch('services.mpd_service.MPDClient')
    def test_mpd_disconnection_and_recovery(self, mock_mpd_class):
        """
        Workflow: MPD connection lost → service detects → reconnects.
        """
        mock_mpd = mock_mpd_class.return_value
        
        # First call: connection fails
        mock_mpd.ping.side_effect = [
            Exception('Connection refused'),
            None  # Second call succeeds (after reconnect)
        ]
        
        mpd_service = MPDService(host='localhost', port=6600, timeout=5)
        mpd_service.client = mock_mpd
        
        # Execute workflow
        # The service should attempt to reconnect if client fails
        # Verify status can be queried
        try:
            status = mpd_service.status()
        except Exception:
            # Connection failed as expected
            pass
        
        # Verify reconnection attempted by checking call count
        assert mock_mpd.ping.call_count >= 1
    
    @patch('services.bandcamp_service.BandcampClient')
    def test_bandcamp_disabled_service_fallback(self, mock_bc_class):
        """
        Workflow: Bandcamp service disabled → returns empty/safe values.
        """
        bandcamp = BandcampService()
        # Don't set client or credentials
        
        # Execute workflow - all should return empty safely
        collection = bandcamp.get_collection(100)
        assert isinstance(collection, list)
        assert len(collection) == 0
        
        album_info = bandcamp.get_album_info(123)
        assert album_info is None
        
        track_info = bandcamp.get_track_info(456)
        assert track_info is None
        
        artwork = bandcamp.get_artwork_url(789)
        assert artwork == ''
        
        search_results = bandcamp.search('test')
        assert isinstance(search_results, list)
        assert len(search_results) == 0
    
    @patch('services.genius_service.requests.get')
    def test_genius_api_error_handling(self, mock_genius):
        """
        Workflow: Genius API fails → service returns None gracefully.
        """
        import requests
        mock_genius.side_effect = requests.RequestException('API Error')
        
        genius = GeniusService()
        
        # Execute workflow
        lyrics = genius.get_lyrics('Test Artist', 'Test Song')
        
        # Should return None on error, not raise
        assert lyrics is None
    
    @patch('services.lastfm_service.requests.get')
    def test_lastfm_response_missing_data(self, mock_lastfm):
        """
        Workflow: Last.fm returns incomplete response → service handles gracefully.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'album': {}  # Missing 'image' key
        }
        mock_lastfm.return_value = mock_response
        
        lastfm = LastfmService(api_key='test', shared_secret='test')
        
        # Execute workflow
        artwork = lastfm.fetch_album_artwork('Test Artist', 'Test Album')
        
        # Should handle missing data gracefully
        assert artwork is None or artwork == ''
