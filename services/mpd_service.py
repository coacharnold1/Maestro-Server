"""
MPDService - Encapsulates all MPD (Music Player Daemon) operations

This service provides a clean interface for interacting with MPD, with:
- Explicit dependency injection (host, port, timeout via constructor)
- Error handling and connection management
- Wrapper methods for all MPD operations used in the app
"""

from mpd import MPDClient, ConnectionError, CommandError
import logging

logger = logging.getLogger(__name__)


class MPDService:
    """Service for managing MPD client connections and operations."""
    
    def __init__(self, host='localhost', port=6600, timeout=30, idletimeout=None):
        """
        Initialize MPDService with connection configuration.
        
        Args:
            host (str): MPD server hostname or IP. Default: 'localhost'
            port (int): MPD server port. Default: 6600
            timeout (int): Connection timeout in seconds. Default: 30
            idletimeout (int): Idle timeout for long-running queries. Default: None (no timeout)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.idletimeout = idletimeout
        self.client = None
    
    def _connect(self):
        """
        Internal method to establish MPD connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Always close existing connection first to avoid "Already connected" error
            if self.client is not None:
                try:
                    self.client.close()
                except:
                    pass
            
            # Create fresh client and connect
            self.client = MPDClient()
            self.client.timeout = self.timeout
            self.client.idletimeout = self.idletimeout
            self.client.connect(self.host, self.port)
            return True
        except ConnectionError as e:
            logger.error(f"MPD Connection Error: {e}")
            self.client = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MPD: {e}")
            self.client = None
            return False
    
    def get_client(self):
        """
        Get or create an MPD client connection.
        
        Returns:
            MPDClient: Connected MPD client instance, or None if connection failed
        """
        # Try to use existing connection, reconnect if needed
        if self.client is None:
            self._connect()
        else:
            try:
                # Verify connection is still alive with a ping
                self.client.ping()
            except Exception as ping_error:
                # Connection is dead, reconnect
                logger.debug(f"MPD ping failed, reconnecting: {ping_error}")
                self._connect()
        
        return self.client
    
    # Playback Control Methods
    
    def play(self, songpos=None):
        """
        Start playback.
        
        Args:
            songpos (int, optional): Position of song to play. If None, resumes playback.
        
        Returns:
            bool: True if successful, False otherwise
        """
        client = self.get_client()
        if not client:
            return False
        
        try:
            if songpos is not None:
                client.play(songpos)
            else:
                client.play()
            return True
        except Exception as e:
            logger.error(f"Error playing: {e}")
            return False
    
    def pause(self):
        """
        Pause playback.
        
        Returns:
            bool: True if successful, False otherwise
        """
        client = self.get_client()
        if not client:
            return False
        
        try:
            client.pause()
            return True
        except Exception as e:
            logger.error(f"Error pausing: {e}")
            return False
    
    def next(self):
        """
        Go to next track.
        
        Returns:
            bool: True if successful, False otherwise
        """
        client = self.get_client()
        if not client:
            return False
        
        try:
            client.next()
            return True
        except Exception as e:
            logger.error(f"Error going to next track: {e}")
            return False
    
    def previous(self):
        """
        Go to previous track.
        
        Returns:
            bool: True if successful, False otherwise
        """
        client = self.get_client()
        if not client:
            return False
        
        try:
            client.previous()
            return True
        except Exception as e:
            logger.error(f"Error going to previous track: {e}")
            return False
    
    def stop(self):
        """
        Stop playback.
        
        Returns:
            bool: True if successful, False otherwise
        """
        client = self.get_client()
        if not client:
            return False
        
        try:
            client.stop()
            return True
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            return False
    
    def seek(self, songpos, position):
        """
        Seek to position in current song.
        
        Args:
            songpos (int): Position of song in playlist
            position (int): Position in song in seconds
        
        Returns:
            bool: True if successful, False otherwise
        """
        client = self.get_client()
        if not client:
            return False
        
        try:
            client.seek(songpos, position)
            return True
        except Exception as e:
            logger.error(f"Error seeking: {e}")
            return False
    
    def setvol(self, volume):
        """
        Set playback volume.
        
        Args:
            volume (int): Volume level (0-100)
        
        Returns:
            bool: True if successful, False otherwise
        """
        client = self.get_client()
        if not client:
            return False
        
        try:
            client.setvol(volume)
            return True
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return False
    
    # Status Methods
    
    def status(self):
        """
        Get current playback status.
        
        Returns:
            dict: Status information or empty dict if error
        """
        client = self.get_client()
        if not client:
            return {}
        
        try:
            return client.status()
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {}
    
    # Playlist Management Methods
    
    def playlist(self):
        """
        Get current playlist (list of filenames).
        
        Returns:
            list: List of song filenames or empty list if error
        """
        client = self.get_client()
        if not client:
            return []
        
        try:
            return client.playlist()
        except Exception as e:
            logger.error(f"Error getting playlist: {e}")
            return []
    
    def playlistinfo(self, start=None, end=None):
        """
        Get current playlist with full song information.
        
        Args:
            start (int, optional): Start position
            end (int, optional): End position
        
        Returns:
            list: List of song dicts or empty list if error
        """
        client = self.get_client()
        if not client:
            return []
        
        try:
            if start is not None and end is not None:
                return client.playlistinfo(f"{start}:{end}")
            elif start is not None:
                return client.playlistinfo(start)
            else:
                return client.playlistinfo()
        except Exception as e:
            logger.error(f"Error getting playlistinfo: {e}")
            return []
    
    def add(self, path):
        """
        Add song or directory to playlist.
        
        Args:
            path (str): Song file path or directory
        
        Returns:
            bool: True if successful, False otherwise
        """
        client = self.get_client()
        if not client:
            return False
        
        try:
            client.add(path)
            return True
        except Exception as e:
            logger.error(f"Error adding to playlist: {e}")
            return False
    
    def clear(self):
        """
        Clear the entire playlist.
        
        Returns:
            bool: True if successful, False otherwise
        """
        client = self.get_client()
        if not client:
            return False
        
        try:
            client.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing playlist: {e}")
            return False
    
    def delete(self, pos):
        """
        Delete song from playlist by position.
        
        Args:
            pos (int): Position in playlist
        
        Returns:
            bool: True if successful, False otherwise
        """
        client = self.get_client()
        if not client:
            return False
        
        try:
            client.delete(pos)
            return True
        except Exception as e:
            logger.error(f"Error deleting from playlist: {e}")
            return False
    
    def move(self, pos, new_pos):
        """
        Move song in playlist to new position.
        
        Args:
            pos (int): Current position in playlist
            new_pos (int): New position in playlist
        
        Returns:
            bool: True if successful, False otherwise
        """
        client = self.get_client()
        if not client:
            return False
        
        try:
            client.move(pos, new_pos)
            return True
        except Exception as e:
            logger.error(f"Error moving song in playlist: {e}")
            return False
    
    # Search/Query Methods
    
    def search(self, tag, value):
        """
        Search for songs matching tag/value (case-insensitive).
        
        Args:
            tag (str): Tag name (album, artist, genre, etc.)
            value (str): Value to search for
        
        Returns:
            list: List of matching songs or empty list if error
        """
        client = self.get_client()
        if not client:
            return []
        
        try:
            return client.search(tag, value)
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def find(self, *args):
        """
        Find songs matching tag/value pairs (case-sensitive).
        
        Args:
            *args: Alternating tag and value pairs (tag1, value1, tag2, value2, ...)
        
        Returns:
            list: List of matching songs or empty list if error
        
        Example:
            find('artist', 'Beatles', 'album', 'Abbey Road')
        """
        client = self.get_client()
        if not client:
            return []
        
        try:
            return client.find(*args)
        except Exception as e:
            logger.error(f"Error finding songs: {e}")
            return []
    
    def list(self, tag, *args):
        """
        List all unique values for a tag, optionally filtered.
        
        Args:
            tag (str): Tag to list (album, artist, genre, etc.)
            *args: Additional tag/value pairs for filtering
        
        Returns:
            list: List of values or empty list if error
        
        Example:
            list('album', 'artist', 'Beatles')
        """
        client = self.get_client()
        if not client:
            return []
        
        try:
            if args:
                return client.list(tag, *args)
            else:
                return client.list(tag)
        except Exception as e:
            logger.error(f"Error listing: {e}")
            return []
    
    def listallinfo(self, path=''):
        """
        List all songs in directory with full information.
        
        Args:
            path (str): Directory path. Default: '' (root/all)
        
        Returns:
            list: List of songs or empty list if error
        """
        client = self.get_client()
        if not client:
            return []
        
        try:
            return client.listallinfo(path)
        except Exception as e:
            logger.error(f"Error listing all info: {e}")
            return []
    
    # Library Management Methods
    
    def update(self, path=None):
        """
        Update MPD's music database.
        
        Args:
            path (str, optional): Specific path to update. If None, updates entire database.
        
        Returns:
            int: Update job ID or 0 if error
        """
        client = self.get_client()
        if not client:
            return 0
        
        try:
            if path:
                return client.update(path)
            else:
                return client.update()
        except Exception as e:
            logger.error(f"Error updating database: {e}")
            return 0
    
    # Connection Management
    
    def disconnect(self):
        """
        Close the MPD connection.
        
        This method is called by route handlers to close connections
        after operations complete. It's an alias for close().
        """
        self.close()
    
    def close(self):
        """Close the MPD connection."""
        if self.client:
            try:
                self.client.close()
            except:
                pass
            finally:
                self.client = None
    
    def __del__(self):
        """Cleanup on object destruction."""
        self.close()
