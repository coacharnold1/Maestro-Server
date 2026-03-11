"""
Library Maintenance Service for Maestro Server
Handles cover standardization, cleanup, and library statistics

Features:
- Scan for album covers and standardize sizes
- Remove orphaned playlist files (.cue, .m3u)
- Generate library statistics
- Async scanning with progress tracking
"""

import os
import json
import threading
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable
import logging

logger = logging.getLogger(__name__)

# Scan state for progress tracking
_scan_state = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current_album': '',
    'status': 'idle',
    'errors': [],
    'found_covers': 0,
    'resized_covers': 0
}

# Stats cache for library statistics
_stats_cache = {
    'data': None,  # Cached stats dictionary
    'scanning': False,  # Whether currently scanning
    'music_dir': None,  # Which directory was scanned
    'timestamp': 0  # When stats were last updated
}

def reset_scan_state():
    """Reset scan state between runs"""
    global _scan_state
    _scan_state = {
        'running': False,
        'progress': 0,
        'total': 0,
        'current_album': '',
        'status': 'idle',
        'errors': [],
        'found_covers': 0,
        'resized_covers': 0
    }

def get_scan_status() -> Dict:
    """Get current scan status"""
    return _scan_state.copy()

def get_stats_status() -> Dict:
    """Get current library stats (cached or scanning status)"""
    global _stats_cache
    if _stats_cache['scanning']:
        return {'status': 'scanning', 'data': _stats_cache['data'], 'message': 'Library statistics scan in progress'}
    elif _stats_cache['data']:
        return {'status': 'success', 'data': _stats_cache['data']}
    else:
        return {'status': 'no_data', 'message': 'No cached statistics available. Click refresh to scan.'}

def get_cached_stats() -> Dict:
    """Get cached stats without blocking"""
    global _stats_cache
    return _stats_cache['data'] or {'status': 'no_data', 'message': 'Run a scan first'}

def start_async_stats_scan(music_dir: str):
    """
    Start library statistics scan in background thread
    Caches results for quick subsequent requests
    
    Args:
        music_dir: Root music directory to scan
    """
    global _stats_cache
    
    _stats_cache['scanning'] = True
    _stats_cache['music_dir'] = music_dir
    
    def _scan_stats():
        global _stats_cache
        try:
            stats = get_library_statistics(music_dir)
            timestamp = int(time.time())
            stats['scan_timestamp'] = timestamp
            _stats_cache['data'] = stats
            _stats_cache['timestamp'] = timestamp
        except Exception as e:
            logger.error(f"Async stats scan error: {e}")
            _stats_cache['data'] = {'status': 'error', 'message': str(e)}
        finally:
            _stats_cache['scanning'] = False
    
    thread = threading.Thread(target=_scan_stats, daemon=True)
    thread.start()

