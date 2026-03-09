# Maestro Server Development Roadmap

## ✅ Completed Phases

### Phase 1: Route Extraction (DONE - March 2026)
**Objective:** Break monolithic app.py into modular route handlers
- Extracted 40+ routes from app.py into dedicated handlers in `routes/` directory
- Pattern: Each handler has signature `handler(app_ctx, *args)` with Flask route wrappers
- Reduced app.py from 4,362 → 4,158 lines
- Bug fixes: Corrected argument order in bandcamp artwork/album handlers
- **Deployed to both production servers (192.168.1.209 + 192.168.1.130)**
- Git commits: Multiple, final = Phase 1 complete

### Phase 2: Radio Page Navbar Standardization (DONE - March 7, 2026)
**Objective:** Standardize radio page with modern fixed-header navbar like other pages
- Copied modern structure from search_results.html as reference
- Implemented `.fixed-header` with dual-row layout:
  - Row 1: Navigation links (Main, Queue, Add Music, Recent, Browse, Radio, Search-mobile)
  - Row 2: Search controls (type selector, autocomplete input, Go button, Random)
- CSS: Added 8 theme variants matching existing color schemes
- JavaScript: Integrated header search with autocomplete support
- **Deployed and tested successfully**
- Git commit: 7a643f8

### Phase 3: Bandcamp Metadata in Queue Display (DONE - March 7, 2026)
**Objective:** Fix Bandcamp track metadata not showing in Queue page
- **Root cause:** Frontend wasn't sending `track_id` to handler, cache key lookups failed
- **Solution implemented:**
  1. Frontend (templates/bandcamp.html): Added `track_id` to both single-track and bulk album add requests
  2. Backend caching (routes/integrations.py): Dual-key strategy - cache by both `track_id` AND `streaming_url`
  3. Queue display (routes/playlist.py): Enhanced `get_mpd_playlist_helper()` to enrich songs with cached metadata
- **Result:** Queue page now displays Bandcamp track titles, artists, albums, and artwork
- Git commit: b749f5e

### Associated: Version Bump to v3.3.0 (March 7, 2026)
- Updated VERSION file and app.py (APP_VERSION, APP_BUILD_DATE)
- Created comprehensive changelog documenting all three phases
- Deployed to production
- Git commits: 4523c55 (v3.3.0), 986213d (minor Go button text fix)

---

## � Upcoming Phases

### Phase 4a: MPDService Extraction (DONE - March 8, 2026)
**Objective:** Extract MPD operations into a service class with explicit dependencies
- Created `services/mpd_service.py` with `MPDService` class (514 lines, fully documented)
- Implemented 16 core MPD methods covering all playback, playlist, search, and status operations
- Connection pooling with automatic reconnect on ping failure
- Comprehensive error handling with logging
- Backward compatible: Routes still get raw client via `get_client()`
- Updated `app.py` to import and initialize MPDService with config (host, port, timeout)
- **Deployed and tested successfully** - MPD connection working, queue displaying correctly
- **Benefits:** Clear separation of concerns, easier to test, explicit dependencies
- Git commit: (pending)

### Phase 4b: Remaining Services Extraction (IN PROGRESS)
**Objective:** Continue refactoring remaining integrations in order of risk (simple → complex)

#### Phase 4b.1: BandcampService Extraction (DONE - March 8, 2026)
- Created `services/bandcamp_service.py` with `BandcampService` class (187 lines, fully documented)
- Implemented 8 methods: `get_collection()`, `get_album_info()`, `get_track_info()`, `get_artwork_url()`, `cache_track_metadata()`, `get_cached_metadata()`, `clear_cache()`, `search()`
- Metadata caching for queue display (by streaming URL and track_id)
- Proper error handling with logging
- Backward compatible: Routes still work, no breaking changes
- Updated app.py to initialize BandcampService with config from settings
- Updated routes/integrations.py handlers to use bandcamp_service
- Updated routes/playlist.py to pass bandcamp_service instead of bandcamp_metadata_cache
- **Deployed and tested successfully** - Collection API returning 68 albums, playlist loading correctly
- **Known limitation:** Some albums have no streamable tracks (unreleased, preview, or DRM content). Added logging to diagnose which albums are affected.
- **Benefits:** Service encapsulates all Bandcamp logic, easier to test, proper dependency injection
- Git commit: (pending)

#### Phase 4 Hotfixes: MPD Connectivity & Bandcamp Artwork Diagnostics (DONE - March 8, 2026)
**Issue 1: Random "Error fetching genres" on Browse page**
- **Root cause:** MPD client library failing to parse malformed genre entries in database (e.g., ' Avishai - Ziv Ravitz - Avishai Cohen')
- **Problem:** Route was calling `client.list('genre')` which uses python-mpd2's parser, failing on corrupt metadata
- **Solution:** Added fallback: if `list('genre')` fails, scan all songs via `listallinfo()` and collect unique genres
- **Result:** Browse page now handles malformed genres gracefully, always loads successfully
- **Code:** Modified `/routes/browse.py` api_browse_genres_handler() with fallback logic
- **Remaining issue:** Reload fixes the error - suggests race condition on first load (MPD connection timing?)
  - TODO: Add connection readiness check or delay before making genre requests
  - Consider adding retry logic with backoff

