"""
Playlist Export Service for Maestro Server
Handles downloading queue to portable devices with format conversion

Features:
- Export current queue from MPD
- Format conversion: FLAC (native) or MP3 with variable bitrates
- Folder structure customization
- Cover art inclusion with toggle
- Progress tracking
- Async background processing
"""

import os
import json
import threading
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Callable
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Export state for progress tracking
_export_state = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current_song': '',
    'status': 'idle',
    'errors': [],
    'songs_processed': 0,
    'file_size_mb': 0,
    'export_file': None,  # Path to the exported ZIP file
    'timestamp': 0
}

def reset_export_state():
    """Reset export state between runs"""
    global _export_state
    _export_state = {
        'running': False,
        'progress': 0,
        'total': 0,
        'current_song': '',
        'status': 'idle',
        'errors': [],
        'songs_processed': 0,
        'file_size_mb': 0,
        'export_file': None,
        'timestamp': 0
    }

def get_export_status() -> Dict:
    """Get current export status"""
    return _export_state.copy()

def check_ffmpeg():
    """Check if FFmpeg is available for MP3 transcoding"""
    try:
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def get_folder_structure_path(song: Dict, structure: str) -> str:
    """
    Generate folder path based on selected structure
    
    Args:
        song: Song metadata dict
        structure: One of 'artist_album', 'artist_album_track', 'album_artist', 'artist', 'album', 'flat'
    
    Returns:
        Relative folder path for the song
    """
    artist = song.get('artist', 'Unknown Artist').replace('/', '_')
    album = song.get('album', 'Unknown Album').replace('/', '_')
    title = song.get('title', 'Unknown Track').replace('/', '_')
    
    structures = {
        'artist_album': f"{artist}/{album}",
        'artist_album_track': f"{artist}/{album}",  # Track filename will include artist - album - track
        'album_artist': f"{album} - {artist}",  # Album - Artist format
        'artist': f"{artist}",
        'flat': "",
        'album': f"{album}",
    }
    
    return structures.get(structure, structures['artist_album'])

