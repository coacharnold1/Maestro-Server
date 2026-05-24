# Bandcamp Metadata Fix - January 24, 2026

## Problem
Bandcamp streams were not displaying artist names or album artwork in "now playing" or history. Metadata was only visible on the Bandcamp browse page but not passed to MPD playback.

## Solution Summary
Implemented metadata caching system that preserves artist and artwork information from the Bandcamp collection and passes it to the backend when tracks are added.

## Files Modified

### 1. app.py
**Line 2700**: Added metadata cache dictionary
```python
bandcamp_metadata_cache = {}
```

**Lines 5627-5634**: Cache metadata when tracks are added (already existed, uses track_id)
```python
cache_key = f"track_{track_id_match.group(1)}"
bandcamp_metadata_cache[cache_key] = {
    'artist': artist,
    'title': title,
    'album': album,
    'artwork_url': artwork_url
}
```

**Lines 541-548**: Retrieve cached metadata for status display (track_id matching)
```python
if 'bandcamp.com' in song_file_path and 'track_id=' in song_file_path:
    import re
    track_id_match = re.search(r'track_id=(\d+)', song_file_path)
    if track_id_match:
        cache_key = f"track_{track_id_match.group(1)}"
        bc_meta = bandcamp_metadata_cache.get(cache_key)
```

**Lines 3902-3925**: Retrieve cached artwork for album art endpoint
- Added fix for relative artwork URLs (line 3924)
```python
if artwork_url.startswith('/api/bandcamp/artwork/'):
    artwork_url = f"http://localhost:5003{artwork_url}"
```

### 2. templates/bandcamp.html
**Lines 514-518**: Preserve collection data before fetching album details
```javascript
const collectionArtId = album.art_id;
const collectionArtist = album.band_name;
```

**Lines 536-544**: Fill in missing data from collection if album API returns empty values
```javascript
if (!albumData.art_id && collectionArtId) {
    albumData.art_id = collectionArtId;
}
if (!albumData.artist && collectionArtist) {
    albumData.artist = collectionArtist;
}
```

**Lines 558-565**: Construct artwork URL and assign to tracks
```javascript
const artworkUrl = album.art_id ? `/api/bandcamp/artwork/${album.art_id}?size=5` : '';
album.tracks.forEach(track => {
    track.artwork_url = artworkUrl;
    track.artist = album.artist || track.artist;
    track.album = album.title;
});
```

**Lines 611-617**: Debug logging in addTrack() (can be removed later)
```javascript
console.log('[DEBUG] Adding track:', {
    artist: track.artist,
    title: track.title,
    album: track.album,
    artwork_url: track.artwork_url
});
```

## How to Verify the Fix is Deployed

Run these commands to check if the fix is present:

```bash
# Check metadata cache exists
grep -n "bandcamp_metadata_cache = {}" /home/fausto/maestro/web/app.py

# Check artwork URL fix exists  
grep -n "if artwork_url.startswith('/api/bandcamp/artwork/')" /home/fausto/maestro/web/app.py

# Check collection data preservation
grep -n "const collectionArtist = album.band_name" /home/fausto/maestro/web/templates/bandcamp.html

# Check artwork assignment to tracks
grep -n "track.artwork_url = artworkUrl" /home/fausto/maestro/web/templates/bandcamp.html
```

Expected output:
- Line 2700: bandcamp_metadata_cache = {}
- Line 3924: if artwork_url.startswith('/api/bandcamp/artwork/'):
- Line 517: const collectionArtist = album.band_name;
- Line 563: track.artwork_url = artworkUrl;

## Git Commit
Commit: 6d35cb9
Branch: main
Date: January 24, 2026

## Testing
1. Navigate to http://localhost:5003/bandcamp
2. Open any album (including Various Artists compilations)
3. Add tracks to queue
4. Verify artist name and artwork appear in "now playing"
5. Check history - both metadata and artwork should be present

## Key Technical Details
- Uses track_id parameter from Bandcamp URLs for cache matching (URLs have changing timestamps)
- Bandcamp album API returns incomplete data, so we preserve collection list data
- Artwork URLs are relative paths that need conversion to absolute URLs for internal requests
- Works for all albums including Various Artists compilations
