# MPD Web Control - Enhanced Edition Deployment Guide

## Version: 20251116_123734_UI_FIXES_AND_BACKUP
Last updated: 2025-11-16

This version includes major radio station auto-fill enhancements, navigation standardization, and professional UI improvements.

## 🚀 Quick Installation (Any Linux System)

### Extract and Setup
```bash
# Extract the archive (use your latest backup filename)
# Generic pattern
tar -xzf mpd_web_control_backup_YYYYmmdd_HHMMSS*.tar.gz
# Example from today
# tar -xzf mpd_web_control_backup_20251116_123734_ui_fixes_20251116.tar.gz
cd mpd_web_control_combined_20251104_180921/

# Setup (creates virtual environment, installs dependencies)
./setup.sh
```

### Option 1: Run Manually (Testing)
```bash
source venv/bin/activate
python app.py
# Access at: http://localhost:5003
```

### Option 2: Install as System Service (Production - Recommended)
```bash
sudo ./install_service.sh
# Service starts automatically and survives reboots
```

## 🎵 New Features Overview

### 📻 Radio Station System
- **Save & Load**: Create custom radio stations with multiple genres
- **Auto-Fill Integration**: Radio stations preserve genre diversity during auto-fill
- **Smart Playback**: Instant station loading with automatic playlist generation
- **Status Display**: Rich information showing active station and genre count

### 🧭 Navigation Enhancements  
- **Consistent Navigation**: Emoji-based navigation across all pages
- **Current Page Indicators**: Clear "you are here" visual cues
- **Mobile Responsive**: Touch-friendly interface optimization
- **Professional UI**: Standardized styling and visual hierarchy

### 🎨 User Experience Improvements
- **Album Art Integration**: Thumbnail display in playlist view
- **Enhanced Auto-Fill**: Intelligent mode switching between normal and radio station operation
- **Real-Time Status**: Live updates for radio station mode and auto-fill information
- **Reliable Playback**: Eliminated timing issues with proper synchronization

## ⚙️ Configuration

Edit `config.env` with your settings:
```bash
# MPD Connection
MPD_HOST=localhost
MPD_PORT=6600
MUSIC_DIRECTORY=/path/to/your/music

# Web Interface  
APP_PORT=5003
APP_HOST=0.0.0.0

# Last.fm (optional)
LASTFM_API_KEY=your_api_key
LASTFM_SHARED_SECRET=your_secret
```

## 🔧 Service Management (if installed as service)

```bash
sudo systemctl status mpd-web-control     # Check status
sudo systemctl stop mpd-web-control       # Stop service  
sudo systemctl restart mpd-web-control    # Restart service
sudo systemctl disable mpd-web-control    # Disable auto-start
journalctl -u mpd-web-control -f          # View logs
```

## ✅ Major Enhancements in This Version

### 🎯 Radio Station Auto-Fill System
- **Intelligent Mode Switching**: Maintains station genre diversity vs single "now playing" genre
- **Persistent Genre Sets**: Radio stations preserve original genre configurations during auto-fill
- **Rich Status Display**: Shows active station name, genre count, and auto-fill status
- **Seamless Integration**: Works with existing auto-fill settings and preferences

### 🧭 Professional Navigation
- **Standardized Interface**: Consistent emoji-based navigation across all pages
- **Current Page Indicators**: Clear visual cues showing location in application  
- **Mobile Optimization**: Touch-friendly responsive design for all screen sizes
- **Visual Hierarchy**: Professional styling matching modern web applications

### 🎨 UI/UX Improvements  
- **Album Art Integration**: Thumbnail display in playlist view with local/Last.fm fallback
- **Enhanced Auto-Fill Display**: Rich information showing radio station mode and genre count
- **Reliable Playback**: Eliminated "failed to start playback" errors with proper timing
- **Button Consistency**: Logical playback control ordering (Previous→Play→Stop→Pause→Next)

### 🔧 Technical Enhancements
- **Timing Synchronization**: Backend + frontend delays for reliable MPD operations
- **POST Request Handling**: Proper AJAX response handling for all endpoints  
- **Mode Management**: Automatic radio station mode activation/deactivation
- **Error Handling**: Improved validation and user feedback throughout application

