# Maestro Server - Changelog

## Version 3.6.6 - Multi-Directory Recent Albums Management (May 9, 2026)

### 📀 Enhanced Recent Albums Directories
- **Multi-Directory Support**: Configure multiple folders for scanning recent albums (e.g., downloads, backups, ripped music)
- **Admin Settings Interface**: New dedicated Settings page in Admin Panel for intuitive directory management
- **Visual Directory Browser**: Multi-select checkbox interface to browse and select directories from your system
- **Status Indicators**: Real-time validation showing directory existence, readability, and item count for each folder
- **Manual Path Entry**: Support for comma-separated paths or individual directory additions
- **Directory Display**: Clearly shows all configured recent album directories with full paths and status badges

### 🎵 Improved Recent Albums Retrieval
- **Increased Default Limit**: Bumped default limit from 25 to 50 albums to better handle multiple directories
- **Configurable Limit**: Added `limit` parameter to `/recent_albums` API endpoint for flexible results
- **Intelligent Path Conversion**: Automatically converts absolute paths to MPD-compatible relative paths
- **Multi-Directory Sorting**: Returns most recent albums across all configured directories, sorted by date

### 📋 Streamlined Main App Settings
- **Cleaner Settings Page**: Removed duplicate Recent Albums Directory text input from main app settings.html
- **Centralized Management**: Redirects users to Admin Panel → Settings for all recent directory configuration
- **Better UX**: Single source of truth for directory management, avoiding confusion

### 📁 Files Modified
- `admin/admin_api.py` - Added GET/POST endpoints for `/api/settings/recent-dirs`
- `admin/templates/admin_settings.html` - NEW: Full-featured settings interface for managing recent directories
- `admin/templates/admin_home.html` - Added Settings card to admin dashboard
- `app.py` - Increased default limit to 50, added limit parameter support
- `templates/settings.html` - Replaced Recent Albums Directory input with link to admin settings
- `VERSION` - Updated to 3.6.6

---

## Version 3.6.5 - Volume Controls & Search Fix (May 8, 2026)

### 🔊 Volume Controls on Secondary Pages
- **Added Volume Controls**: Mini volume controls (-2, +2 buttons) now available on all 6 secondary pages: Add Music, Queue/Playlist, Recent Albums, Browse Genres, Radio, and Search Results
- **Real-time Updates**: Volume display updates instantly via socket.io when adjusting volume
- **Theme-Aware Styling**: Volume box matches each of the 8 theme color schemes with subtle borders
- **Proper Spacing**: Added margin-bottom to prevent overlap with page content

### 🔍 Artist Search Fix
- **Fixed Album Grouping**: Artist searches now correctly return albums instead of individual tracks
- **Search Logic Improved**: Using MPD's `list('album', 'artist', query)` instead of `search()` for artist queries
- **Better UX**: Users searching for "Sun Ra" now get album results instead of 1,868+ individual tracks

### 🛠️ Backend Improvements
- **Socket.IO Broadcasting**: Volume changes now broadcast status updates to all connected clients
- **Route Context Fixes**: All secondary page routes now pass `mpd_info` context to templates for proper data display
- **Volume Persistence**: Volume settings persist across page navigation and socket updates

### 📁 Files Modified
- `app.py` - Artist search fix, route context fixes, volume broadcast endpoint
- `templates/add_music.html` - Volume controls, socket listener updates
- `templates/playlist.html` - Volume controls, socket listener updates
- `templates/recent_albums.html` - Volume controls, socket listener updates
- `templates/browse_genres.html` - Volume controls, socket listener updates
- `templates/radio.html` - Volume controls, socket listener updates
- `templates/search_results.html` - Volume controls, socket listener updates
- `VERSION` - Bumped to 3.6.5, updated date to May 8, 2026

---

## Version 3.2 - Enhanced Search & Autocomplete (March 3, 2026)

### 🔍 Universal Autocomplete Search
- **Autocomplete Across All Pages**: Implemented on search results and all 4 browse pages (albums, artists, genres, recent)
- **Consistent Behavior**: Same autocomplete dropdown style and functionality everywhere
- **"All Types" Option**: New search option to quickly search across artists, albums, and titles simultaneously
- **Fixed Search Parameters**: Corrected backend parameter names (album/artist/title instead of albums/artists/songs)

