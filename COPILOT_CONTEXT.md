# Copilot Context - READ THIS FIRST

⚠️ **TL;DR - IF YOU ONLY READ ONE THING:**
## Two Services Run Independently!
- **Main Web (port 5003)**: Edit → Copy to `/maestro/web/` → Restart `maestro-web.service`
- **Admin (port 5004)**: Edit → Copy to BOTH `/maestro/admin/` AND `/maestro/web/admin/` → Restart `maestro-admin.service`

**Steps for EVERY change:**
1. Edit in `/home/fausto/Maestro-Server` (git repo)
2. Copy to running directories (see which service below)
3. Restart correct service
4. Test the change
5. Commit to git and push
- **Without copy+restart, changes WILL NOT appear!**

## 🚨 CRITICAL: Environment & Paths

### Current Machine
**This is the DEVELOPMENT server at 192.168.1.209**

### Path Structure (ALWAYS REMEMBER THIS!)
- **Git Repository**: `/home/fausto/Maestro-Server` (where you edit files)
- **Main Web App**: `/home/fausto/maestro/web` (where maestro-web.service runs from)
- **Admin App**: Runs separately from same location but has own template dirs

### ⚠️ TWO SEPARATE SERVICES (READ CAREFULLY!)

**There are TWO independent Flask apps running:**

#### 1️⃣ **Main Maestro Web Service**
- **Service**: `maestro-web.service`
- **Port**: 5003
- **URL**: http://192.168.1.209:5003
- **Files Located At**:
  - Source: `/home/fausto/Maestro-Server/` (git repo)
  - Running: `/home/fausto/maestro/web/` 
  - Templates: `/home/fausto/maestro/templates/` AND `/home/fausto/maestro/web/templates/`
  - Static: `/home/fausto/maestro/web/static/`
- **Restart**: `sudo systemctl restart maestro-web.service`

#### 2️⃣ **Admin Service** (SEPARATE!)
- **Service**: `maestro-admin.service`
- **Port**: 5004
- **URL**: http://192.168.1.209:5004
- **Files**: Admin templates and Python in `/admin/` folder
- **Copy Templates To BOTH**:
  - `/home/fausto/maestro/admin/templates/` (template location 1)
  - `/home/fausto/maestro/web/admin/templates/` (template location 2)
- **Restart**: `sudo systemctl restart maestro-admin.service`
- **Pages**: library_management.html, audio_tweaks.html, system_admin.html, etc.

### ⚠️ CRITICAL DEPLOYMENT WORKFLOW (DO NOT SKIP STEPS)

**Changes ONLY appear on the live server if you copy files to the RUNNING directories!**

**MANDATORY for EVERY code change:**

1. ✅ **Edit file in `/home/fausto/Maestro-Server`** (git repo)
2. ✅ **MUST copy to correct running directory:**
   - **Main app**: Copy to `/home/fausto/maestro/web/`
   - **Admin app**: Copy to BOTH `/home/fausto/maestro/admin/` AND `/home/fausto/maestro/web/admin/`
3. ✅ **Restart correct service:**
   - Main app: `sudo systemctl restart maestro-web.service`
   - Admin app: `sudo systemctl restart maestro-admin.service`
4. ✅ **Test the change:**
   - Main: http://192.168.1.209:5003
   - Admin: http://192.168.1.209:5004
5. ✅ **THEN commit to git** and push to GitHub

### DANGER: Common Mistakes That Waste Time

❌ **WRONG**: "I edited the file in git repo, why isn't it working?"
- Because the running app serves from `/home/fausto/maestro/web/`, NOT the git repo!
- You MUST copy the files after editing

❌ **WRONG**: "The admin page changes aren't showing!"
- You probably only copied to `/maestro/web/admin/` but NOT `/maestro/admin/`
- ALWAYS copy admin templates to BOTH locations!
- Then restart maestro-admin.service (not maestro-web.service!)

❌ **WRONG**: "I restarted maestro-web.service but the admin page still didn't change"
- Admin uses maestro-admin.service, not maestro-web.service
- You restarted the WRONG service!
- Use: `sudo systemctl restart maestro-admin.service`

❌ **WRONG**: "The update-maestro.sh script reverted my changes!"
- The script runs `git stash` which resets uncommitted changes
- Always `git add` and `git commit` BEFORE running update script
- OR: Make changes AFTER running the update script

❌ **WRONG**: "I only deployed one template but others still have the old code"
- ALWAYS copy ALL affected files to the running directory
- Use wildcards: `sudo cp /home/fausto/Maestro-Server/templates/*.html /home/fausto/maestro/web/templates/`

