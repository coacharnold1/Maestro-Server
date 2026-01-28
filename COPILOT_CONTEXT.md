# Copilot Context - READ THIS FIRST

## 🚨 CRITICAL: Environment & Paths

### Current Machine
**This is the DEVELOPMENT server at 192.168.1.209**

### Path Structure (ALWAYS REMEMBER THIS!)
- **Git Repository**: `/home/fausto/Maestro-Server` (where you edit files)
- **Running Application**: `/home/fausto/maestro/web` (where systemd service runs from)
- **Service Name**: `maestro-web.service`

### After ANY code change:
1. Edit file in `/home/fausto/Maestro-Server`
2. **MUST** copy to `/home/fausto/maestro/web` (running directory)
3. Restart service: `sudo systemctl restart maestro-web.service`
4. Commit to git in `/home/fausto/Maestro-Server`
5. Push to GitHub

### Quick Copy Commands
```bash
# Python files
sudo cp /home/fausto/Maestro-Server/app.py /home/fausto/maestro/web/app.py

# Templates
sudo cp /home/fausto/Maestro-Server/templates/*.html /home/fausto/maestro/web/templates/

# Admin files
sudo cp /home/fausto/Maestro-Server/admin/*.py /home/fausto/maestro/web/admin/
```

## 📍 Other Environments

### Development Machine (192.168.1.209)
- For testing major changes
- Same path structure as production

### Test Machine (192.168.1.106)
- For experimental features
- Same path structure

## 📦 Version Management

### Version File
Location: `/home/fausto/Maestro-Server/VERSION`

### Version Numbering Rules
- **Major (X.0.0)**: Breaking changes, major new features
- **Minor (0.X.0)**: New features, significant improvements, no breaking changes
- **Patch (0.0.X)**: Bug fixes, small tweaks, cosmetic changes

### CRITICAL: Update BOTH Files When Versioning
When bumping version (e.g., 2.9.1 → 2.9.2):
1. **Update /home/fausto/Maestro-Server/VERSION** (first line and Version: line)
2. **Update /home/fausto/Maestro-Server/app.py**:
   - Line 4: `APP_VERSION = "2.9.2"`
   - Line 5: `APP_BUILD_DATE = "2026-01-27"`
3. Copy both files to running dir before restarting
4. All templates pull version from `/api/version` endpoint (which reads APP_VERSION from app.py)

### ALWAYS Update VERSION After Changes
1. Edit VERSION file
2. Edit app.py (APP_VERSION and APP_BUILD_DATE)
3. Copy both files to running directory: 
   ```bash
   sudo cp /home/fausto/Maestro-Server/VERSION /home/fausto/maestro/web/VERSION
   sudo cp /home/fausto/Maestro-Server/app.py /home/fausto/maestro/web/app.py
   ```
4. Restart service
5. Commit with clear message
6. Push to GitHub

## 🔄 Standard Workflow

### For Code Changes:
1. ✅ Edit in `/home/fausto/Maestro-Server`
2. ✅ Copy to `/home/fausto/maestro/web`
3. ✅ Restart service if needed
4. ✅ Test the change
5. ✅ Update VERSION if appropriate
6. ✅ Git commit with clear message
7. ✅ Git push to GitHub

### For Testing:
- Always verify service status after restart
- Check logs: `sudo journalctl -u maestro-web.service -f`
- Test from browser at http://192.168.1.209:5003

## 🎯 Common Tasks

### Service Management
```bash
# Restart
sudo systemctl restart maestro-web.service

# Status
sudo systemctl status maestro-web.service

# Logs (live)
sudo journalctl -u maestro-web.service -f

# Logs (last 50 lines)
sudo journalctl -u maestro-web.service -n 50
```

### File Locations
- Music: NFS mounts (see /etc/fstab)
- Cache: `/home/fausto/Maestro-Server/cache/`
- Playlists: `/home/fausto/Maestro-Server/playlists/`
- Admin interface: `/home/fausto/Maestro-Server/admin/`

## ⚠️ Important Notes