### 🎨 Album Artwork & Visual Improvements
- **Song Search Results**: Album artwork now displays as thumbnails next to song results (was missing)
- **Autocomplete Dropdown Layout**: Fixed CSS overlap issues between dropdown and search button
- **Playback Controls Redesign**: Reorganized layout to prevent centering issues from float properties
- **Theme-Specific Styling**: Now-playing-bar now respects all 8 themes with proper colors on browse_albums

### 📁 Files Modified
- `templates/search_results.html` - Album artwork display, autocomplete data fetching
- `templates/browse_albums.html` - Autocomplete, playback controls, theme CSS for now-playing-bar
- `templates/browse_artists.html` - Autocomplete, playback controls layout
- `templates/browse_genres.html` - Autocomplete, playback controls layout
- `templates/recent_albums.html` - Autocomplete, removed redundant Clear Playlist button
- `app.py` - Version bumped to 3.2

---

## Version 3.0.1 - Phase 2A UI Modernization (March 3, 2026)

### 🎭 Fixed Header Navigation (Phase 2A)
- **Persistent Navigation**: Fixed header bar stays visible during scrolling across all pages
- **Consistent Header Design**: Unified navigation across index.html, search_results.html, and all browse pages
- **Integrated Search Bar**: Search functionality in header with autocomplete suggestions
- **Dynamic Page Headings**: Genre names and artist names displayed in page titles

### 📚 Enhanced Browse Pages
- **browse_albums.html**: Full Phase 2A header integration with artist/album browsing
- **browse_artists.html**: Alphabetic artist listing with phase 2A header
- **browse_genres.html**: Genre-based music discovery with fixed header
- **recent_albums.html**: Recently added albums with consistent navigation

<<<<<<< HEAD
## Version 3.6.5 - Volume Controls & Search Fix (May 8, 2026)

### 🔊 Volume Controls on Secondary Pages
- **Added Volume Controls**: Mini volume controls (-2, +2 buttons) now available on all 6 secondary pages: Add Music, Queue/Playlist, Recent Albums, Browse Genres, Radio, and Search Results
- **Real-time Updates**: Volume display updates instantly via socket.io when adjusting volume
- **Theme-Aware Styling**: Volume box matches each of the 8 theme color schemes with subtle borders
- **Proper Spacing**: Added margin-bottom to prevent overlap with page content

### 🔍 Artist Search Fix
- **Fixed Album Grouping**: Artist searches now correctly return albums instead of individual tracks
- **Search Logic Improved**: Using MPD's `list('album', 'artist', query)` instead of `search()` for artist queries
- **Better UX**: Users searching for "Sun Ra" now get album results instead of 1,868+ individual tracks

### 🛠️ Backend Improvements
- **Socket.IO Broadcasting**: Volume changes now broadcast status updates to all connected clients
- **Route Context Fixes**: All secondary page routes now pass `mpd_info` context to templates for proper data display
- **Volume Persistence**: Volume settings persist across page navigation and socket updates

### 📁 Files Modified
- `app.py` - Artist search fix, route context fixes, volume broadcast endpoint
- `templates/add_music.html` - Volume controls, socket listener updates
- `templates/playlist.html` - Volume controls, socket listener updates
- `templates/recent_albums.html` - Volume controls, socket listener updates
- `templates/browse_genres.html` - Volume controls, socket listener updates
- `templates/radio.html` - Volume controls, socket listener updates
- `templates/search_results.html` - Volume controls, socket listener updates
- `VERSION` - Bumped to 3.6.5, updated date to May 8, 2026
=======
## Version 3.3 - Multi-Directory Recent Albums Management (May 9, 2026)

### 📀 Enhanced Recent Albums Directories
- **Multi-Directory Support**: Configure multiple folders for scanning recent albums (e.g., downloads, backups, ripped music)
- **Admin Settings Interface**: New dedicated Settings page in Admin Panel for intuitive directory management
- **Visual Directory Browser**: Multi-select checkbox interface to browse and select directories from your system
- **Status Indicators**: Real-time validation showing directory existence, readability, and item count for each folder
- **Manual Path Entry**: Support for comma-separated paths or individual directory additions
- **Directory Display**: Clearly shows all configured recent album directories with full paths and status badges