❌ **WRONG**: "I changed the code but service still shows old behavior"
- You MUST restart the service after copying files
- Service restart is NOT optional

### Quick Copy Commands
```bash
# Main web app - Python files
sudo cp /home/fausto/Maestro-Server/app.py /home/fausto/maestro/web/app.py

# ⚠️ Main web app - Templates (copy to BOTH locations!)
sudo cp /home/fausto/Maestro-Server/templates/*.html /home/fausto/maestro/web/templates/
sudo cp /home/fausto/Maestro-Server/templates/*.html /home/fausto/maestro/templates/

# Main web app - Static files (JS, CSS)
sudo cp /home/fausto/Maestro-Server/static/* /home/fausto/maestro/web/static/

# ⚠️ ADMIN APP - Templates (copy to BOTH locations!)
sudo cp /home/fausto/Maestro-Server/admin/templates/*.html /home/fausto/maestro/admin/templates/
sudo cp /home/fausto/Maestro-Server/admin/templates/*.html /home/fausto/maestro/web/admin/templates/

# Admin app - Python files
sudo cp /home/fausto/Maestro-Server/admin/*.py /home/fausto/maestro/web/admin/

# After copying MAIN app files, restart MAIN service:
sudo systemctl restart maestro-web.service

# After copying ADMIN app files, restart ADMIN service:
sudo systemctl restart maestro-admin.service

# Verify main app (port 5003):
curl http://localhost:5003

# Verify admin app (port 5004):
curl http://localhost:5004
```

### Quick Reference: Which Service Runs Which Pages?

**Main Web Service (port 5003) - maestro-web.service**
- Browse albums, artists, genres
- Search results
- Playlist management
- Now playing display
- Settings
- Radio
- Recent albums

**Admin Service (port 5004) - maestro-admin.service**
- Library management (`/admin/` - URL localhost:5004/)
- Audio tweaks
- System administration
- Bandcamp settings
- CD ripper
- Database backup & restore
- Cover art management
- Queue export modal (library_management.html)

**Need to update Admin pages (e.g., library_management.html)?**
1. Copy to: `/home/fausto/maestro/admin/templates/` AND `/home/fausto/maestro/web/admin/templates/`
2. Restart: `sudo systemctl restart maestro-admin.service`
3. Test at: http://192.168.1.209:5004

### Safe Update Workflow

**For End Users - Simple One-Command Update:**
```bash
# Just run this - it pulls latest changes and updates everything automatically
./update.sh
```

**For Developers - Manual Process (if needed):**
```bash
# ALWAYS commit changes first
cd /home/fausto/Maestro-Server
git add -A
git commit -m "your message"

# THEN run the bootstrap script (pulls latest, then runs update)
cd /home/fausto
/home/fausto/Maestro-Server/update.sh

# This will automatically copy files and restart services
```

**How It Works:**
- `update.sh` (bootstrap) → Pulls git first → Then runs `update-maestro.sh` with latest changes
- This ensures script updates are picked up immediately without needing to run twice
- The wrapper approach is transparent and foolproof

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

**Last Updated**: March 11, 2026
**Maintainer**: fausto
**Current Version**: 3.6.0
**Environment**: Production Server (192.168.1.209)

---

## 📋 Feature Documentation (v3.6.0)

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

## 🏗️ DEVELOPMENT ROADMAP

**See [WHATS_NEXT.md](WHATS_NEXT.md) for the complete roadmap.**

**Current Status as of March 8, 2026:**
- ✅ Phase 1-3: Completed (routes, radio navbar, bandcamp metadata)
- 📋 Phase 4: Next priority - Services Extraction (2-3 days)
- 📋 Phase 5: After Phase 4 - Test Suite (1-2 days)
- 📋 Phase 6-8: Feature additions (album art tool, playlist export, etc.)

**Next Action:** Start Phase 4 (Services Extraction) to refactor code for maintainability before adding new features.

---

**Recent Work (March 2-4, 2026):**
- v3.2.1: Mobile navbar redesign (9 pages updated, all themes)
- Repository cleanup: Removed 6 test/debug files
- Album art bug fix: NOW PLAYING bar showing placeholder on production
  - Root cause: Missing `song_file` parameter in 9 pages
  - Fixed all 9 pages, deployed, verified working ✓
- Settings enhancement: Recent Albums Directory configuration
  - Added folder browser UI with modal picker
  - New API endpoint: `/api/list_music_directories`
  - Settings page now lets users change recent folder at runtime
  - Tested locally ✓, pushed to GitHub ✓

**Last Updated**: March 11, 2026
**Maintainer**: fausto
**Current Version**: 3.6.0
**Environment**: Dev (192.168.1.209), Production Arch (192.168.1.142)



