# Copilot Context - READ THIS FIRST

⚠️ **TL;DR - IF YOU ONLY READ ONE THING:**
- Edit files in `/home/fausto/Maestro-Server` (git repo)
- COPY files to `/home/fausto/maestro/web/` IMMEDIATELY (running app is here!)
- Restart: `sudo systemctl restart maestro-web.service`
- Test on http://192.168.1.209:5003
- THEN commit to git and push
- Without the copy+restart, your changes WILL NOT appear!

## 🚨 CRITICAL: Environment & Paths

### Current Machine
**This is the DEVELOPMENT server at 192.168.1.209**

### Path Structure (ALWAYS REMEMBER THIS!)
- **Git Repository**: `/home/fausto/Maestro-Server` (where you edit files)
- **Running Application**: `/home/fausto/maestro/web` (where systemd service runs from)
- **Service Name**: `maestro-web.service`

### ⚠️ CRITICAL DEPLOYMENT WORKFLOW (DO NOT SKIP STEPS)

**Changes ONLY appear on the live server if you copy files to `/home/fausto/maestro/web/`**

**MANDATORY for EVERY code change:**

1. ✅ **Edit file in `/home/fausto/Maestro-Server`** (git repo)
2. ✅ **MUST copy to `/home/fausto/maestro/web`** (REQUIRED - app runs from here, not git repo)
3. ✅ **Restart service**: `sudo systemctl restart maestro-web.service`
4. ✅ **Test the change** on http://192.168.1.209:5003
5. ✅ **THEN commit to git** and push to GitHub

### DANGER: Common Mistakes That Waste Time

❌ **WRONG**: "I edited the file in git repo, why isn't it working?"
- Because the running app serves from `/home/fausto/maestro/web/`, NOT the git repo!
- You MUST copy the files after editing

❌ **WRONG**: "The update-maestro.sh script reverted my changes!"
- The script runs `git stash` which resets uncommitted changes
- Always `git add` and `git commit` BEFORE running update script
- OR: Make changes AFTER running the update script

❌ **WRONG**: "I only deployed one template but others still have the old code"
- ALWAYS copy ALL affected files to the running directory
- Use wildcards: `sudo cp /home/fausto/Maestro-Server/templates/*.html /home/fausto/maestro/web/templates/`

❌ **WRONG**: "I changed the code but service still shows old behavior"
- You MUST restart the service after copying files
- `sudo systemctl restart maestro-web.service` is NOT optional

### Quick Copy Commands
```bash
# Python files
sudo cp /home/fausto/Maestro-Server/app.py /home/fausto/maestro/web/app.py

# All templates (recommended)
sudo cp /home/fausto/Maestro-Server/templates/*.html /home/fausto/maestro/web/templates/

# All static files (JS, CSS)
sudo cp /home/fausto/Maestro-Server/static/* /home/fausto/maestro/web/static/

# Admin files
sudo cp /home/fausto/Maestro-Server/admin/*.py /home/fausto/maestro/web/admin/

# After copying, ALWAYS restart:
sudo systemctl restart maestro-web.service

# Verify it worked:
curl http://localhost:5003
```

### Safe Update Workflow
```bash
# ALWAYS commit changes first
cd /home/fausto/Maestro-Server
git add -A
git commit -m "your message"

# THEN run update script as fausto user (not root!)
cd /home/fausto
/home/fausto/Maestro-Server/update-maestro.sh

# This will automatically copy files and restart services
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

### 🚨 CRITICAL: Inline Scripts in Jinja2 Templates Don't Execute
**ISSUE FOUND (Jan 31, 2026):**
- Inline `<script>` tags in HTML templates DO NOT execute, even though they appear in served HTML
- External `<script src="/static/file.js"></script>` files work perfectly
- Root cause: Flask/Jinja2 rendering issue (possibly security-related)

**SOLUTION:**
- Move all JavaScript from inline `<script>` blocks to external `.js` files in `/static/`
- Reference them with `<script src="/static/filename.js"></script>`
- Example: `browse_albums.html` → `static/browse_albums.js`

**FILES AFFECTED:**
- `templates/browse_albums.html` - Fixed in v2.9.45 ✓
- Check other pages if JavaScript doesn't work

**WORKAROUND if you must use inline script:**
- Use external file instead (always works)
- If absolutely needed, try `<script nonce="">` but external is better

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

---

## 📋 Feature Documentation (v2.9.45)

### Browse Albums Feature
**Files:**
- Template: `templates/browse_albums.html` (699 lines, minimal logic)
- JavaScript: `static/browse_albums.js` (500+ lines, all logic here)
- API: `/api/browse/albums?artist=X&genre=Y`

**Flow:**
1. Browse → select Genre
2. Genre page → list Artists
3. Click Artist → Browse Albums page (loads via URL params)
4. `browse_albums.js` extracts `artist` and `genre` from URL
5. `loadAlbums()` fetches data from API
6. Displays album list with cover art, tracks, and action buttons

**Key Functions in static/browse_albums.js:**
- `loadAlbums(artist)` - Main fetch function
- `displayAlbums(albums)` - Renders album list
- `toggleAlbumDetails()` - Load/show tracks for album
- `displayMultiDiscTracks()` - Handle multi-disc albums
- `addAlbumToPlaylist()` - Add to queue
- `clearAndAddAlbum()` - Replace queue and auto-play

**Common Issues & Fixes:**
- If albums don't load: Check that `static/browse_albums.js` is deployed to `/home/fausto/maestro/web/static/`
- If no albums appear: Check API endpoint `/api/browse/albums` returns data
- Socket.io errors: Not critical - only for now-playing bar (disabled on test server in v2.9.45)
- JavaScript not executing: Check if using inline `<script>` - use external file instead!

**Important:** Remember inline scripts don't execute in Flask/Jinja2!

---

**Current Session (Jan 31, 2026):**
- Fixed critical bug: Albums page stuck on loading spinner
- Root cause: Inline scripts weren't executing in Jinja2 templates
- Solution: Moved all JavaScript to `static/browse_albums.js`
- Version bumped to 2.9.45
- Changes deployed and tested ✓
- Committed to GitHub ✓

**Last Updated**: January 31, 2026
**Maintainer**: fausto
**Current Version**: 2.9.45
**Environment**: Test Server (192.168.1.209)
