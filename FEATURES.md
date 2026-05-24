# 📚 Maestro - Comprehensive Feature Guide

**Last Updated:** December 21, 2025 | **Version:** 2.2.0

This document provides detailed information about every feature in Maestro MPD Server.

---

## Table of Contents

1. [Web Player Interface](#web-player-interface)
2. [Library Management](#library-management)
3. [Admin Dashboard](#admin-dashboard)
4. [CD Ripping System](#cd-ripping-system)
5. [Last.fm Integration](#lastfm-integration)
6. [Theme System](#theme-system)
7. [Audio Configuration](#audio-configuration)
8. [System Management](#system-management)

---

## Web Player Interface

### Playback Controls

#### Standard Controls
- **Play/Pause/Stop** - Full transport control with visual feedback
- **Next/Previous Track** - Navigate through queue with keyboard shortcuts
- **Volume Control** - Smooth 0-100% adjustment with visual indicator
- **Progress Bar** - Clickable seek with time display (elapsed/total)
- **Shuffle Mode** - Random playback with visual indicator
- **Repeat Mode** - Off, repeat all, repeat single track

#### Advanced Playback
- **HTTP Streaming** - Listen directly in browser (MPD HTTP output)
- **Real-time Updates** - SocketIO connection for instant UI updates
- **Queue Position** - Click any track to start playback from that position
- **Volume Memory** - Remembers last volume setting across sessions

### Queue Management

#### Current Playlist
- **Dynamic Queue Display** - Shows all queued tracks with metadata
- **Track Information** - Artist, album, title, duration for each track
- **Clear Playlist** - One-click queue clearing
- **Add to Queue** - Multiple ways to add music:
  - Click album art → adds entire album
  - Click track → adds single track
  - Browse and add by artist, genre, or album

#### Smart Queue Features
- **Album Grouping** - Visually groups album tracks in queue
- **Disc Detection** - Properly handles multi-disc albums
- **Duration Display** - Shows individual track and total queue time
- **Position Indicator** - Highlights currently playing track

### Library Browsing

#### Browse by Albums
<!-- SCREENSHOT NEEDED: browse-albums.png -->
- **Grid View** - Clean album grid with cover art
- **Album Art Display** - High-quality album artwork when available
- **Quick Add** - Click album to add entire album to queue
- **Metadata Display** - Shows artist, album title, year
- **Recent Albums** - Dedicated page for newly added/ripped music
- **Multi-Disc Support** - Properly groups box sets and multi-disc albums

#### Browse by Artists
<!-- SCREENSHOT NEEDED: browse-artists.png -->
- **Alphabetical Sorting** - Clean A-Z artist list
- **Letter Jump Navigation** - Appears automatically when >50 artists
  - One-click jump to any letter
  - Visual highlight of current position
  - Mobile-optimized buttons
  - Smooth scrolling with centering
- **Artist Track Count** - Shows number of tracks per artist
- **Genre Filtering** - Filter artists by genre
- **Quick Navigation** - Click artist to see all albums

#### Browse by Genres
- **Genre List** - All genres in your library
- **Letter Jump Navigation** - Same as artists (>50 genres)
- **Artist Count** - Shows artists per genre
- **Quick Filtering** - Click genre to filter artists/albums

#### Search Functionality
- **Global Search** - Search across all metadata
- **Real-time Results** - Instant search as you type
- **Search Scope**:
  - Artist names
  - Album titles
  - Track titles
- **Result Display** - Shows all matches with metadata
- **Quick Add** - Add search results directly to queue

### Playback Charts
<!-- SCREENSHOT NEEDED: charts.png -->
- **Listening Statistics** - Track your music listening habits
- **Top Artists** - Most played artists
- **Top Albums** - Most played albums
- **Top Tracks** - Most played songs
- **Time-based Stats** - Daily, weekly, monthly views
- **Visual Graphs** - Bar charts and pie charts
- **Export Data** - Download stats as CSV/JSON

---

## Library Management

### Music Directory Structure

Maestro expects a standard hierarchical structure:
```
/media/music/
├── Artist Name/
│   ├── Album Name/
│   │   ├── 01 - Track Name.flac
│   │   ├── 02 - Track Name.flac
│   │   └── cover.jpg
│   └── Another Album/
└── ripped/          # Auto-ripped CDs appear here
    └── [Same structure]
```

### Network Share Management
<!-- SCREENSHOT NEEDED: library-management.png -->

#### NFS Shares
1. Navigate to Admin → Library Management
2. Click "Add NFS Share"
3. Enter details:
   - **Server IP/Hostname**
   - **Export Path** (e.g., `/export/music`)
   - **Mount Point** (e.g., `/media/music/nas`)
4. Click "Mount"
5. Click "Update MPD Library"

**Supported Options:**
- `ro` - Read-only mount (recommended)
- `rw` - Read-write mount
- `soft` - Soft mount (fails gracefully)
- `hard` - Hard mount (waits indefinitely)
- `intr` - Interruptible mount
- `timeo=600` - Timeout settings

#### SMB/CIFS Shares
1. Navigate to Admin → Library Management
2. Click "Add SMB Share"
3. Enter details:
   - **Server IP/Hostname**
   - **Share Name**
   - **Username** (optional)
   - **Password** (optional)
   - **Mount Point**
4. Click "Mount"
5. Click "Update MPD Library"

**Credentials Storage:**
- Stored in `/etc/maestro/smbcreds` (secure permissions)
- Never exposed in web interface
- Encrypted at rest (optional with LUKS)

### Library Updates

#### Automatic Updates
- **CD Rip Completion** - Triggers after every CD rip
- **Mount Operations** - Updates after mounting new share
- **Scheduled Updates** - Optional cron job (recommended daily)

#### Manual Updates
1. Main UI → Footer → "Update MPD Database"
2. Admin → Library Management → "Update Library"
3. Command line: `mpc update`

#### Update Status
- **Progress Monitoring** - Real-time update progress
- **Toast Notifications** - "Database update started" and "Complete"
- **Non-blocking** - UI remains usable during update
- **Smart Scanning** - MPD only scans changed files

### Recent Albums Feature
<!-- SCREENSHOT NEEDED: recent-albums.png -->

Automatically tracks and displays recently added albums:

**Configuration** (settings.json):
```json
{
  "recent_albums_dir": "ripped"
}
```

**How it Works:**
1. Scans specified directory for albums
2. Sorts by modification time (newest first)
3. Displays 50 most recent albums
4. Shows album art, artist, album name
5. Click to add to queue

**Best Practices:**
- Point to your "incoming" or "ripped" directory
- Use for new downloads or CD rips
- Keep separate from main library for easy browsing
- Updates automatically when directory changes

---

## Admin Dashboard

### System Monitoring
<!-- SCREENSHOT NEEDED: admin-dashboard.png -->

#### Real-time Statistics
**Update Frequency:** Every 2 seconds

**Metrics Displayed:**
- **CPU Usage** - Overall percentage and per-core breakdown
- **Memory Usage** - Used/total with percentage
- **Disk Usage** - All mount points with used/free/percentage
- **Network Traffic** - Bytes sent/received with rate calculations
- **Process Count** - Running processes
- **Uptime** - System uptime formatted

**Visual Elements:**
- Progress bars for CPU/RAM/Disk
- Color coding: Green (<70%), Yellow (70-90%), Red (>90%)
- Live updating graphs
- Automatic refresh

#### System Information
- **Hostname** - System name
- **OS Version** - Distribution and version
- **Kernel Version** - Linux kernel version
- **Architecture** - x86_64, aarch64, etc.
- **IP Addresses** - All network interfaces
- **Python Version** - Python interpreter version
- **MPD Version** - Music Player Daemon version

### Service Management

#### Service Status Display
- **MPD Service** - Running/stopped with restart button
- **Web UI Service** - maestro-web.service status
- **Admin API Service** - maestro-admin.service status

#### Service Controls
- **Restart MPD** - Graceful MPD restart
- **Restart Web UI** - Reloads web interface
- **Restart Admin** - Reloads admin interface
- **Restart All** - Complete service restart
- **Stop Services** - Graceful shutdown

#### Service Logs
<!-- SCREENSHOT NEEDED: system-logs.png -->
- **View Logs** - Last 100 lines from systemd journal
- **Filter by Service** - MPD, Web, Admin, or System logs
- **Real-time Tail** - Auto-updating log view
- **Error Highlighting** - Red highlighting for errors
- **Search Logs** - Filter by keyword

### System Administration

#### OS Package Updates
1. Click "Check for Updates"
2. Review available updates
3. Click "Install Updates"
4. Watch real-time progress
5. Restart services if needed

**Features:**
- Real-time progress display
- Package names and versions shown
- Automatic cleanup after install
- Rollback support (dpkg/pacman)

#### System Reboot
1. Click "Reboot System"
2. Confirm action
3. Optional countdown (10 seconds)
4. Services gracefully stop
5. System reboots

**Safety Features:**
- Confirmation required
- Saves MPD state
- Graceful service shutdown
- Countdown warning

---

## CD Ripping System

### Automatic CD Detection
<!-- SCREENSHOT NEEDED: cd-ripper.png -->

**How it Works:**
1. **udev Rule** (`/etc/udev/rules.d/99-maestro-cd.rules`)
   - Detects CD insertion
   - Identifies disc via `cd-discid`
   - Triggers rip script

2. **Auto-Rip Script** (`~/maestro/scripts/cd-inserted.sh`)
   - Queries FreeDB for metadata
   - Configures abcde settings
   - Starts ripping process
   - Updates MPD library

3. **Status Monitoring**
   - Admin → CD Ripper shows progress
   - Log file: `~/maestro/logs/cd-rip.log`
   - Toast notification on completion

### CD Ripper Configuration

#### Audio Format Settings
**Supported Formats:**
- **FLAC** (recommended) - Lossless, best quality
- **MP3** - Lossy, smaller files (V0, 320kbps, 256kbps, 192kbps)
- **OGG Vorbis** - Lossy, open source (q8, q9, q10)
- **AAC/M4A** - Lossy, Apple compatibility
- **WAV** - Uncompressed, largest files

**FLAC Settings:**
```json
{
  "format": "flac",
  "flac_level": 8,
  "flac_verify": true
}
```

**MP3 Settings:**
```json
{
  "format": "mp3",
  "mp3_quality": "V0",
  "mp3_encoder": "lame"
}
```

#### Metadata Configuration
- **FreeDB** - Default, works offline
- **MusicBrainz** - More accurate, requires internet
- **CDDB** - Alternative database
- **Manual Entry** - Override metadata

**Metadata Fields:**
- Artist name
- Album title
- Track titles
- Album year
- Genre
- Album art (embedded)

#### Output Settings
**Directory Structure:**
```
/media/music/ripped/
└── $ARTIST/
    └── $ALBUM/
        ├── 01 - $TRACK.flac
        ├── 02 - $TRACK.flac
        └── cover.jpg
```

**Naming Options:**
- **Track Naming**: `$TRACKNUM - $TITLE`
- **Disc Naming**: `$DISCNUM-$TRACKNUM - $TITLE`
- **Compilation**: `Various Artists/` folder

#### Behavior Settings
- **Eject After Rip** - Auto-eject disc when complete
- **Update MPD** - Auto-update library after rip
- **Show Toast** - Desktop notification on completion
- **Auto-Delete Failed** - Remove incomplete rips

### Multi-Disc Handling

For box sets and multi-disc albums:
- **Disc Detection** - Automatically identifies disc number
- **Unified Album** - All discs in same album folder
- **Track Numbering** - `1-01`, `2-01`, etc.
- **Metadata Preservation** - Disc number in tags

### Manual CD Ripping

If auto-rip doesn't work:
```bash
# Insert CD
cd ~/maestro/scripts
./cd-inserted.sh /dev/sr0

# Or use abcde directly
abcde -c ~/.abcde.conf
```

---

## Last.fm Integration

### Setup Process
<!-- SCREENSHOT NEEDED: settings-lastfm.png -->

**Step-by-Step:**
1. Get API credentials from [Last.fm API](https://www.last.fm/api/account/create)
2. Open Maestro Settings (`http://YOUR_IP:5003/settings`)
3. Enter **API Key** and **Shared Secret**
4. Click **① Test Last.fm** - Validates credentials
5. Click **② Connect Last.fm** - Opens Last.fm authorization
6. Authorize Maestro on Last.fm website
7. Click **③ Finalize Last.fm** - Completes setup
8. Save Settings

**Configuration:**
```json
{
  "lastfm_api_key": "your_api_key",
  "lastfm_api_secret": "your_secret",
  "lastfm_session_key": "generated_after_auth",
  "lastfm_username": "your_username",
  "enable_scrobbling": true,
  "show_scrobble_toasts": true
}
```

### Scrobbling Behavior

#### "Now Playing" Updates
- **Triggers:** When track starts playing
- **Data Sent:** Artist, Track, Album, Duration
- **Timing:** Within 2 seconds of playback start
- **Retry:** Up to 3 attempts on failure

#### Scrobble Submission
- **Triggers:**
  - After 50% of track played, OR
  - After 4 minutes, whichever comes first
- **Requirements:**
  - Track must have artist and title
  - Duration must be >30 seconds
  - Not in shuffle mode (configurable)
- **Data Sent:**
  - Artist, Track, Album
  - Timestamp
  - Album artist (if different)
  - Duration

### Visual Feedback

#### Toast Notifications
**"Now Playing" Toast:**
```
🎵 Now Playing on Last.fm
Artist - Track Name
Album Name
```

**Scrobble Success Toast:**
```
✓ Scrobbled to Last.fm
Artist - Track Name
```

**Error Toast:**
```
✗ Last.fm Error
Failed to scrobble: [error message]
```

#### Settings Control
- **Enable Scrobbling** - Master on/off switch
- **Show Toasts** - Enable/disable notifications
- **Auto-hide** - Toasts disappear after 5 seconds
- **Manual Dismiss** - Click to close toast

---

## Theme System

### Available Themes
<!-- SCREENSHOT NEEDED: themes-showcase.png -->

Maestro includes 8 professionally designed themes:

#### 1. Dark (Default)
- **Primary:** #1a1a1a (charcoal black)
- **Accent:** #1db954 (Spotify green)
- **Best For:** Night listening, reduced eye strain
- **Text:** High contrast white on dark

#### 2. Light
- **Primary:** #ffffff (pure white)
- **Accent:** #1db954 (Spotify green)
- **Best For:** Bright rooms, daytime use
- **Text:** Dark gray on white

#### 3. High Contrast
- **Primary:** #000000 (pure black)
- **Accent:** #00ff00 (bright green)
- **Best For:** Accessibility, visual impairment
- **Text:** Pure white on pure black

#### 4. Desert
- **Primary:** #d4a574 (sandy beige)
- **Accent:** #8b4513 (saddle brown)
- **Best For:** Warm, earthy aesthetic
- **Text:** Dark brown on beige

#### 5. Terminal
- **Primary:** #0c0c0c (terminal black)
- **Accent:** #00ff00 (matrix green)
- **Best For:** Retro, hacker aesthetic
- **Text:** Bright green on black

#### 6. Sunset
- **Primary:** #ff6b35 (sunset orange)
- **Accent:** #f7931e (warm gold)
- **Best For:** Warm, cozy atmosphere
- **Text:** White on orange

#### 7. Forest
- **Primary:** #2d5016 (forest green)
- **Accent:** #8bc34a (lime green)
- **Best For:** Natural, calming theme
- **Text:** Light green on dark green

#### 8. Midnight
- **Primary:** #191970 (midnight blue)
- **Accent:** #4169e1 (royal blue)
- **Best For:** Cool, sophisticated look
- **Text:** White on dark blue

### Theme Application

**Where Themes Apply:**
- ✅ Main player interface
- ✅ All browse pages (albums, artists, genres)
- ✅ Search results
- ✅ Settings page
- ✅ Queue display
- ✅ Footer and navigation
- ✅ Buttons and controls
- ✅ Progress bars and sliders
- ✅ Toast notifications
- ✅ Letter navigation

**Theme Persistence:**
- Saved in browser localStorage
- Persists across sessions
- Syncs across tabs (same domain)
- No server-side storage needed

### CSS Variables

Themes use CSS custom properties:
```css
--primary-color: #1a1a1a;
--accent-color: #1db954;
--text-color: #ffffff;
--secondary-text: #b3b3b3;
--border-color: #333333;
```

**Custom Theme Creation:**
1. Edit `static/manifest.json`
2. Add theme object:
```json
{
  "name": "My Theme",
  "primary": "#hexcode",
  "accent": "#hexcode"
}
```
3. Restart web service
4. Theme appears in settings

---

## Audio Configuration

### Audio Output Selection
<!-- SCREENSHOT NEEDED: audio-tweaks.png -->

#### Scan Audio Devices
1. Admin → Audio Tweaks
2. Click "Scan Audio Devices"
3. View all ALSA devices:
   - USB DACs
   - Internal sound cards
   - HDMI outputs
   - Bluetooth devices (if configured)

#### Configure Output
```
audio_output {
    type "alsa"
    name "My DAC"
    device "hw:2,0"
    mixer_type "hardware"
    mixer_device "hw:2"
    mixer_control "PCM"
}
```

**Parameters:**
- **type** - alsa, pulse, pipewire, httpd
- **name** - Display name
- **device** - Hardware address (hw:X,Y)
- **mixer_type** - hardware, software, none
- **mixer_control** - Volume control name

### Bit-Perfect Playback

**Requirements:**
- USB DAC with native DSD support
- ALSA configuration
- MPD compiled with DSD support

**Configuration:**
```
audio_output {
    type "alsa"
    name "USB DAC"
    device "hw:2,0"
    dsd_usb "yes"
    format "dsd64:2"
}
```

**DSD Formats:**
- **DSD64** - 2.8 MHz (SACD quality)
- **DSD128** - 5.6 MHz
- **DSD256** - 11.2 MHz
- **DSD512** - 22.4 MHz (requires high-end DAC)

### Buffer Settings

**Default:**
```
audio_buffer_size "4096"
buffer_before_play "20%"
```

**Optimization Guide:**
- **Local files**: 2048-4096 KB
- **Network shares**: 8192-16384 KB
- **Streaming**: 16384+ KB
- **DSD playback**: 32768 KB

**Buffer Before Play:**
- **Local**: 10-20%
- **Network**: 50-80%
- **Unreliable network**: 90%

### Resampling

**Disable for bit-perfect:**
```
audio_output_format "*:*:*"
resampler "soxr very high"
```

**Enable for compatibility:**
```
audio_output_format "44100:16:2"
resampler "soxr very high"
```

**Resampler Quality:**
- **soxr very high** - Best quality, high CPU
- **soxr high** - Good quality, medium CPU
- **soxr medium** - Balanced
- **libsamplerate** - Alternative resampler

### System Audio Optimizations

#### CPU Governor
```bash
# Performance mode for best audio
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

**Via Admin:**
1. Audio Tweaks → System Optimizations
2. Select "Performance" governor
3. Apply changes

#### Swappiness
```bash
# Reduce swapping for better real-time performance
echo 10 | sudo tee /proc/sys/vm/swappiness
```

**Via Admin:**
1. Audio Tweaks → System Optimizations
2. Set swappiness to 10-20
3. Apply changes

#### Real-time Priority
```
# In /etc/mpd.conf
audio_output {
    priority "high"
}
```

---

## System Management

### Service Management

#### SystemD Services

**maestro-web.service:**
```ini
[Unit]
Description=Maestro Web UI
After=network.target mpd.service
Requires=mpd.service

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/maestro/web
Environment="PATH=/home/youruser/maestro/web/venv/bin"
ExecStart=/home/youruser/maestro/web/venv/bin/python3 app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

**maestro-admin.service:**
```ini
[Unit]
Description=Maestro Admin API
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/maestro/admin
Environment="PATH=/home/youruser/maestro/admin/venv/bin"
ExecStart=/home/youruser/maestro/admin/venv/bin/python3 admin_api.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

#### MPD Configuration Override

**NFS Wait Configuration:**
`/etc/systemd/system/mpd.service.d/nfs-wait.conf`
```ini
[Unit]
After=network-online.target remote-fs.target
Wants=network-online.target
Requires=remote-fs.target

[Service]
Restart=on-failure
RestartSec=10
```

**Purpose:**
- Prevents MPD starting before NFS mounts
- Avoids database loss on network shares
- Auto-restarts on failure
- Waits 10 seconds between restart attempts

### Log Management

#### Application Logs
- **Web UI**: `~/maestro/web/logs/maestro.log`
- **Admin API**: `~/maestro/admin/logs/admin.log`
- **CD Ripping**: `~/maestro/logs/cd-rip.log`

#### SystemD Logs
```bash
# View web UI logs
journalctl -u maestro-web -n 100 -f

# View admin logs
journalctl -u maestro-admin -n 100 -f

# View MPD logs
journalctl -u mpd -n 100 -f

# View all Maestro logs
journalctl -u maestro-* -n 100 -f
```

#### Log Rotation
Automatically configured via `/etc/logrotate.d/maestro`:
```
/home/*/maestro/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 0644 user user
}
```

### Backup & Restore

#### MPD Database Backup
```bash
# Manual backup
sudo cp /var/lib/mpd/database /var/lib/mpd/database.backup.$(date +%Y%m%d)

# Via Admin API
curl -X POST http://localhost:5004/api/backup/mpd
```

**Automatic Backups:**
- Before library updates
- After CD rips
- Daily via cron (optional)

#### Settings Backup
```bash
# Backup settings
cp ~/maestro/settings.json ~/maestro/settings.json.backup

# Via update script
./update-maestro.sh  # Automatically backs up
```

#### Full System Backup
```bash
# Backup Maestro installation
tar -czf maestro-backup-$(date +%Y%m%d).tar.gz \
  ~/maestro/ \
  /etc/systemd/system/maestro-* \
  /etc/sudoers.d/maestro \
  /etc/udev/rules.d/99-maestro-cd.rules
```

### Performance Tuning

#### Network Share Optimization
```bash
# NFS mount options
mount -t nfs -o ro,soft,intr,timeo=600,retrans=2,rsize=32768,wsize=32768 \
  server:/export /media/music
```

**Recommended Options:**
- `ro` - Read-only (prevents accidental writes)
- `soft` - Fails gracefully on timeout
- `intr` - Interruptible on hang
- `timeo=600` - 60 second timeout
- `rsize/wsize=32768` - 32KB read/write buffer

#### MPD Performance
```
# In /etc/mpd.conf
max_connections "20"
connection_timeout "60"
max_playlist_length "32768"
max_command_list_size "32768"
max_output_buffer_size "32768"
```

#### Web UI Performance
- **Gzip Compression** - Enabled by default
- **Static Caching** - Browser caches CSS/JS
- **SocketIO** - Real-time updates without polling
- **Lazy Loading** - Images load on scroll

---

## Advanced Features

### Multi-Room Audio

MPD's network architecture allows:
- Multiple clients to same MPD server
- Zone control via multiple MPD instances
- Synchronized playback with snapcast

**Example Setup:**
```
Living Room: MPD on port 6600
Bedroom: MPD on port 6601
Kitchen: MPD on port 6602
```

Each zone has separate Maestro instance pointing to different MPD.

### Automation Integration

#### Home Assistant
```yaml
media_player:
  - platform: mpd
    host: YOUR_IP
    port: 6600
```

#### REST API Automation
```bash
# Add album to queue
curl -X POST "http://YOUR_IP:5003/api/add/album/Artist/Album"

# Start playback
curl -X POST "http://YOUR_IP:5003/api/play"

# Set volume
curl -X POST "http://YOUR_IP:5003/api/volume/75"
```

### Custom Scripts

#### Auto-DJ Mode
Create `~/maestro/scripts/auto-dj.sh`:
```bash
#!/bin/bash
# Continuous playback with smart queue management

while true; do
    # Check queue length
    QUEUE_LENGTH=$(mpc playlist | wc -l)
    
    # Add random album if queue low
    if [ $QUEUE_LENGTH -lt 5 ]; then
        RANDOM_ALBUM=$(mpc list album | shuf -n1)
        mpc findadd album "$RANDOM_ALBUM"
    fi
    
    sleep 60
done
```

---

## Troubleshooting Guide

### Common Issues

#### Issue: Album art not displaying
**Causes:**
- Missing cover.jpg in album folder
- Permissions issue
- Incorrect MPD configuration

**Solutions:**
1. Check file permissions: `ls -la /path/to/album/`
2. Ensure MPD can read files: `sudo chown -R mpd:audio /media/music`
3. Update library: `mpc update`
4. Clear MPD cache: `sudo rm /var/lib/mpd/albumart/*`

#### Issue: Scrobbles not working
**Causes:**
- Invalid Last.fm session
- Network connectivity
- Track metadata missing

**Solutions:**
1. Re-authorize Last.fm (Settings → Finalize Last.fm)
2. Check logs: `~/maestro/logs/maestro.log`
3. Verify metadata: `mpc current -f "%artist% - %title%"`
4. Test API: `curl https://ws.audioscrobbler.com/2.0/`

#### Issue: CD not auto-ripping
**Causes:**
- udev rule not loaded
- CD-ROM permissions
- abcde not configured

**Solutions:**
1. Reload udev: `sudo udevadm control --reload-rules`
2. Check permissions: `ls -la /dev/sr0`
3. Test manually: `~/maestro/scripts/cd-inserted.sh /dev/sr0`
4. Check logs: `cat ~/maestro/logs/cd-rip.log`

---

## Performance Benchmarks

### System Resource Usage

**Typical Usage (Raspberry Pi 4, 4GB):**
- **Idle**: 50MB RAM, 1% CPU
- **Playback**: 75MB RAM, 3-5% CPU
- **Library Scan**: 150MB RAM, 20-30% CPU
- **CD Ripping**: 200MB RAM, 40-60% CPU

**Large Libraries:**
- **10,000 tracks**: 100MB RAM, instant search
- **50,000 tracks**: 200MB RAM, <1s search
- **100,000 tracks**: 300MB RAM, <2s search

### Network Performance

**Local Playback:**
- FLAC: 1-2 Mbps
- MP3 320kbps: ~320 Kbps
- WAV: 10-15 Mbps

**NFS Shares:**
- Buffering: 5-10 seconds initial
- Playback: Seamless after buffer
- Track changes: <1 second

---

## API Reference

See **[Admin README](admin/README.md)** for complete API documentation.

### Quick Reference

#### Player Control
```bash
# Play
POST /api/play

# Pause
POST /api/pause

# Next track
POST /api/next

# Set volume
POST /api/volume/{0-100}
```

#### Library
```bash
# Browse albums
GET /api/browse/albums

# Browse artists
GET /api/browse/artists?genre=Rock

# Search
GET /api/search?q=query
```

#### Queue
```bash
# Add album
POST /api/add/album/{artist}/{album}

# Clear queue
POST /api/clear
```

---

## Frequently Asked Questions

### General

**Q: Does Maestro work with Spotify/Tidal/streaming services?**
A: No, Maestro is designed for local music collections. It's perfect for CDs, downloads, and local files.

**Q: Can I access Maestro remotely over the internet?**
A: Yes, but you'll need to set up port forwarding or a VPN. We recommend using a reverse proxy with authentication for security.

**Q: Does it work on Windows/macOS?**
A: Maestro is designed for Linux. It may work with WSL on Windows, but is untested. macOS is not supported.

### Technical

**Q: What's the maximum library size?**
A: MPD handles 100,000+ tracks easily. Maestro has been tested with 50,000 tracks without issues.

**Q: Can I use multiple audio outputs simultaneously?**
A: Yes! Configure multiple `audio_output` sections in `/etc/mpd.conf`.

**Q: Does it support gapless playback?**
A: Yes, MPD supports gapless playback natively for FLAC, MP3, and most formats.

### CD Ripping

**Q: What CD formats are supported?**
A: Standard audio CDs only. Data CDs, DVDs, and Blu-rays are not supported.

**Q: Can I rip to multiple formats?**
A: Yes, configure multiple output formats in CD Ripper settings.

**Q: What about copy-protected CDs?**
A: Some copy-protected CDs may not rip correctly. Try different CD drives or manual ripping.

---

**Need more help?** See [README.md](README.md) or open an [issue on GitHub](https://github.com/coacharnold1/Maestro-Server/issues).