### 📱 Core Features (Previously Fixed)
- **Search Results**: No more "Method Not Allowed" errors
- **Add Buttons**: Proper POST forms instead of broken GET links  
- **User Experience**: Clean redirects instead of blank JSON pages
- **Service Integration**: Reliable systemd service with proper venv activation
- **Genre Selection**: Multi-select random music with 255+ genres available

## 🎮 Quick Start Guide

### 1. First Time Setup
```bash
# After installation, configure your settings
cp config.env.example config.env
nano config.env  # Edit with your MPD and music directory settings
```

### 2. Access the Interface
- **Desktop**: Navigate to `http://localhost:5003`
- **Remote Access**: Use your server IP: `http://your-server-ip:5003`
- **Mobile**: Fully responsive design works on all devices

### 3. Key Features to Try
1. **🏠 Dashboard**: View current playing status with album art
2. **📋 Playlist**: Manage current queue with thumbnail album art  
3. **➕ Add Music**: Use radio stations or manual track addition
4. **🔍 Search**: Find music across your entire library
5. **📻 Radio Stations**: Save genre combinations for instant playlist creation

### 4. Radio Station Workflow
```
1. Navigate to Add Music page (➕)
2. Select multiple genres from dropdown
3. Click "Save as Radio Station" 
4. Enter station name (e.g., "Metal Mix", "Chill Jazz")
5. Use "Load & Play" to instantly create playlists
6. Auto-fill maintains station's genre diversity
```

## 🛠️ Advanced Configuration

### Radio Station Management
Radio stations are stored in `radio_stations.json` and can be:
- **Exported**: Copy file to backup station configurations  
- **Imported**: Replace file to restore or share stations
- **Modified**: Edit JSON directly for bulk changes

### Auto-Fill Customization
- **Track Range**: Configure min/max tracks added (default: 3-7)
- **Queue Threshold**: Set minimum queue length trigger (default: 3)
- **Genre Filtering**: Enable/disable genre-based filtering
- **Radio Station Mode**: Automatically activated when radio stations are playing

### Performance Tuning
- **Large Libraries**: Auto-fill cooldown prevents excessive additions (30 second default)
- **Remote Access**: Adjust `APP_HOST=0.0.0.0` for network accessibility
- **Memory Usage**: Monitor with systemd journal: `journalctl -u mpd-web-control -f`

## �️ Troubleshooting

### Common Issues
- **MPD Connection**: Ensure MPD is running: `systemctl status mpd`
- **Firewall**: Open port 5003 if accessing remotely: `sudo ufw allow 5003`
- **Permissions**: Check music directory is readable by the app user
- **Service Issues**: Check logs with `journalctl -u mpd-web-control -f`

### Radio Station Issues
- **Station Not Loading**: Verify genres exist in your music library
- **Auto-Fill Not Working**: Check "Enable Auto-Fill" checkbox is checked
- **Playback Delays**: Normal behavior - 1.5 second delay ensures reliable playback
- **Genre Missing**: Station will skip unavailable genres automatically

### Performance Issues  
- **Slow Loading**: Large libraries may take time for initial genre enumeration
- **High Memory**: Monitor usage with `systemctl status mpd-web-control`
- **Auto-Fill Spam**: 30-second cooldown prevents excessive additions

### Mobile Access Issues
- **Touch Problems**: Clear browser cache for responsive design updates
- **Layout Issues**: Ensure latest version is deployed with navigation enhancements
- **Station Management**: Use desktop for complex radio station creation

## 📊 System Requirements

### Minimum Requirements
- **OS**: Linux with systemd (tested on Arch Linux)
- **Python**: 3.7+ with pip and venv support
- **MPD**: Running and accessible (typically on port 6600)
- **Memory**: 50-100MB RAM for normal operation
- **Storage**: 200MB for application + virtual environment

### Recommended Setup
- **CPU**: Multi-core for better auto-fill performance with large libraries
- **RAM**: 1GB+ available for comfortable operation
- **Network**: Stable connection for Last.fm album art and similar artist features  
- **Browser**: Modern browser with JavaScript enabled (Chrome, Firefox, Safari, Edge)

### Optional Enhancements
- **Last.fm API**: For album art fallback and similar artist suggestions
- **SSD Storage**: Faster music library scanning and auto-fill operations
- **Reverse Proxy**: nginx/Apache for HTTPS and domain hosting
- **Monitoring**: systemd journal integration for operational visibility