### 🎵 Improved Recent Albums Retrieval
- **Increased Default Limit**: Bumped default limit from 25 to 50 albums to better handle multiple directories
- **Configurable Limit**: Added `limit` parameter to `/recent_albums` API endpoint for flexible results
- **Intelligent Path Conversion**: Automatically converts absolute paths to MPD-compatible relative paths
- **Multi-Directory Sorting**: Returns most recent albums across all configured directories, sorted by date

### 📋 Streamlined Main App Settings
- **Cleaner Settings Page**: Removed duplicate Recent Albums Directory text input from main app settings.html
- **Centralized Management**: Redirects users to Admin Panel → Settings for all recent directory configuration
- **Better UX**: Single source of truth for directory management, avoiding confusion

### 📁 Files Modified
- `admin/admin_api.py` - Added GET/POST endpoints for `/api/settings/recent-dirs`
- `admin/templates/admin_settings.html` - NEW: Full-featured settings interface for managing recent directories
- `admin/templates/admin_home.html` - Added Settings card to admin dashboard
- `app.py` - Increased default limit to 50, added limit parameter support
- `templates/settings.html` - Replaced Recent Albums Directory input with link to admin settings
- `VERSION` - Updated to 3.3
>>>>>>> da3f2a7 (Feature: Multi-directory Recent Albums Management)

---

### 🔍 Universal Autocomplete Search
- **Autocomplete Across All Pages**: Implemented on search results and all 4 browse pages (albums, artists, genres, recent)
- **Consistent Behavior**: Same autocomplete dropdown style and functionality everywhere
- **"All Types" Option**: New search option to quickly search across artists, albums, and titles simultaneously
- **Fixed Search Parameters**: Corrected backend parameter names (album/artist/title instead of albums/artists/songs)

### 🎨 Album Artwork & Visual Improvements
- **Song Search Results**: Album artwork now displays as thumbnails next to song results (was missing)
- **Autocomplete Dropdown Layout**: Fixed CSS overlap issues between dropdown and search button
- **Playback Controls Redesign**: Reorganized layout to prevent centering issues from float properties
- **Theme-Specific Styling**: Now-playing-bar now respects all 8 themes with proper colors on browse_albums

### 📁 Files Modified
- `templates/search_results.html` - Album artwork display, autocomplete data fetching
- `templates/browse_albums.html` - Autocomplete, playback controls, theme CSS for now-playing-bar
- `templates/browse_artists.html` - Autocomplete, playback controls layout
- `templates/browse_genres.html` - Autocomplete, playback controls layout
- `templates/recent_albums.html` - Autocomplete, removed redundant Clear Playlist button
- `app.py` - Version bumped to 3.2

---

## Version 3.0.1 - Phase 2A UI Modernization (March 3, 2026)

### 🎭 Fixed Header Navigation (Phase 2A)
- **Persistent Navigation**: Fixed header bar stays visible during scrolling across all pages
- **Consistent Header Design**: Unified navigation across index.html, search_results.html, and all browse pages
- **Integrated Search Bar**: Search functionality in header with autocomplete suggestions
- **Dynamic Page Headings**: Genre names and artist names displayed in page titles

### 📚 Enhanced Browse Pages
- **browse_albums.html**: Full Phase 2A header integration with artist/album browsing
- **browse_artists.html**: Alphabetic artist listing with phase 2A header
- **browse_genres.html**: Genre-based music discovery with fixed header
- **recent_albums.html**: Recently added albums with consistent navigation

### 🎨 Theme & Styling
- **Comprehensive Theme Support**: All 8 themes (dark, light, high-contrast, desert, terminal, sunset, forest, midnight) now apply to fixed header elements
- **Smart Button Placement**: Bandcamp button on left, Clear Playlist on right with proper spacing
- **Enhanced Visual Hierarchy**: Improved spacing and consistency across all pages

### 🔊 Discovery Features
- **Better Music Randomization**: Collects 3 tracks per artist for more balanced variety
- **Clickable Artist Links**: Random album results link back to artist search for deeper exploration
- **Enhanced Debug Messages**: Shows similar artist count and candidate pool size

---

## Version 2.9.7 - External Information Links (February 28, 2026)

### 🔗 Artist & Album Information Links
- **Discogs Album Search Button**: Direct link to Discogs for album details and pricing
- **AllMusic Artist Search Button**: Direct link to AllMusic for artist biographies
- **Improved Information Buttons**: Better integration and placement in UI
- **External Link Strategy**: Streamlines music research without leaving the app

