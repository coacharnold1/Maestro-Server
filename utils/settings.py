"""
Settings management utilities for Maestro Server
Handles loading/saving user preferences, genre stations, and manual radio stations
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# File paths for different settings
def get_settings_file_path():
    """Get the path to settings.json"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings.json')

def get_genre_stations_file_path():
    """Get the path to genre_stations.json"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'genre_stations.json')

def get_artist_stations_file_path():
    """Get the path to artist_stations.json"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'artist_stations.json')

def get_manual_stations_file_path():
    """Get the path to manual_radio_stations.json"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'manual_radio_stations.json')


def load_settings() -> dict:
    """Load user settings from settings.json file"""
    settings_file = get_settings_file_path()
    try:
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading settings.json: {e}")
    
    # Return default settings if file doesn't exist or fails to load
    return {
        'theme': 'dark',
        'lastfm_api_key': '',
        'lastfm_shared_secret': '',
        'show_scrobble_toasts': True,
        'genius_client_id': '',
        'genius_client_secret': '',
        'genius_access_token': ''
    }


def save_settings(data: dict) -> bool:
    """Save user settings to settings.json file"""
    settings_file = get_settings_file_path()
    try:
        with open(settings_file, 'w') as f:
            json.dump(data, f, indent=2)
        try:
            os.chmod(settings_file, 0o600)
        except Exception as pe:
            print(f"Warning: could not set permissions on settings.json: {pe}")
        return True
    except Exception as e:
        print(f"Error saving settings.json: {e}")
        return False


def load_genre_stations() -> dict:
    """Load genre stations from JSON file"""
    genre_stations_file = get_genre_stations_file_path()
    try:
        if os.path.exists(genre_stations_file):
            with open(genre_stations_file, 'r') as f:
                return json.load(f)
        return {}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading genre stations: {e}")
        return {}


def save_genre_stations(stations: dict) -> bool:
    """Save genre stations to JSON file"""
    genre_stations_file = get_genre_stations_file_path()
    try:
        with open(genre_stations_file, 'w') as f:
            json.dump(stations, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving genre stations: {e}")
        return False


def load_artist_stations() -> dict:
    """Load artist stations from JSON file"""
    artist_stations_file = get_artist_stations_file_path()
    try:
        if os.path.exists(artist_stations_file):
            with open(artist_stations_file, 'r') as f:
                return json.load(f)
        return {}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading artist stations: {e}")
        return {}


def save_artist_stations(stations: dict) -> bool:
    """Save artist stations to JSON file"""
    artist_stations_file = get_artist_stations_file_path()
    try:
        with open(artist_stations_file, 'w') as f:
            json.dump(stations, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving artist stations: {e}")
        return False


def load_manual_stations() -> list:
    """Load manually added radio stations from persistent storage"""
    manual_stations_file = get_manual_stations_file_path()
    try:
        if os.path.exists(manual_stations_file):
            with open(manual_stations_file, 'r') as f:
                return json.load(f)
        return []
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading manual stations: {e}")
        return []


def save_manual_stations(stations: list) -> bool:
    """Save manually added stations to persistent storage"""
    manual_stations_file = get_manual_stations_file_path()
    try:
        with open(manual_stations_file, 'w') as f:
            json.dump(stations, f, indent=2)
        print(f"Saved {len(stations)} manual radio stations")
        return True
    except IOError as e:
        print(f"Error saving manual stations: {e}")
        return False


def add_manual_station(name: str, url: str, favicon: str = '') -> Tuple[bool, str]:
    """Add a new manually added radio station"""
    try:
        stations = load_manual_stations()
        
        # Check if URL already exists
        if any(s['url'] == url for s in stations):
            return False, "Station URL already exists"
        
        station = {
            'name': name.strip(),
            'url': url.strip(),
            'favicon': favicon.strip() if favicon else '',
            'added_date': datetime.now().isoformat(),
            'manual': True
        }
        
        stations.append(station)
        if save_manual_stations(stations):
            return True, "Station added successfully"
        return False, "Failed to save station"
    except Exception as e:
        print(f"Error adding manual station: {e}")
        return False, str(e)


def remove_manual_station(url: str) -> Tuple[bool, str]:
    """Remove a manually added station by URL"""
    try:
        stations = load_manual_stations()
        original_count = len(stations)
        stations = [s for s in stations if s['url'] != url]
        
        if len(stations) < original_count:
            save_manual_stations(stations)
            return True, "Station removed successfully"
        return False, "Station not found"
    except Exception as e:
        print(f"Error removing manual station: {e}")
        return False, str(e)
