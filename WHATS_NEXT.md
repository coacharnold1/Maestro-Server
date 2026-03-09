# Maestro Server Development Roadmap

## 📊 Current Status Summary (Updated March 9, 2026)

**Session Focus:** MPD Connectivity Fixes + Service Extraction Pattern
- ✅ **Phase 4b.2 Complete:** GeniusService integration (lyrics functionality)
- ✅ **Phase 4b.3a Complete:** LastfmService album art extraction (foundation for phases 4b.3b-d)
- 🔄 **Phase 4b.3b Next:** Scrobbling hooks extraction (2 hours, ~1 hour per method)

**Framework Improvements:**
- Album art loading: Fixed and stable (HTTP 404/0 errors resolved)
- Route handlers: All fixed with proper MPD disconnect before response serialization
- Service architecture: Established pattern (import → initialize → pass via app_ctx → delegate)
- Code reduction: Replaced inline Last.fm API logic with clean service method calls

**Ready to Resume After Pause:** Phase 4b.3b scrobbling extraction is low-risk and can begin immediately

---

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

#### Phase 4b.2: GeniusService Extraction (DONE - March 9, 2026)
- Created `services/genius_service.py` with methods for lyrics search and instrumental detection
- Methods: `get_lyrics(artist, track)`, `is_likely_instrumental(title)`, `test_connection()`, `_fetch_lyrics_genius()`
- Integrated into app.py: Import, initialization, route handlers pass service via app_ctx
- Updated routes/integrations.py handlers:
  - `api_get_lyrics_handler()` → calls `genius_service.get_lyrics()` and `genius_service.is_likely_instrumental()`
  - `api_test_genius_handler()` → calls `genius_service.test_connection()`
- **Deployed and tested successfully** - /api/test_genius returns success, "Genius reachable and returned lyrics"
- **Benefits:** Encapsulates Genius API logic, decouples from app.py, reusable for future features
- Git commit: ec12325

#### Phase 4b.3: LastfmService Extraction (IN PROGRESS - Most Complex)
**Note:** Extracting in multiple low-risk sub-phases to minimize complexity
- **4b.3a:** Extract album art fetching only ✅ DONE (March 9, 2026)
- **4b.3b:** Extract scrobbling hooks (NEXT - PLANNED)
- **4b.3c:** Extract charts/OAuth flow (PLANNED)
- **4b.3d:** Refactor global variables → service injection (PLANNED)

##### Phase 4b.3a: Album Art Extraction (DONE - March 9, 2026)
- Created `services/lastfm_service.py` (168 lines, fully documented)
- Methods:
  - `fetch_album_artwork(artist, album)` → Calls album.getinfo, extracts best image size (mega/extralarge/large)
  - `fetch_track_artwork(artist, track)` → Calls track.getinfo for streams, navigates to album images
  - `test_connection()` → Verifies API key validity
- Integrated into app.py:
  - Import LastfmService, initialize with LASTFM_API_KEY
  - Updated /album_art route to delegate all Last.fm calls to service (3 separate call blocks replaced)
- **Deployed and tested successfully** - /album_art returns 200 OK with image data
- **Benefits:** 
  - Encapsulates all Last.fm image API logic (parameter construction, response parsing, error handling)
  - Enables reuse by 4b.3b (scrobbling) and 4b.3c (charts)
  - Cleaner app.py /album_art route (66 lines reduced to ~30 lines of service calls)
- Git commit: 08ccd1c

##### Phase 4b.3b: Scrobbling Hooks (PLANNED - NEXT)
- Extract methods: `update_now_playing(artist, album, track)`, `scrobble(artist, album, track, timestamp)`
- Dependency: Requires `lastfm_session_key` from settings
- Scope: Read-only operations during playback (no side effects)
- Risk: Low (self-contained, integrated in playback flow)
- Estimated: 1-2 hours

##### Phase 4b.3c: Charts/OAuth Flow (PLANNED)
- Extract methods: `request_token()`, `authorize_url()`, `get_session()`, `get_user_charts()`
- Includes: OAuth token management, session key persistence
- Risk: Medium (stateful, affects settings persistence)
- Estimated: 2 hours

##### Phase 4b.3d: Global Variables Cleanup (PLANNED)
- Replace global `lastfm_session_key` with service property
- Ensure all Last.fm routes pass service via app_ctx
- Clean up initialization, finalize service interface
- Risk: Low (cleanup-only, no feature changes)
- Estimated: 1 hour

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
