# CD Ripper TODO - Continue Tomorrow

## ✅ COMPLETED TODAY (Dec 18, 2025)

### Core Functionality
- ✅ CD detection (cdparanoia) - detects disc presence and track count
- ✅ CD drive detection (scans /dev/sr0-sr2, /dev/cdrom) - shows drive model and type
- ✅ Metadata lookup with intelligent fallback:
  1. MusicBrainz API (tries disc ID from cd-discid)
  2. If fails, uses abcde-musicbrainz-tool to get proper MB disc ID format
  3. Returns artist, album, year, track names
- ✅ Album art fetching with dual source:
  1. MusicBrainz Cover Art Archive (primary)
  2. Last.fm API (fallback) - uses keys from ~/maestro/web/settings.json
- ✅ CD ripping with abcde in background thread
  - Monitors progress by parsing abcde output
  - Updates rip_status dict for real-time progress
  - Encodes to FLAC with compression level 8
- ✅ Output format: "Artist - Album (Year)/## - Track Name.flac"
- ✅ Album art options (user-selectable):
  - Embed in FLAC tags
  - Save as cover.jpg in album folder
  - Both (default)
- ✅ Web UI displays:
  - Drive info
  - Disc detection status
  - Album art thumbnail (200x200)
  - Artist, album, year, track list
  - Rip progress bar with track numbers
  - Album art checkboxes
- ✅ Progress persistence - page checks rip status on load and restores progress view

### Technical Fixes Applied
- ✅ Installer: Added DEBIAN_FRONTEND=noninteractive to prevent postfix prompts
- ✅ Subprocess PATH fix: env={'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': ...}
- ✅ File paths corrected: /mnt/music → /media/music throughout
- ✅ Sudoers updated with CD commands: cdparanoia, cd-discid, abcde, abcde-musicbrainz-tool, eject
- ✅ **CRITICAL**: Deployment requires copying from /home/fausto/Maestro-Server to /home/fausto/maestro
  - Admin API: /home/fausto/maestro/admin/admin_api.py
  - Templates: /home/fausto/maestro/admin/templates/
  - Settings: ~/maestro/web/settings.json (for Last.fm keys)

### Files Modified
- admin/admin_api.py - all CD endpoints implemented
- admin/templates/cd_ripper.html - full UI with album art
- settings.json.example - cd_ripper section with album_art options
- install-maestro.sh - CD tools, sudoers, directory creation
- /etc/sudoers.d/maestro - CD command permissions

## 🔨 TODO FOR TOMORROW

### 1. CD Settings Page (admin/templates/cd_settings.html)
**Purpose**: Configure CD ripper settings via web UI instead of editing JSON

**Features Needed**:
- Output directory selector/input
- Format dropdown (FLAC/MP3/Ogg)
- Quality selector (High/Medium/Low)
- Metadata provider dropdown (MusicBrainz/CDDB/FreeDB - currently only MB works)
- Auto-eject checkbox
- Parallel encode checkbox
- Max processes slider (1-8)
- Album art settings:
  - Enable/disable
  - Embed checkbox
  - Save file checkbox
  - Filename input (default: cover.jpg)

**API Endpoints** (already exist in admin_api.py):
- GET /api/cd/settings - returns cd_ripper config
- POST /api/cd/settings - saves cd_ripper config
  - Validates output_dir exists and is under /media/music/
  - Writes to ~/maestro/settings.json

**Implementation Notes**:
- Copy structure from cd_ripper.html for styling consistency
- Use fetch() for GET/POST
- Show success/error toast messages
- Load current settings on page load
- Save button calls POST endpoint

### 2. File Browser Page (admin/templates/file_browser.html)
**Purpose**: Browse/manage ripped files before moving to MPD library

**Features Needed**:
- Directory tree view starting at /media/music/ripped/
- File list with:
  - Name, size, date
  - Album art thumbnail (if cover.jpg exists)
  - Action buttons: Move, Delete, Play preview?
- Breadcrumb navigation
- "Move to Library" button - moves folder to /media/music/ and runs mpc update
- "Delete" button - confirms and removes files/folders
- Create folder button
- Destination selector for move operations

**API Endpoints** (already exist in admin_api.py):
- GET /api/cd/files/browse?path=/media/music/ripped/ - lists directory
  - Returns: {files: [{name, size, type, modified}], current_path}
  - Security check: path must start with /media/music/
- POST /api/cd/files/move - moves file/folder
  - Body: {source, destination}
  - Runs: sudo mv, then mpc update
- POST /api/cd/files/delete - deletes file/folder
  - Body: {path}
  - Runs: sudo rm or sudo rm -rf
- POST /api/cd/files/mkdir - creates directory
  - Body: {path}

**Implementation Notes**:
- Use table or card layout for files
- Show icons for folders vs files
- Confirm destructive operations (delete, move)
- Display album art if cover.jpg/cover.png found in folder
- Disable operations on files outside /media/music/
- Add MPD library destination picker (browse /media/music/)

### 3. Navigation Links
**Update admin home page** (admin/templates/admin_home.html):
- Add "CD Ripper" card/link → /cd-ripper
- Add "CD Settings" card/link → /cd-settings  
- Add "File Browser" card/link → /files