---

## Version 2.5.0 - Album Art Collage & Music Discovery (January 10, 2026)

### 🖼️ Interactive Album Art Collage
- **Click Album Art Feature**: Click album art to see interactive 3x3 grid of artist's albums
- **Local Album Discovery**: Prioritizes music from your collection, shows collaborations
- **Interactive Selection**: Click any album in collage to search and auto-close view
- **Dual Album Art Strategy**: Main page uses local art (fast), full-screen uses Last.fm (best quality)
- **Random Album Selection**: Shows 8 random albums from collection for discovery variety

### 📦 Layout & Organization
- **Compact 2-Column Layout**: Status info takes 50% less vertical space
- **Visual Hierarchy Improvements**: Blue labels, consistent spacing, highlighted "Up Next" section
- **File Path Display**: Clean popup instead of inline display (less clutter)
- **Mobile Protection**: Album art not clickable on small screens (<768px)

### 📺 Visual Enhancements
- **High-Resolution Images**: Last.fm mega size prioritized for full-screen viewing
- **UI Polish**: Hover effects on collage, album titles on hover, smooth transitions

---

## Version 2.4.1 - Search Results Fixes (December 26, 2025)

### 🐛 Bug Fixes
- **Album Drill-down Buttons**: Now work correctly with special characters in album names
- **Event Handling**: Replaced inline onclick with safe event delegation
- **Error Handling**: Better debugging and user feedback in search interface

---

## Version 2.4 - Internet Radio Streaming (December 25, 2025)

### 📻 Full Internet Radio Integration
- **Radio Browser API**: 22 countries of streaming radio stations
- **Smart Metadata Parsing**: Handles complex patterns like "Title by Artist - Station"
- **Toast Notifications**: Real-time feedback for user actions via Socket.IO
- **Station Favicon Art**: Station logos display as album art when Last.fm has no data
- **API Redundancy**: 3-server failover (de1, nl1, at1) with retry functionality
- **Stream Metadata Fallback**: Shows "🔴 LIVE: Station Name" for streams without metadata

### ✋ User Experience
- **Confirmation Dialog**: Asks before clearing playlist when playing radio
- **UI Polish**: Text overflow handling, no layout shift, reduced art jitter

---

## Version 2.3 - CD Ripping Enhancement (December 23, 2025)

### 💿 CD Ripping Improvements
- **Pre-download Album Art**: Cover art downloads BEFORE ripping starts
- **Special Character Support**: Albums with parentheses in names now rip correctly
- **Metadata Caching**: MusicBrainz metadata properly cached for reliable lookups
- **Album Organization**: Tracks and cover art stored in same folder structure

---

## Version 2.2 - Navigation & NFS Reliability (December 21, 2025)

### 🔤 Navigation Enhancements
- **Letter Jump Navigation**: Quick alphabetic navigation for artist lists with >50 items
- **Context-Aware UI**: Letter jump only appears when useful
- **Button Reorganization**: Charts moved up, MPD controls in footer for cleaner UI

### 🌐 NFS & Reliability
- **Improved NFS Mount Reliability**: MPD waits for remote-fs.target before starting
- **Auto-restart on Failure**: Automatic service restart if NFS mounts fail
- **Theme Consistency**: Search results now properly support all 8 themes

### 🧹 UI Polish
- **Removed Unused Elements**: Eliminated unclear Clear Cache button
- **Charts Button Size**: Increased prominence for better discoverability
- **Database Toast Behavior**: Only shows when manually triggered, not on page load

---

## Version 2.1 - Playlist Management & Themes (December 17, 2025)

### � Playlist Management
- **Playlist Save/Load**: Save playlists in M3U format with full metadata preservation
- **Playlist Operations**: List, delete, and manage multiple playlists
- **Track Reordering**: Up/down arrow buttons to move songs within playlists
- **Persistent Storage**: Playlists safely stored for future use

### 🎨 Theme Expansion
- **4 New Themes**: Terminal (retro green), Sunset (warm tones), Forest (green palette), Midnight (purple)
- **Music Directory Standardization**: Unified `/media/music/` directory structure
- **Symlink Support**: Seamless handling of symbolic links in music directory

### ⚡ Interactive Features  
- **Clickable Seeking**: Click progress bar to jump to any position in track
- **Safe Installer**: Preserves existing MPD config and database during setup