def get_filename(song: Dict, folder_structure: str = 'artist_album') -> str:
    """Generate safe filename from song metadata"""
    title = song.get('title', 'Unknown Track')
    artist = song.get('artist', 'Unknown Artist')
    album = song.get('album', 'Unknown Album')
    
    # For artist_album_track structure, just use title since path includes artist/album
    if folder_structure == 'artist_album_track':
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
    else:
        # For other structures, include artist - album - title
        safe_title = "".join(c for c in f"{artist} - {album} - {title}" if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
    
    return safe_title or "untitled"

def transcode_to_mp3(input_file: str, output_file: str, bitrate: int = 192) -> bool:
    """
    Transcode audio file to MP3
    
    Args:
        input_file: Path to source audio file
        output_file: Path to output MP3 file
        bitrate: Bitrate in kbps (128, 192, 256, 320)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-b:a', f'{bitrate}k',
            '-q:a', '2',  # Variable bitrate quality
            '-y',  # Overwrite output file
            output_file
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per file
        )
        
        if result.returncode == 0:
            logger.info(f"Transcoded to MP3: {output_file}")
            return True
        else:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Transcode timeout: {input_file}")
        return False
    except Exception as e:
        logger.error(f"Transcode error: {e}")
        return False

def copy_cover_art(album_dir: str, export_folder: str) -> bool:
    """
    Copy cover.jpg from album directory to export folder
    
    Args:
        album_dir: Path to album directory on server
        export_folder: Path to export destination folder
    
    Returns:
        True if cover was copied, False otherwise
    """
    try:
        album_path = Path(album_dir)
        cover_names = ['cover.jpg', 'cover.png', 'folder.jpg', 'albumart.jpg', 'front.jpg']
        
        for cover_name in cover_names:
            cover_path = album_path / cover_name
            if cover_path.exists():
                dest_path = Path(export_folder) / cover_name
                shutil.copy2(cover_path, dest_path)
                logger.info(f"Copied cover art: {cover_name}")
                return True
        
        return False
    except Exception as e:
        logger.error(f"Cover art copy error: {e}")
        return False

def export_queue(
    queue: List[Dict],
    format_type: str = 'flac',
    mp3_bitrate: int = 192,
    folder_structure: str = 'artist_album',
    include_cover_art: bool = True,
    music_dir: str = '/media/music',
    callback: Optional[Callable] = None
) -> Dict:
    """
    Export queue to downloadable ZIP file
    
    Args:
        queue: List of song dicts from MPD queue
        format_type: 'flac' (native) or 'mp3'
        mp3_bitrate: Bitrate for MP3 (128, 192, 256, 320)
        folder_structure: Organization ('artist_album', 'artist', 'album', 'flat')
        include_cover_art: Whether to copy cover.jpg files
        music_dir: Root music directory
        callback: Progress callback function
    
    Returns:
        Dictionary with export results
    """
    global _export_state
    
    reset_export_state()
    _export_state['running'] = True
    _export_state['total'] = len(queue)
    _export_state['status'] = 'Preparing export...'
    
    try:
        # Create temp export directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_name = f"maestro_export_{timestamp}"
        temp_export_dir = tempfile.mkdtemp(prefix=export_name)
        temp_music_dir = os.path.join(temp_export_dir, 'music')
        os.makedirs(temp_music_dir, exist_ok=True)
        
        logger.info(f"Starting queue export to {temp_export_dir}")
        
        processed = 0
        skipped = 0
        errors = []
        copied_cover_count = 0
        
        # Check if FFmpeg is needed and available
        if format_type == 'mp3':
            if not check_ffmpeg():
                raise ValueError("FFmpeg not found. Cannot transcode to MP3.")
        
        for idx, song in enumerate(queue):
            _export_state['progress'] = idx + 1
            _export_state['current_song'] = f"{song.get('artist', 'Unknown')} - {song.get('title', 'Unknown')}"
            _export_state['status'] = f"Processing {_export_state['current_song']}..."
            
            if callback:
                callback(_export_state)
            
            try:
                # Get source file path
                file_path = song.get('file', '')
                if not file_path:
                    skipped += 1
                    continue
                
                # Resolve full path
                if not file_path.startswith('/'):
                    source_file = os.path.join(music_dir, file_path)
                else:
                    source_file = file_path
                
                if not os.path.exists(source_file):
                    errors.append(f"File not found: {file_path}")
                    skipped += 1
                    continue
                
                # Determine output path and extension
                folder_path = get_folder_structure_path(song, folder_structure)
                filename = get_filename(song, folder_structure)
                
                if format_type == 'flac':
                    # Native FLAC - copy original file
                    ext = Path(source_file).suffix.lower()
                    dest_filename = f"{filename}{ext}"
                else:
                    # MP3 transcode
                    dest_filename = f"{filename}.mp3"
                
                # Create destination folder structure
                export_song_dir = os.path.join(temp_music_dir, folder_path)
                os.makedirs(export_song_dir, exist_ok=True)
                dest_file = os.path.join(export_song_dir, dest_filename)
                
                # Copy or transcode file
                if format_type == 'flac':
                    shutil.copy2(source_file, dest_file)
                    logger.info(f"Copied: {dest_file}")
                else:
                    if not transcode_to_mp3(source_file, dest_file, mp3_bitrate):
                        errors.append(f"Failed to transcode: {file_path}")
                        skipped += 1
                        continue
                
                # Copy cover art if requested
                if include_cover_art:
                    album_dir = song.get('album_dir', os.path.dirname(source_file))
                    if copy_cover_art(album_dir, export_song_dir):
                        copied_cover_count += 1
                
                processed += 1
                _export_state['songs_processed'] = processed
                
            except Exception as e:
                error_msg = f"Error processing {song.get('title', 'Unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                skipped += 1
        
        _export_state['status'] = 'Creating ZIP archive...'
        if callback:
            callback(_export_state)
        
        # Create ZIP file
        zip_output_dir = tempfile.gettempdir()
        zip_filename = f"{export_name}.zip"
        zip_path = os.path.join(zip_output_dir, zip_filename)
        
        shutil.make_archive(
            os.path.splitext(zip_path)[0],  # Path without .zip
            'zip',  # Format
            temp_music_dir  # Directory to compress
        )
        
        # Calculate file size
        file_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        _export_state['file_size_mb'] = round(file_size_mb, 2)
        _export_state['export_file'] = zip_path
        
        # Cleanup temp directory
        shutil.rmtree(temp_export_dir, ignore_errors=True)
        
        _export_state['running'] = False
        _export_state['status'] = 'Export complete'
        
        return {
            'status': 'success',
            'message': f'Successfully exported {processed} songs',
            'songs_processed': processed,
            'songs_skipped': skipped,
            'covers_copied': copied_cover_count,
            'format': format_type,
            'bitrate': mp3_bitrate if format_type == 'mp3' else 'native',
            'file_size_mb': file_size_mb,
            'zip_file': zip_path,
            'zip_filename': zip_filename,
            'errors': errors
        }
    
    except Exception as e:
        _export_state['running'] = False
        _export_state['status'] = f'Error: {str(e)}'
        logger.error(f"Queue export error: {e}")
        return {
            'status': 'error',
            'message': f'Export failed: {str(e)}',
            'errors': [str(e)]
        }

def start_async_queue_export(
    queue: List[Dict],
    format_type: str = 'flac',
    mp3_bitrate: int = 192,
    folder_structure: str = 'artist_album',
    include_cover_art: bool = True,
    music_dir: str = '/media/music'
):
    """
    Start queue export in background thread
    
    Args:
        queue: List of songs to export
        format_type: Output format ('flac' or 'mp3')
        mp3_bitrate: Bitrate for MP3 output
        folder_structure: Folder organization scheme
        include_cover_art: Whether to include album art
        music_dir: Music library root directory
    """
    thread = threading.Thread(
        target=export_queue,
        args=(queue, format_type, mp3_bitrate, folder_structure, include_cover_art, music_dir),
        daemon=True
    )
    thread.start()
    return thread

def cleanup_old_exports(max_age_hours: int = 24):
    """
    Clean up old export ZIP files from temp directory
    
    Args:
        max_age_hours: Delete exports older than this
    """
    try:
        import time
        temp_dir = tempfile.gettempdir()
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for filename in os.listdir(temp_dir):
            if filename.startswith('maestro_export_') and filename.endswith('.zip'):
                filepath = os.path.join(temp_dir, filename)
                file_age = current_time - os.path.getmtime(filepath)
                
                if file_age > max_age_seconds:
                    try:
                        os.remove(filepath)
                        logger.info(f"Cleaned up old export: {filename}")
                    except Exception as e:
                        logger.error(f"Failed to delete {filename}: {e}")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