**Issue 2: Some Bandcamp albums missing artwork**
- **Diagnosis:** Bandcamp API doesn't always return `item_art_id` for certain albums
- **Solution:** Added comprehensive logging to identify which albums lack artwork
  - Backend logging in BandcampService.get_collection(): Logs albums missing art_id with examples
  - Frontend logging in bandcamp.html: Logs albums without artwork to browser console
  - Added img onerror handler: If artwork URL fails to load, gracefully hides broken image
- **Result:** Can now diagnose why specific albums don't show artwork
- **Code:** Modified `services/bandcamp_service.py` get_collection() + `templates/bandcamp.html` displayAlbums()

**Issue 3: Bandcamp metadata only showing in Bandcamp browse page**
- **Current behavior:** Bandcamp track metadata (title, artist, album) enriches queue only when adding from /bandcamp page
- **Problem:** Metadata cache is populated during Bandcamp page operations, but not accessible from other add sources
- **Needed:** Extend BandcampService to provide metadata lookup for tracks added from:
  - Search results page
  - Files/folders browser
  - Direct URL additions
- **TODO for next session:** 
  - Modify search handlers to check if track is Bandcamp (streaming URL pattern)
  - Pass bandcamp_service to those handlers
  - Enrich track metadata before returning to frontend
  - Store metadata in cache for later queue display

**Additional fixes:**
- Removed all `client.disconnect()` calls from all routes (browse, playback, playlist, status, debug, radio)
  - These were breaking shared MPD connection when concurrent requests occurred
  - MPDService's ping-based health check now handles reconnection automatically
- **Deployed:** All changes tested and running in production
- **Benefit:** Improved reliability + diagnostic visibility into remaining edge cases

#### Phase 4b.2: GeniusService (PLANNED)
- Extract album art fetching logic
- Methods: `fetch_album_art(artist, album)`, `search_labels(label_name)`
- Own caching & rate limiting
- Lower risk: Minimal dependencies, used only for search/display
- Estimated: 1 day

#### Phase 4b.2: GeniusService Extraction (PLANNED)
- Extract lyrics/genius lookup functionality
- Methods: `search_song(artist, track)`, `get_lyrics()`, `test_connection()`
- OAuth token management
- Medium risk: Independent feature, error-handling well-contained
- Estimated: 1 day
- **Known Issue:** Lyrics feature is currently broken - needs investigation
  - `/api/lyrics` endpoint may be failing
  - GeniusService code exists but not integrated into app.py
  - TODO: Test endpoint, verify Genius API connectivity, fix broken routes

#### Phase 4b.3: LastfmService (PLANNED - Most Complex)
**Note:** Extracted LAST to minimize risk. Multiple sub-phases:
- **4b.3a:** Extract album art fetching only (low risk subset)
- **4b.3b:** Extract scrobbling hooks (medium risk, playback-coupled)
- **4b.3c:** Extract charts/OAuth flow (medium risk, state management)
- **4b.3d:** Refactor global variables → service injection (cleanup)
- Total effort: 2-3 days across sub-phases
- **Strategy:** Deploy after each sub-phase, test extensively

**Why this order?**
- Build confidence with simpler services first
- Each success increases safety net for Last.fm work
- Can commit Bandcamp + Genius independently if needed
- Last.fm gets maximum testing + careful incremental approach

### Phase 5: Test Suite & CI/CD (PLANNED)
**Objective:** Foundation for safe future changes
- Unit tests for each service (mock external APIs)
- Integration tests for key flows:
  - User selects album → album art loads correctly
  - Scrobbling enabled → plays track → Last.fm receives scrobble
  - Search returns results → clicking plays track
- CI/CD hook: Tests run on every commit
- **Benefit:** Future changes = run tests + deploy with confidence
- **Estimated effort:** 1-2 days

### Phase 6: Library Maintenance Tool in Admin Panel (PLANNED)
**Objective:** Integrate cover standardization script into admin UI
- Create `/admin/library_maintenance.html` page with:
  - Section 1: Cover Standardization
    - "Scan for cover images" button (triggers `/api/library/scan_covers`)
    - Live progress log (WebSocket/Server-Sent Events)
    - Resize threshold selector
  - Section 2: Cleanup Tools
    - "Remove .cue and .m3u files" button
    - "Scan for orphaned artwork" button
- Backend API endpoints:
  - `POST /api/library/scan_covers` - Start cover scan (async)
  - `GET /api/library/scan_status` - Get progress
  - `POST /api/library/cleanup_playlists` - Remove CUE/M3U files
  - `GET /api/library/stats` - Library statistics
- Convert bash script to Python module in `services/library_maintenance.py`
- **Estimated effort:** 2-3 days

### Phase 7: Advanced Library Management Features (PLANNED)
**Objective:** Expand library maintenance with automation & advanced tools
- Scheduling System: Cron-like scheduling for cover scans and cleanup
- Additional Tools: Duplicate detection, metadata validation, ID3 tag editor, missing artwork detection
- Performance: Parallel processing, caching, incremental scanning
- History & Reports: Log all actions, generate reports, rollback capability
- **Estimated effort:** 3-4 days

### Phase 8: Playlist Export & Download with Transcoding (PLANNED)
**Objective:** Enable users to download playlists to USB/portable devices
- Export Modal UI: Select songs/albums, options for folder structure, cover art, transcode format
- Folder Structure: `Artist/Album/song.mp3` with optional `cover.jpg`
- Transcoding: MP3, AAC, FLAC, OGG with variable bitrates (128-320k)
- Backend: `/api/export/playlist` endpoint using FFmpeg
- **Estimated effort:** 2-3 days