---

## Version 2.8.0 - Squeezebox/LMS Multi-Room Audio (January 21, 2026)

### �🔊 Logitech Media Server Integration
- **Squeezebox Support**: Stream Maestro audio to Squeezebox Radio and other LMS-compatible devices
- **LMS Configuration UI**: Easy setup in Admin Panel → System with IP address and port fields
- **Player Discovery**: Automatic detection of all Squeezebox players on your network
- **Multi-Room Control**: Select which players stream Maestro audio from Settings page
- **Volume Control**: Individual volume sliders for each Squeezebox player (0-100%)
- **Real-time Status**: See player connection status and control streaming with one click
- **Connection Testing**: Test LMS server connectivity before saving settings
- **Smart Enable/Disable**: Toggle LMS integration without losing configuration
- **User-Configurable**: Complete freedom to specify your own LMS server IP and port
- **Graceful Degradation**: System continues working if LMS server is unreachable

### 🎵 Technical Implementation
- **JSON-RPC Client**: Full LMS API client (lms_client.py) with player control methods
- **HTTP Stream Integration**: Automatically pushes MPD's HTTP stream (port 8000) to selected players
- **REST API**: New endpoints `/api/lms/players`, `/api/lms/sync`, `/api/lms/unsync`, `/api/lms/volume`, `/api/lms/status`
- **Settings Persistence**: LMS configuration stored in settings.json alongside other preferences
- **Error Handling**: Graceful fallbacks with timeout protection when LMS is unavailable or unconfigured
- **Independent Audio Paths**: Works alongside Raspberry Pi MPV streamers without interference

### 📚 Documentation & Setup
- **Admin Interface**: New "Squeezebox/LMS Integration" section in System Administration
- **Settings Page**: Dedicated player selection UI with checkbox controls and volume sliders
- **Status Indicators**: Visual feedback for player connectivity and streaming state
- **Setup Instructions**: Clear guidance linking to Admin Panel from Settings page

---

## Version 2.1.0 - HTTP Streaming UI & Critical Fixes (December 20, 2025)

### 🎧 HTTP Streaming Configuration
- **Admin UI for HTTP Streaming**: Configure MPD HTTP streaming without manual config editing
- **Simple Toggle**: Enable/disable HTTP streaming with one click
- **Advanced Settings**: Full control over port, encoder, bitrate, format, max clients, and bind address
- **Smart Defaults**: Pre-configured with optimal settings (port 8000, LAME encoder, 192kbps)
- **Auto-restart MPD**: Automatic service restart after configuration changes
- **Stream URL Display**: Shows connection URL for clients when streaming is enabled
- **Multi-room Setup**: Complete documentation for Raspberry Pi MPV clients

### 🔒 Critical Fixes
- **Database Backup/Restore**: Fixed missing sudo permissions for MPD database operations
- **Sudoers Configuration**: Added passwordless `cp` commands for backup/restore functionality
- **Update Script Enhancement**: Regenerate sudoers during updates for consistency
- **NFS Mount Recovery**: Documented solution for network share mount failures after reboot

### 🎨 UI/UX Improvements
- **Navigation Rebranding**: Changed "MPD Control" to "Maestro Control" across all admin pages
- **Navigation Consistency**: Removed new window behavior, direct navigation for better UX
- **OS Update Warnings**: Added safety notices with screen/tmux command examples

### 📚 Documentation
- **Ras-Pi-Client.md**: Complete guide for multi-room Raspberry Pi client setup
- **Admin UI Instructions**: Step-by-step streaming configuration via web interface
- **Alternative Methods**: Manual mpd.conf configuration documented as fallback

---

## Version 2.0.0 - Admin API Integration (December 14, 2025)

### 🎉 Major Release - Complete Music Server Solution

### ⚙️ New Admin API (Port 5004)
- **System Administration Dashboard**: Web-based system management interface
- **Library Management**: Configure music library folders and mount network shares
- **Network Mounts**: NFS and SMB/CIFS mount management with friendly names
- **Audio Configuration**: Detect and configure audio devices
- **System Monitoring**: CPU, memory, disk usage, and uptime tracking
- **System Updates**: One-click OS package updates with real-time output
- **Automatic fstab Reading**: Detects existing network mounts from /etc/fstab

