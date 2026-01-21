"""
Logitech Media Server (LMS) Client
Provides JSON-RPC API interface for controlling Squeezebox players
"""

import requests
import json
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class LMSClient:
    """Client for interacting with Logitech Media Server via JSON-RPC"""
    
    def __init__(self, host: str = "localhost", port: int = 9000, timeout: int = 5):
        """
        Initialize LMS client
        
        Args:
            host: LMS server hostname or IP
            port: LMS server port (default 9000)
            timeout: Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}/jsonrpc.js"
    
    def _request(self, player_id: str, command: List[Any]) -> Optional[Dict]:
        """
        Send JSON-RPC request to LMS
        
        Args:
            player_id: Player MAC address or "" for server commands
            command: Command array (e.g., ["playlist", "play", "url"])
            
        Returns:
            Response dict or None on error
        """
        try:
            payload = {
                "id": 1,
                "method": "slim.request",
                "params": [player_id, command]
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", {})
            else:
                logger.error(f"LMS request failed: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"LMS request timeout to {self.host}:{self.port}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to LMS at {self.host}:{self.port}")
            return None
        except Exception as e:
            logger.error(f"LMS request error: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test connection to LMS server
        
        Returns:
            True if server is reachable
        """
        result = self._request("", ["version", "?"])
        return result is not None and "_version" in result
    
    def get_server_version(self) -> Optional[str]:
        """Get LMS server version"""
        result = self._request("", ["version", "?"])
        return result.get("_version") if result else None
    
    def get_players(self) -> List[Dict[str, str]]:
        """
        Get list of all connected Squeezebox players
        
        Returns:
            List of player dicts with keys: id (MAC), name, model, ip, connected
        """
        result = self._request("", ["players", 0, 999])
        
        if not result or "players_loop" not in result:
            return []
        
        players = []
        for player in result["players_loop"]:
            players.append({
                "id": player.get("playerid", ""),
                "name": player.get("name", "Unknown Player"),
                "model": player.get("model", "Unknown"),
                "ip": player.get("ip", ""),
                "connected": player.get("connected", 0) == 1
            })
        
        return players
    
    def get_player_status(self, player_id: str) -> Optional[Dict]:
        """
        Get current status of a player
        
        Args:
            player_id: Player MAC address
            
        Returns:
            Status dict with mode, current_title, time, etc.
        """
        result = self._request(player_id, ["status", "-", 1, "tags:"])
        
        if not result:
            return None
        
        return {
            "mode": result.get("mode", "stop"),  # play, pause, stop
            "time": result.get("time", 0),
            "title": result.get("current_title", ""),
            "playlist_index": result.get("playlist_cur_index", -1),
            "playlist_tracks": result.get("playlist_tracks", 0)
        }
    
    def play_url(self, player_id: str, url: str) -> bool:
        """
        Play a URL on a specific player
        
        Args:
            player_id: Player MAC address
            url: Stream URL to play
            
        Returns:
            True if command succeeded
        """
        # Clear playlist and add URL
        result = self._request(player_id, ["playlist", "play", url])
        return result is not None
    
    def stop(self, player_id: str) -> bool:
        """
        Stop playback on a player
        
        Args:
            player_id: Player MAC address
            
        Returns:
            True if command succeeded
        """
        result = self._request(player_id, ["stop"])
        return result is not None
    
    def pause(self, player_id: str) -> bool:
        """
        Pause playback on a player
        
        Args:
            player_id: Player MAC address
            
        Returns:
            True if command succeeded
        """
        result = self._request(player_id, ["pause", "1"])
        return result is not None
    
    def resume(self, player_id: str) -> bool:
        """
        Resume playback on a player
        
        Args:
            player_id: Player MAC address
            
        Returns:
            True if command succeeded
        """
        result = self._request(player_id, ["pause", "0"])
        return result is not None
    
    def set_volume(self, player_id: str, volume: int) -> bool:
        """
        Set volume on a player
        
        Args:
            player_id: Player MAC address
            volume: Volume level (0-100)
            
        Returns:
            True if command succeeded
        """
        volume = max(0, min(100, volume))  # Clamp 0-100
        result = self._request(player_id, ["mixer", "volume", str(volume)])
        return result is not None
    
    def sync_players(self, master_id: str, slave_ids: List[str]) -> bool:
        """
        Synchronize multiple players (multi-room audio)
        
        Args:
            master_id: Master player MAC address
            slave_ids: List of slave player MAC addresses
            
        Returns:
            True if command succeeded
        """
        # Join slaves to master
        slaves = ",".join(slave_ids)
        result = self._request(master_id, ["sync", slaves])
        return result is not None
    
    def unsync_player(self, player_id: str) -> bool:
        """
        Unsynchronize a player from any group
        
        Args:
            player_id: Player MAC address
            
        Returns:
            True if command succeeded
        """
        result = self._request(player_id, ["sync", "-"])
        return result is not None


# Factory function for easy instantiation
def create_lms_client(settings: Dict) -> Optional[LMSClient]:
    """
    Create LMS client from settings dict
    
    Args:
        settings: Dict with keys: lms_enabled, lms_host, lms_port
        
    Returns:
        LMSClient instance or None if disabled or invalid
    """
    if not settings.get("lms_enabled", False):
        return None
    
    host = settings.get("lms_host", "").strip()
    port = settings.get("lms_port", 9000)
    
    if not host:
        return None
    
    try:
        port = int(port)
    except (ValueError, TypeError):
        logger.error(f"Invalid LMS port: {port}")
        return None
    
    return LMSClient(host=host, port=port)