**Update cd_ripper.html navigation**:
- Add link to CD Settings
- Add link to File Browser
- Add "Back to Admin Home" link

### 4. Testing & Polish
- Test full workflow:
  1. Insert disc
  2. View metadata and album art
  3. Adjust settings
  4. Start rip
  5. Navigate away and back (verify progress restoration)
  6. Wait for completion
  7. Browse files
  8. Move to library
  9. Verify MPD sees new files
- Test edge cases:
  - No disc inserted
  - Unknown disc (no metadata)
  - No album art available
  - Network timeout on API calls
  - Disk full during rip
- Remove DEBUG print statements from production code
- Add error handling for failed rips
- Add "Cancel Rip" button

### 5. Documentation
- Update CD_RIPPING_INTEGRATION.md with:
  - Album art sources (MusicBrainz + Last.fm)
  - Folder format: "Artist - Album (Year)"
  - Complete workflow screenshots
  - Troubleshooting section
- Update README with CD ripping features
- Add to CHANGELOG.md

### 6. Deployment to Production (.142)
- Sync all files from .209 to .142:
  - admin/admin_api.py
  - admin/templates/
  - settings.json.example
  - install-maestro.sh
- Restart services on .142
- Test full workflow on production

## 📋 TECHNICAL NOTES FOR TOMORROW

### File Paths
- **Development**: /home/fausto/Maestro-Server/
- **Deployed**: /home/fausto/maestro/
- **Settings**: ~/maestro/web/settings.json (Last.fm keys)
- **Output**: /media/music/ripped/
- **Library**: /media/music/

### Deployment Command
```bash
sudo cp /home/fausto/Maestro-Server/admin/admin_api.py /home/fausto/maestro/admin/admin_api.py
sudo cp /home/fausto/Maestro-Server/admin/templates/*.html /home/fausto/maestro/admin/templates/
sudo systemctl restart maestro-admin.service
```

### API Endpoints Summary
**Already Implemented**:
- GET /api/cd/drives - list CD drives
- GET /api/cd/status - disc present, track count
- GET /api/cd/info - metadata + album art URL
- GET /api/cd/settings - get cd_ripper config
- POST /api/cd/settings - save cd_ripper config
- POST /api/cd/rip - start rip (body: {format, output_dir, album_art: {embed, save_file}})
- GET /api/cd/rip-status - progress monitoring
- POST /api/cd/eject - eject disc
- GET /api/cd/files/browse - list directory
- POST /api/cd/files/move - move file/folder + mpc update
- POST /api/cd/files/delete - delete file/folder + mpc update
- POST /api/cd/files/mkdir - create directory

### Album Art Pipeline
1. Get disc metadata from MusicBrainz
2. If release has release_id, try Cover Art Archive: https://coverartarchive.org/release/{release_id}
3. If no art, query Last.fm: album.getinfo with api_key from ~/maestro/web/settings.json
4. Return URL to web UI for display
5. During rip, abcde with COVERARTWGET=y fetches art
6. If embed=true, adds to ACTIONS: embedalbumart
7. If save_file=true, sets COVERART=y (saves cover.jpg in folder)

### abcde Configuration (generated in rip_cd())
- OUTPUTFORMAT='${ARTISTFILE} - ${ALBUMFILE} (${CDYEAR})/${TRACKNUM} - ${TRACKFILE}'
- CDDBMETHOD=musicbrainz
- ACTIONS=cddb,read,encode,tag,move[,embedalbumart],clean
- COVERART=y (if save_file)
- COVERARTWGET=y (fetch from internet)
- ALBUMARTFILE="cover.jpg"

### Current Rip Status Global Dict
```python
rip_status = {
    'active': bool,
    'progress': int (0-100),
    'current_track': int,
    'total_tracks': int,
    'status': str,
    'error': str or None
}
```

### Gotchas Discovered
1. **Disc ID Format**: cd-discid returns CDDB format (9409300c), MusicBrainz needs different format (GPd9wUJKvttBDix8GnEOyukhoZ8-) - use abcde-musicbrainz-tool to convert
2. **Subprocess PATH**: Must set env={'PATH': '/usr/local/bin:/usr/bin:/bin'} or abcde can't find system commands
3. **run_command return**: Returns dict with keys 'success', 'returncode', 'stdout', 'stderr' (not CompletedProcess object)
4. **MusicBrainz API**: Must include 'Accept: application/json' header, use ?inc=artist-credits+recordings
5. **Last.fm Settings**: Read from ~/maestro/web/settings.json (not ~/maestro/settings.json)
6. **Service Restart**: Changes to Python files require systemctl restart maestro-admin.service

## 🎯 PRIORITY FOR TOMORROW
1. File Browser (most useful immediately after rip completes)
2. CD Settings page
3. Navigation links
4. Testing and polish
5. Remove DEBUG statements
6. Deploy to .142

## 🚀 CURRENT STATUS
- CD ripping is 100% functional
- Metadata lookup working (MusicBrainz + fallback)
- Album art working (Cover Art Archive + Last.fm fallback)
- Web UI showing all info
- Progress monitoring working
- Ready for file management UI

Everything is working great! Just need the management/settings UIs tomorrow.