### 🚀 Installation & Deployment
- **One-Command Installer**: Universal bash installer for Ubuntu/Debian/Arch
- **Automatic Service Setup**: Creates systemd services for web UI and admin API
- **Dependency Management**: Automatic installation of all required packages
- **Port Configuration**: Web UI on 5003, Admin API on 5004, MPD on 6600
- **No Docker Required**: Native Linux installation with systemd services

### 🔄 Navigation Improvements
- **Bidirectional Links**: Admin button in Web UI, MPD Control button in Admin
- **Smart Navigation**: Admin button navigates directly, MPD Control opens new tab
- **Consistent Branding**: Unified interface design across both applications

### 🧹 Code Cleanup
- **Removed Docker Support**: Streamlined for native Linux server deployment
- **Removed Windows Scripts**: Focused on Linux server environment
- **Removed Non-Functional Features**: Cleaned up mood auto-fill UI
- **Documentation Updates**: Comprehensive v2.0 documentation

### 🎨 User Interface
- **Mood Auto-Fill Removed**: Cleaned up non-functional feature from UI
- **Admin Integration**: Seamless navigation between Web UI and Admin API
- **Responsive Design**: Both interfaces optimized for desktop and mobile

### 🔧 Technical Changes
- **Default Port Change**: Web UI now defaults to 5003 (was 5000)
- **Enhanced fstab Parsing**: Generates friendly mount names from mount points
- **Service Management**: Proper systemd integration for both services
- **Environment Variables**: Configurable via .env or config.env

### 📦 Repository Changes
- **New Repository**: Maestro-Server (separate from Maestro-MPD-Control)
- **Git Tag**: v2.0.0 release tag created
- **GitHub Release**: Complete release with installer and documentation

---

## Version 1.0.0 - Docker Release (November 2025)

### ✨ Features
- **4 Complete Themes**: Dark, Light, High Contrast, Desert
- **Mobile Responsive**: Optimized interface for all screen sizes
- **Radio Stations**: Save and manage genre-based radio stations
- **Smart Auto-Fill**: Intelligent playlist management with Last.fm integration
- **Advanced Search**: Comprehensive music library search
- **Last.fm Integration**: Charts, scrobbling, and music discovery
- **Album Art Support**: Local and web-based album artwork
- **Real-time Updates**: Live playback status via WebSockets

### 🐳 Docker Support
- **Multi-Container Setup**: Separate MPD and web application containers
- **Flexible Deployment**: Support for both containerized and external MPD
- **Environment Configuration**: Complete environment variable support
- **Health Checks**: Built-in service monitoring
- **Data Persistence**: Preserves settings and cache across restarts
- **Security Hardening**: Non-root user execution

### 🎨 User Interface
- **Desert Theme**: New warm brown/tan theme with reddish accents
- **Mobile Footer**: Improved mobile layout with stacked controls
- **Navigation**: Consistent emoji-based navigation across all pages
- **Progress Bars**: Real-time track progress visualization
- **Settings Management**: Persistent theme and configuration storage

### 🔧 Technical Improvements
- **Memory Optimization**: Reduced MPD memory usage (3.2GB → 162MB)
- **Performance**: Optimized background monitoring and caching
- **Error Handling**: Improved error messages and fallback behavior
- **Configuration**: Environment-based configuration for Docker deployment
- **Security**: Removed admin features for public deployment

### 🎵 Music Features
- **Radio Station Mode**: Genre-based automatic playlist generation
- **Consume Mode**: Automatic track removal after playing
- **Shuffle Support**: Random playback with cross-page synchronization
- **Crossfade**: Smooth transitions between tracks
- **Volume Control**: Precise volume management with presets
- **Queue Management**: Advanced playlist manipulation

### 🌐 Integration
- **Last.fm Charts**: Personal music statistics and charts
- **Music Discovery**: Similar artist recommendations
- **External Links**: Wikipedia, AllMusic, MusicBrainz integration
- **API Support**: RESTful API endpoints for automation
- **WebSocket Events**: Real-time status updates

---

## Previous Versions

### Pre-1.0 Development
- Initial Flask application development
- MPD integration and control
- Basic theme system implementation
- Search functionality development
- Album art processing
- Last.fm API integration
- Auto-fill system creation
- Mobile responsiveness improvements

---

*For detailed technical information, see README.md*