def is_mount_read_only(path: str) -> bool:
    """
    Check if a mount point is read-only
    
    Args:
        path: Path to check
    
    Returns:
        True if mount is read-only, False if writable
    """
    try:
        result = subprocess.run(
            ['mount'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Find the mount entry for this path
        path_obj = Path(path).resolve()
        
        for line in result.stdout.split('\n'):
            if path_obj.as_posix() in line:
                # Check if 'ro' appears in the mount options
                return ',ro,' in ',' + line + ',' or line.startswith(path + ' ')
        
        return False
    except Exception as e:
        logger.warning(f"Could not determine mount read-only status: {e}")
        return False

def scan_library_covers(music_dir: str, target_size: int = 500, callback: Optional[Callable] = None) -> Dict:
    """
    Scan library for album covers and standardize them
    
    Args:
        music_dir: Root music directory path
        target_size: Target pixel size for cover images (default 500x500)
        callback: Optional callback function to receive progress updates
    
    Returns:
        Dictionary with scan results
    """
    global _scan_state
    
    # Check if mount is read-only
    is_readonly = is_mount_read_only(music_dir)
    if is_readonly:
        logger.warning(f"Mount {music_dir} is READ-ONLY. Will scan and report covers but not resize them.")
    
    # Check if PIL is available for image processing
    try:
        from PIL import Image
    except ImportError:
        logger.warning("Pillow not installed - cover resizing disabled")
        return {'status': 'error', 'message': 'Pillow library not installed. Install with: pip install Pillow'}
    
    # Reset state
    reset_scan_state()
    _scan_state['running'] = True
    _scan_state['status'] = 'Scanning for covers...'
    
    try:
        music_path = Path(music_dir)
        if not music_path.exists():
            raise ValueError(f"Music directory not found: {music_dir}")
        
        # Find all album directories (directories with audio files)
        album_dirs = find_album_directories(music_path)
        _scan_state['total'] = len(album_dirs)
        
        found_covers = 0
        resized_covers = 0
        errors = []
        
        # Common cover filenames to look for
        cover_names = ['cover.jpg', 'cover.png', 'folder.jpg', 'albumart.jpg', 'front.jpg']
        
        for idx, album_dir in enumerate(album_dirs):
            _scan_state['progress'] = idx + 1
            _scan_state['current_album'] = album_dir.name
            _scan_state['status'] = f'Scanning {album_dir.name}...'
            
            if callback:
                callback(_scan_state)
            
            try:
                # Look for existing covers
                cover_found = False
                for cover_name in cover_names:
                    cover_path = album_dir / cover_name
                    if cover_path.exists():
                        cover_found = True
                        found_covers += 1
                        
                        # Check if resize is needed (only if not read-only)
                        if not is_readonly:
                            try:
                                img = Image.open(cover_path)
                                width, height = img.size
                                
                                # Only resize if larger than target size
                                if width > target_size or height > target_size:
                                    ratio = min(target_size / width, target_size / height)
                                    new_size = (int(width * ratio), int(height * ratio))
                                    img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
                                    img_resized.save(cover_path, quality=95)
                                    resized_covers += 1
                                    logger.info(f"Resized: {cover_path} → {new_size}")
                            except Exception as e:
                                errors.append(f"Error processing {cover_path}: {str(e)}")
                                logger.error(f"Error processing cover {cover_path}: {e}")
                        
                        break
                
                if not cover_found:
                    # Look for any image files that might be covers
                    image_files = list(album_dir.glob('*.jpg')) + list(album_dir.glob('*.png')) + list(album_dir.glob('*.jpeg'))
                    for img_file in image_files:
                        if img_file.stat().st_size > 10240:  # Skip very small files
                            found_covers += 1
                            if not is_readonly:
                                try:
                                    img = Image.open(img_file)
                                    width, height = img.size
                                    if width > target_size or height > target_size:
                                        ratio = min(target_size / width, target_size / height)
                                        new_size = (int(width * ratio), int(height * ratio))
                                        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
                                        img_resized.save(img_file, quality=95)
                                        resized_covers += 1
                                except Exception as e:
                                    errors.append(f"Error processing {img_file}: {str(e)}")
                                
            except Exception as e:
                errors.append(f"Error scanning {album_dir}: {str(e)}")
                logger.error(f"Error scanning album directory {album_dir}: {e}")
        
        _scan_state['status'] = 'Scan complete'
        _scan_state['found_covers'] = found_covers
        _scan_state['resized_covers'] = resized_covers
        _scan_state['errors'] = errors
        _scan_state['running'] = False
        
        if callback:
            callback(_scan_state)
        
        return {
            'status': 'success',
            'is_readonly': is_readonly,
            'albums_scanned': len(album_dirs),
            'covers_found': found_covers,
            'covers_resized': resized_covers,
            'errors': errors,
            'message': f'Scanned {len(album_dirs)} albums. Found {found_covers} covers{", resized " + str(resized_covers) if not is_readonly else " (library is read-only - covers not resized)"}.'
        }
    
    except Exception as e:
        _scan_state['running'] = False
        _scan_state['status'] = f'Error: {str(e)}'
        logger.error(f"Library cover scan error: {e}")
        return {'status': 'error', 'message': f'Scan error: {str(e)}'}

def find_album_directories(music_dir: Path) -> List[Path]:
    """
    Find all album directories (directories containing audio files)
    
    Args:
        music_dir: Root music directory
    
    Returns:
        List of album directory paths
    """
    audio_extensions = {'.mp3', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.alac'}
    album_dirs = []
    
    # Scan with max depth of 4 levels (Artist/Album/CD/Files deep)
    for dirpath, dirnames, filenames in os.walk(music_dir, topdown=True):
        # Limit depth
        depth = dirpath[len(str(music_dir)):].count(os.sep)
        if depth > 3:
            dirnames.clear()
            continue
        
        # Check if this directory has audio files
        has_audio = any(
            Path(f).suffix.lower() in audio_extensions
            for f in filenames
        )
        
        if has_audio:
            album_dirs.append(Path(dirpath))
    
    return sorted(album_dirs)

def cleanup_playlist_files(music_dir: str) -> Dict:
    """
    Remove .cue and .m3u playlist files from library
    
    SAFETY: If mount is read-only, reports what would be deleted without deleting
    
    Args:
        music_dir: Root music directory
    
    Returns:
        Dictionary with cleanup results
    """
    try:
        music_path = Path(music_dir)
        if not music_path.exists():
            raise ValueError(f"Music directory not found: {music_dir}")
        
        # Check if mount is read-only
        is_readonly = is_mount_read_only(music_dir)
        
        if is_readonly:
            logger.warning(f"Mount {music_dir} is READ-ONLY. Reporting files that WOULD be deleted without actually deleting.")
        
        removed_cue = 0
        removed_m3u = 0
        errors = []
        found_cue = []
        found_m3u = []
        
        # Find and optionally remove .cue files
        for cue_file in music_path.rglob('*.cue'):
            found_cue.append(str(cue_file))
            if not is_readonly:
                try:
                    cue_file.unlink()
                    removed_cue += 1
                    logger.info(f"Removed: {cue_file}")
                except Exception as e:
                    error_msg = f"Failed to remove {cue_file}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            else:
                removed_cue += 1  # Count as "would be removed"
                logger.info(f"Would remove (read-only): {cue_file}")
        
        # Find and optionally remove .m3u files
        for m3u_file in music_path.rglob('*.m3u'):
            found_m3u.append(str(m3u_file))
            if not is_readonly:
                try:
                    m3u_file.unlink()
                    removed_m3u += 1
                    logger.info(f"Removed: {m3u_file}")
                except Exception as e:
                    error_msg = f"Failed to remove {m3u_file}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            else:
                removed_m3u += 1  # Count as "would be removed"
                logger.info(f"Would remove (read-only): {m3u_file}")
        
        return {
            'status': 'success',
            'is_readonly': is_readonly,
            'removed_cue_files': removed_cue,
            'removed_m3u_files': removed_m3u,
            'total_removed': removed_cue + removed_m3u,
            'errors': errors,
            'message': f"{'Would remove' if is_readonly else 'Removed'} {removed_cue} .cue and {removed_m3u} .m3u files" + (" (READ-ONLY MOUNT - no files were deleted)" if is_readonly else ""),
            'found_cue': found_cue,
            'found_m3u': found_m3u
        }
    
    except Exception as e:
        logger.error(f"Playlist file cleanup error: {e}")
        return {'status': 'error', 'message': f'Cleanup error: {str(e)}'}

def scan_orphaned_artwork(music_dir: str) -> Dict:
    """
    Find orphaned image files not associated with audio files
    
    Args:
        music_dir: Root music directory
    
    Returns:
        Dictionary with orphaned files list
    """
    try:
        music_path = Path(music_dir)
        if not music_path.exists():
            raise ValueError(f"Music directory not found: {music_dir}")
        
        audio_extensions = {'.mp3', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.alac'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        
        orphaned = []
        
        # Scan each directory
        for dirpath, dirnames, filenames in os.walk(music_path):
            dir_path = Path(dirpath)
            
            # Check if directory has audio files
            has_audio = any(
                Path(f).suffix.lower() in audio_extensions
                for f in filenames
            )
            
            if not has_audio:
                # This directory has no audio - check for orphaned images
                for filename in filenames:
                    if Path(filename).suffix.lower() in image_extensions:
                        file_path = dir_path / filename
                        size_mb = file_path.stat().st_size / (1024 * 1024)
                        orphaned.append({
                            'path': str(file_path),
                            'size_mb': round(size_mb, 2),
                            'filename': filename
                        })
        
        return {
            'status': 'success',
            'orphaned_count': len(orphaned),
            'orphaned_files': orphaned[:100],  # Limit to 100 results
            'message': f'Found {len(orphaned)} orphaned image files'
        }
    
    except Exception as e:
        logger.error(f"Orphaned artwork scan error: {e}")
        return {'status': 'error', 'message': f'Scan error: {str(e)}'}

def get_library_statistics(music_dir: str, mpd_service=None) -> Dict:
    """
    Get comprehensive library statistics
    
    Args:
        music_dir: Root music directory
        mpd_service: Optional MPDService instance for additional stats
    
    Returns:
        Dictionary with library statistics
    """
    try:
        music_path = Path(music_dir)
        if not music_path.exists():
            raise ValueError(f"Music directory not found: {music_dir}")
        
        audio_extensions = {'.mp3', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.alac'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        
        total_size = 0
        audio_files = 0
        image_files = 0
        album_count = 0
        artist_dirs = set()
        
        album_dirs = find_album_directories(music_path)
        album_count = len(album_dirs)
        
        # Scan all files for statistics
        for dirpath, dirnames, filenames in os.walk(music_path):
            dir_path = Path(dirpath)
            
            for filename in filenames:
                file_path = dir_path / filename
                try:
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    suffix = Path(filename).suffix.lower()
                    if suffix in audio_extensions:
                        audio_files += 1
                    elif suffix in image_extensions:
                        image_files += 1
                except:
                    pass
            
            # Count artist directories (first level below music root)
            if dirpath != str(music_path):
                depth = dirpath[len(str(music_path)):].count(os.sep)
                if depth == 1:
                    artist_dirs.add(Path(dirpath).name)
        
        total_size_gb = total_size / (1024**3)
        
        stats = {
            'status': 'success',
            'library_path': str(music_path),
            'total_size_gb': round(total_size_gb, 2),
            'total_files': audio_files + image_files,
            'audio_files': audio_files,
            'image_files': image_files,
            'albums': album_count,
            'artists': len(artist_dirs),
            'message': f'Library contains {audio_files} audio files, {album_count} albums'
        }
        
        # Add MPD stats if service provided
        if mpd_service:
            try:
                client = mpd_service.get_client()
                if client:
                    stats_result = client.stats()
                    stats.update({
                        'mpd_artists': int(stats_result.get('artists', 0)),
                        'mpd_albums': int(stats_result.get('albums', 0)),
                        'mpd_songs': int(stats_result.get('songs', 0)),
                        'mpd_db_playtime': int(stats_result.get('db_playtime', 0))
                    })
            except Exception as e:
                logger.warning(f"Could not get MPD stats: {e}")
        
        return stats
    
    except Exception as e:
        logger.error(f"Library statistics error: {e}")
        return {'status': 'error', 'message': f'Statistics error: {str(e)}'}

def start_async_cover_scan(music_dir: str, target_size: int = 500, callback: Optional[Callable] = None):
    """
    Start cover scanning in background thread
    
    Args:
        music_dir: Root music directory
        target_size: Target pixel size for covers
        callback: Optional progress callback
    """
    thread = threading.Thread(
        target=scan_library_covers,
        args=(music_dir, target_size, callback),
        daemon=True
    )
    thread.start()
    return thread
