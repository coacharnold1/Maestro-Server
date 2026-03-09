"""
conftest.py - Shared pytest fixtures for all tests.

Provides:
- Mock fixtures for external API calls
- Common test data
- Database/filesystem isolation
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json


@pytest.fixture
def mock_lastfm_api():
    """Mock Last.fm API responses."""
    def _mock_response(method, params):
        if method == 'auth.getToken':
            return {'token': 'test_token_12345'}
        elif method == 'auth.getSession':
            return {'session': {'key': 'test_session_key_67890'}}
        elif method == 'album.getinfo':
            return {
                'album': {
                    'name': 'Test Album',
                    'artist': 'Test Artist',
                    'image': [
                        {'size': 'mega', '#text': 'https://example.com/image_mega.jpg'},
                        {'size': 'extralarge', '#text': 'https://example.com/image_large.jpg'},
                    ]
                }
            }
        elif method == 'track.getinfo':
            return {
                'track': {
                    'name': 'Test Track',
                    'artist': {'name': 'Test Artist'},
                    'album': {
                        'name': 'Test Album',
                        'image': [
                            {'size': 'mega', '#text': 'https://example.com/track_image.jpg'},
                        ]
                    }
                }
            }
        elif method == 'track.updateNowPlaying':
            return {'nowplaying': {'artist': 'Test Artist', 'track': 'Test Track'}}
        elif method == 'track.scrobble':
            return {'scrobbles': {'scrobble': [{'artist': 'Test Artist'}]}}
        elif method == 'user.getTopArtists':
            return {
                'topartists': {
                    'artist': [
                        {'name': 'Artist 1', 'playcount': '100', 'url': 'https://example.com/artist1'},
                        {'name': 'Artist 2', 'playcount': '50', 'url': 'https://example.com/artist2'},
                    ]
                }
            }
        elif method == 'user.getTopAlbums':
            return {
                'topalbums': {
                    'album': [
                        {'name': 'Album 1', 'artist': {'name': 'Artist 1'}, 'playcount': '20', 'url': 'https://example.com/album1'},
                    ]
                }
            }
        elif method == 'user.getTopTracks':
            return {
                'toptracks': {
                    'track': [
                        {'name': 'Track 1', 'artist': {'name': 'Artist 1'}, 'playcount': '30', 'url': 'https://example.com/track1'},
                    ]
                }
            }
        return {}
    
    return _mock_response


@pytest.fixture
def mock_genius_api():
    """Mock Genius API responses."""
    return {
        'response': {
            'hits': [
                {
                    'result': {
                        'title': 'Test Song',
                        'artist': {'name': 'Test Artist'},
                        'url': 'https://example.com/song1'
                    }
                }
            ]
        }
    }


@pytest.fixture
def mock_bandcamp_api():
    """Mock Bandcamp API responses."""
    return {
        'items': [
            {
                'id': 1,
                'title': 'Test Album',
                'artist': 'Test Artist',
                'item_art_id': 123456,
                'item_url': 'https://example.bandcamp.com/album/test',
                'tracks': [
                    {'id': 1, 'title': 'Track 1', 'duration': 180},
                    {'id': 2, 'title': 'Track 2', 'duration': 240},
                ]
            }
        ]
    }


@pytest.fixture
def mock_mpd_client():
    """Mock MPD client."""
    client = MagicMock()
    
    # Mock basic responses
    client.ping.return_value = None
    client.status.return_value = {
        'state': 'play',
        'song': '0',
        'time': '10:180'
    }
    client.currentsong.return_value = {
        'artist': 'Test Artist',
        'title': 'Test Song',
        'album': 'Test Album',
        'file': 'Music/Artist/Album/song.mp3'
    }
    client.playlist.return_value = [
        'Music/Artist/Album/song1.mp3',
        'Music/Artist/Album/song2.mp3'
    ]
    
    return client


@pytest.fixture
def test_settings():
    """Return test settings dictionary."""
    return {
        'theme': 'dark',
        'enable_scrobbling': True,
        'lastfm_api_key': 'test_api_key',
        'lastfm_shared_secret': 'test_secret',
        'lastfm_session_key': 'test_session_key',
        'bandcamp_username': 'test_user',
        'bandcamp_identity_token': 'test_identity',
        'genius_access_token': 'test_genius_token'
    }