### NFS Mounts
- Server: 192.168.1.110
- Health monitoring enabled
- Check status: `~/Maestro-Server/scripts/nfs-health-report.sh`

### Rate Limiting
- Album art has 2-second rate limit per client
- Prevents client loops from overwhelming NFS

### Python Environment
- Service uses venv at `/home/fausto/maestro/web/venv`
- Requirements in `/home/fausto/Maestro-Server/requirements.txt`

## 🚫 Common Mistakes to Avoid

1. ❌ Editing files only in git repo without copying to running dir
2. ❌ Forgetting to restart service after changes
3. ❌ Not updating VERSION file for significant changes
4. ❌ Making changes directly in `/home/fausto/maestro/web` (always work from git repo)
5. ❌ Not testing after deployment

## 📝 Commit Message Guidelines

- Be clear and descriptive
- Include what changed and why
- Reference issue/problem if fixing a bug
- Example: "Fix album art flashing loop - only update when song changes"

---

## 🎵 Genre Tags Feature (Added v2.9.2, Jan 27, 2026)

### What It Does
Displays genre metadata (🎵 icon) below artist names in:
- Search results (album/artist searches)
- Random album selection
- Song search results
- Recent albums page

### How to Add Genre Tags to New Pages

**Backend (app.py):**
- Extract genre from first song: `genre = song.get('genre', 'Unknown Genre')`
- Add to album dict: `'genre': genre`
- Add to song dict: `'genre': song.get('genre', 'Unknown Genre')`

**Template (HTML/JavaScript):**
- For albums: 
  ```html
  {% if item.get('genre') and item.get('genre') != 'Unknown Genre' %}
  <div style="font-size: 0.85em; color: #95a5a6; margin-top: 2px;">🎵 {{ item.get('genre') }}</div>
  {% endif %}
  ```
- For JavaScript/JSON:
  ```javascript
  ${genre && genre !== 'Unknown Genre' ? `<div style="font-size: 0.85em; color: #95a5a6;">🎵 ${escapeHtml(genre)}</div>` : ''}
  ```

### Files Modified for Genre Tags
- `/app.py`: `perform_search()`, `/random_albums`, `get_recent_albums_from_mpd()`
- `/templates/search_results.html`: Album and song result rendering
- `/templates/recent_albums.html`: Recent albums display

---

## 🔄 Replace Playlist Auto-Play Feature (Added v2.9.3, Jan 28, 2026)

### What It Does
When clicking "Replace Playlist" (🔄) button on browse_albums or recent_albums:
1. Fetches current playlist length from `/get_mpd_status`
2. Clears playlist and adds new album via `/clear_and_add_album`
3. Shows single toast: "▶️ {number} tracks cleared, now playing: {artist} - {album}"
4. Auto-plays after 500ms delay

### Key Changes

**Templates (browse_albums.html, recent_albums.html):**
- Updated `clearAndAddAlbum()` function to:
  - Call `/get_mpd_status?_t=Date.now()` with cache-busting
  - Extract `queue_length` from status response
  - Display track count in success message
  - Call `playbackAction('play')` after 500ms delay

**Backend (app.py):**
- Enhanced `/get_mpd_status` endpoint with no-cache headers
- Added cache control: `Cache-Control: no-cache, no-store, must-revalidate`

### Files Modified
- `/templates/browse_albums.html`: Updated `clearAndAddAlbum()` (lines 915-955)
- `/templates/recent_albums.html`: Updated `clearAndAddAlbum()` (lines 839-895)
- `/app.py`: Added cache headers to `/get_mpd_status` endpoint (line 4732)

### Important Notes
- Field name is `queue_length`, NOT `playlistlength`
- Must use cache-busting (`?_t=Date.now()`) on frontend GET requests
- Backend endpoints need `Cache-Control` headers for fresh data
- Duplicate prevention still active (checks `pendingAlbumAdditions` Set)

---

**Last Updated**: January 28, 2026
**Maintainer**: fausto
**Current Version**: 2.9.3
**Environment**: Production Server (192.168.1.209)