---

## 🚀 Production Deployment Notes

This enhanced version is production-ready with:
- ✅ Comprehensive error handling and user feedback
- ✅ Proper systemd service integration with automatic restarts
- ✅ Mobile-responsive design for multi-device access
- ✅ Advanced radio station functionality with auto-fill integration
- ✅ Professional UI consistency and navigation standardization

**Status**: Ready for deployment in home server or professional environments.

## 🔐 Backup & Retention

Before upgrades or major changes, create a backup:
```bash
./backup.sh
```
This produces `backups/mpd_web_control_backup_YYYYmmdd_HHMMSS.tar.gz` while excluding `venv/`, `__pycache__/`, and existing backups.

### Automatic Retention (Dual-Location)
Script keeps only the two newest archives per location (project `backups/` and `$HOME`). Override:
```bash
RETENTION_COUNT=4 ./backup.sh
```
Add descriptive label:
```bash
DESCRIPTION=post_upgrade ./backup.sh
```
Change secondary destination:
```bash
HOME_BACKUP_DIR=/mnt/backup ./backup.sh
```
Skip creating home copy:
```bash
SKIP_HOME_COPY=1 ./backup.sh
```

### Recommended Workflow
1. Run `./backup.sh` (confirm success)
2. Perform upgrade / modifications
3. Run `./backup.sh` again (post-change snapshot)
4. Off-site copy critical files (`config.env`, `radio_stations.json`) if needed

### Validate a Backup
```bash
tar -tzf backups/mpd_web_control_backup_YYYYmmdd_HHMMSS.tar.gz | head
```

### Restore
```bash
tar -xzf backups/mpd_web_control_backup_YYYYmmdd_HHMMSS.tar.gz
cd mpd_web_control_combined_*/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 🛡️ Disaster recovery on a fresh machine (from backup)

Follow these steps to rebuild everything on a new Linux host using a saved backup archive.

1) Install system prerequisites
- Python (with venv) and MPD must be installed. Example commands:

Debian/Ubuntu
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip mpd git curl
```

Arch/Manjaro
```bash
sudo pacman -Syu --noconfirm
sudo pacman -S --noconfirm python python-virtualenv python-pip mpd git curl
```

2) Copy the backup archive to the new host and extract
```bash
mkdir -p ~/restore && cd ~/restore
cp /path/to/mpd_web_control_backup_YYYYmmdd_HHMMSS*.tar.gz .
tar -xzf mpd_web_control_backup_YYYYmmdd_HHMMSS*.tar.gz
cd mpd_web_control_combined_*/
```

3) Create virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

4) Configure environment
- Start with example and edit values for your MPD and system:
```bash
cp -n config.env.example config.env
nano config.env
```
- If you have a `settings.json` and `radio_stations.json` in the backup, they are already restored in the project root (contains theme, Last.fm session key, station presets). Keep file perms secure:
```bash
chmod 600 settings.json 2>/dev/null || true
```

5) Test run (manual)
```bash
source venv/bin/activate
python app.py
# Open http://localhost:5003
```

6) Install as a system service (recommended)
```bash
sudo ./install_service.sh
sudo systemctl status mpd-web-control
```

7) Point the app to your music
- Ensure MPD is installed and configured on this host and that `MUSIC_DIRECTORY` in `config.env` matches MPD’s database.
- If moving MPD too, copy your `/etc/mpd.conf` and restart MPD:
```bash
sudo systemctl restart mpd
sudo systemctl status mpd
```

8) Optional: Verify Last.fm
- If you backed up `settings.json` with a valid Last.fm session key, Charts and scrobbling should work immediately. Otherwise, reconnect in Settings.

9) Smoke test
```bash
curl -s http://localhost:5003/api/version | jq .
# Navigate UI: Main, Add Music, Search, Playlist, Charts
```

Notes
- Backup excludes `venv/`, `__pycache__/`, and prior `backups/`, so venv is recreated.
- Archives include `config.env` (if present), `settings.json`, and other app data—treat archives as sensitive.
- MPD and system audio settings are outside this app; restore `/etc/mpd.conf` separately.

