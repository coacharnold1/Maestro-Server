# 🪟 Windows Native MPD Setup Guide

This guide explains how to set up **native Windows MPD** with the Maestro web interface for **true Windows system audio output**.

## 📋 Table of Contents
- [Why Native MPD?](#why-native-mpd)
- [Quick Setup (Automated)](#quick-setup-automated)
- [Manual Setup](#manual-setup)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Why Native MPD?

### Containerized vs Native MPD on Windows

| Feature | Containerized MPD | Native Windows MPD |
|---------|-------------------|-------------------|
| **Audio Output** | HTTP stream only (port 8001) | ✅ Direct Windows audio (WASAPI) |
| **Quality** | Browser/VLC playback | ✅ Native system audio |
| **Setup** | Simple, one command | Requires MPD installation |
| **Best For** | Quick testing | Daily use, best quality |

**Recommendation:** Use **native Windows MPD** for the best experience.

---

## 🚀 Quick Setup (Automated)

### Using the Setup Script

Run the automated PowerShell setup script:

```powershell
# Run in PowerShell (from project directory)
.\setup-windows.ps1
```

The script will:
1. ✅ Check for Docker Desktop
2. ✅ Install Chocolatey (if needed)
3. ✅ Install MPD for Windows
4. ✅ Configure MPD with WASAPI audio
5. ✅ Create Windows service
6. ✅ Generate `.env` configuration
7. ✅ Start Docker web interface
8. ✅ Validate deployment

**Choose Option 1** when prompted for native MPD setup.

---

## 🔧 Manual Setup

If you prefer manual installation or the script fails:

### Step 1: Install MPD for Windows

#### Option A: Chocolatey (Recommended)
```powershell
# Install Chocolatey first (if not installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install MPD
choco install mpd -y
```

#### Option B: Manual Download
1. Visit https://www.musicpd.org/download.html
2. Download **Windows (x64)** build
3. Extract to `C:\Program Files\mpd\`
4. Add to PATH: `C:\Program Files\mpd\bin`

### Step 2: Configure MPD

Create configuration directory:
```powershell
New-Item -ItemType Directory -Path "$env:APPDATA\mpd" -Force
New-Item -ItemType Directory -Path "$env:APPDATA\mpd\data" -Force
New-Item -ItemType Directory -Path "$env:APPDATA\mpd\playlists" -Force
New-Item -ItemType Directory -Path "$env:APPDATA\mpd\logs" -Force
```

Create `mpd.conf` at `%APPDATA%\mpd\mpd.conf`:

```ini
# MPD Configuration for Windows
music_directory     "C:/Users/YourUsername/Music"
db_file             "C:/Users/YourUsername/AppData/Roaming/mpd/data/mpd.db"
state_file          "C:/Users/YourUsername/AppData/Roaming/mpd/data/mpdstate"
playlist_directory  "C:/Users/YourUsername/AppData/Roaming/mpd/playlists"
log_file            "C:/Users/YourUsername/AppData/Roaming/mpd/logs/mpd.log"

bind_to_address     "127.0.0.1"
port                "6600"

# Windows Audio (WASAPI) - Primary
audio_output {
    type        "wasapi"
    name        "Windows Audio"
    enabled     "yes"
}

# HTTP Stream (Optional - for browser playback)
audio_output {
    type        "httpd"
    name        "HTTP Stream"
    encoder     "lame"
    port        "8001"
    bitrate     "320"
    format      "44100:16:2"
    always_on   "yes"
    enabled     "yes"
}

auto_update             "yes"
filesystem_charset      "UTF-8"
```

**⚠️ Important:** Replace `YourUsername` with your actual Windows username and use **forward slashes** for paths.

### Step 3: Start MPD

#### Option A: Manual Start
```powershell
mpd --no-daemon "$env:APPDATA\mpd\mpd.conf"
```

#### Option B: Windows Service (Recommended)

Install as service using NSSM:
```powershell
# Install NSSM
choco install nssm -y

# Install MPD service
nssm install MPD "C:\Program Files\mpd\mpd.exe" --no-daemon "$env:APPDATA\mpd\mpd.conf"
nssm set MPD DisplayName "Music Player Daemon"
nssm set MPD Start SERVICE_AUTO_START

# Start service
Start-Service MPD
```

Or use Windows Task Scheduler for auto-start without NSSM.

### Step 4: Configure Docker Environment

Create `.env` file in project root:

```bash
# Music directory (forward slashes!)
MUSIC_DIRECTORY=C:/Users/YourUsername/Music

# Connect to native Windows MPD
MPD_HOST=host.docker.internal
MPD_PORT=6600
MPD_TIMEOUT=10

# Web interface
WEB_PORT=5003
DEFAULT_THEME=dark

# Optional: Last.fm integration
LASTFM_API_KEY=
LASTFM_SHARED_SECRET=

# Settings
AUTO_FILL_ENABLED=true
RECENT_MUSIC_DIRS=
SECRET_KEY=maestro-windows-$(Get-Random)
```

### Step 5: Start Docker Web Interface

```powershell
# Use the native-mpd docker-compose file
docker-compose -f docker-compose.native-mpd.yml up -d --build
```

### Step 6: Verify Setup

```powershell
# Check MPD is running
Get-Service MPD  # If installed as service
# or
Get-Process mpd  # If running manually

# Test MPD connection
Test-NetConnection -ComputerName localhost -Port 6600

# Check Docker container
docker ps

# Test web interface
Start-Process "http://localhost:5003"
```

---

## ⚙️ Configuration

### Audio Output Options

MPD for Windows supports multiple audio outputs:

#### WASAPI (Recommended - Windows 10/11)
```ini
audio_output {
    type        "wasapi"
    name        "Windows Audio"
    device      "default"  # or specific device ID
    enabled     "yes"
}
```

#### DirectSound (Legacy)
```ini
audio_output {
    type        "winmm"
    name        "DirectSound"
    device      "default"
    enabled     "yes"
}
```

#### HTTP Stream (Browser/Network)
```ini
audio_output {
    type        "httpd"
    name        "HTTP Stream"
    encoder     "lame"
    port        "8001"
    bitrate     "320"
    enabled     "yes"
}
```

You can have **multiple outputs enabled** simultaneously!

### Music Library Paths

MPD accepts several path formats on Windows:

✅ **Supported:**
- `C:/Users/username/Music` (forward slashes)
- `C:\\Users\\username\\Music` (escaped backslashes)
- `//server/share/music` (UNC paths)

❌ **Not Supported:**
- `C:\Users\username\Music` (single backslashes)

### Network Shares

To use network music libraries:

```ini
# UNC path
music_directory "//nas/music"

# Mapped drive (ensure MPD service has access)
music_directory "Z:/music"
```

**Service Note:** If running as service, ensure the service account has network access.

---

## 🐛 Troubleshooting

### MPD Won't Start

**Check configuration:**
```powershell
mpd --no-daemon --verbose "$env:APPDATA\mpd\mpd.conf"
```

**Common issues:**
- Invalid paths (use forward slashes)
- Missing directories (create data/playlists/logs folders)
- Port 6600 already in use
- Music directory not accessible

### No Audio Output

**Test MPD status:**
```powershell
# Connect with mpc (install via chocolatey)
choco install mpc -y
mpc status
mpc outputs
```

**Check outputs:**
```powershell
mpc enable 1  # Enable output #1
mpc play
```

**WASAPI issues:**
- Ensure default playback device is set in Windows
- Try `device "default"` in mpd.conf
- Check Windows audio services are running

### Docker Can't Connect to MPD

**Verify host.docker.internal:**
```powershell
# From inside container
docker exec mpd-web-control ping -c 3 host.docker.internal
```

**Firewall:**
```powershell
# Allow MPD through Windows Firewall
New-NetFirewallRule -DisplayName "MPD Server" -Direction Inbound -Protocol TCP -LocalPort 6600 -Action Allow
```

### Service Won't Start

**Check service logs:**
```powershell
Get-EventLog -LogName Application -Source MPD -Newest 10
```

**Restart service:**
```powershell
Restart-Service MPD
Get-Service MPD
```

### Database Not Updating

**Manual update:**
```powershell
mpc update
# Wait a few seconds
mpc stats
```

**Auto-update settings:**
```ini
auto_update         "yes"
auto_update_depth   "3"
```

### Permission Issues

**Music directory access:**
- Ensure MPD service user has read access
- Check folder permissions
- Try running MPD as your user account (via Task Scheduler)

---

## 📊 Performance Tips

### Faster Database Updates

Limit scan depth for large libraries:
```ini
auto_update_depth   "3"  # Only scan 3 levels deep
```

Use `RECENT_MUSIC_DIRS` in `.env` for faster recent album scanning.

### Memory Usage

```ini
max_output_buffer_size  "8192"   # Larger buffer = smoother playback
max_playlist_length     "16384"  # Increase for huge playlists
```

### Network Performance

```ini
max_connections         "10"
connection_timeout      "60"
bind_to_address         "127.0.0.1"  # Localhost only (more secure)
```

---

## 🔄 Management Commands

### PowerShell Service Management

```powershell
# Check status
Get-Service MPD

# Start/Stop/Restart
Start-Service MPD
Stop-Service MPD
Restart-Service MPD

# Set startup type
Set-Service MPD -StartupType Automatic
```

### Docker Container Management

```powershell
# View logs
docker-compose -f docker-compose.native-mpd.yml logs -f

# Restart web interface
docker-compose -f docker-compose.native-mpd.yml restart

# Rebuild after changes
docker-compose -f docker-compose.native-mpd.yml up -d --build

# Stop everything
docker-compose -f docker-compose.native-mpd.yml down
```

### MPD Client Commands (mpc)

```powershell
# Playback control
mpc play
mpc pause
mpc stop
mpc next
mpc prev

# Playlist management
mpc clear
mpc add "Artist/Album"
mpc playlist

# Database
mpc update
mpc rescan

# Status
mpc status
mpc stats
mpc outputs
```

---

## 📱 Usage Workflow

### Daily Use:

1. **MPD runs automatically** (Windows service)
2. **Open web interface**: `http://localhost:5003`
3. **Browse and play music**
4. **Audio plays through Windows speakers/headphones** 🎵

### Starting/Stopping:

```powershell
# Stop everything
Stop-Service MPD
docker-compose -f docker-compose.native-mpd.yml down

# Start everything
Start-Service MPD
docker-compose -f docker-compose.native-mpd.yml up -d
```

---

## 🆚 Comparison: Native vs Containerized

### When to use Native MPD:
- ✅ Daily driver / primary music player
- ✅ Want native Windows audio quality
- ✅ Multiple audio outputs needed
- ✅ Existing MPD setup to integrate

### When to use Containerized MPD:
- ✅ Testing/development
- ✅ Temporary setup
- ✅ Don't want to install MPD
- ✅ Browser/VLC playback is acceptable

---

## 🔗 Additional Resources

- **MPD Official Site:** https://www.musicpd.org/
- **MPD Windows Builds:** https://www.musicpd.org/download.html
- **Chocolatey:** https://chocolatey.org/
- **NSSM (Service Manager):** https://nssm.cc/
- **Maestro Project:** See main README.md

---

## 💡 Tips & Tricks

### Multiple Output Setup

Enable both system audio AND HTTP streaming:

```ini
# Native Windows audio
audio_output {
    type        "wasapi"
    name        "Speakers"
    enabled     "yes"
}

# Stream to other devices
audio_output {
    type        "httpd"
    name        "Web Stream"
    port        "8001"
    enabled     "yes"
}
```

### System Tray Integration

Use **MPD clients** for system tray control:
- **Cantata** (full-featured)
- **M.A.L.P.** (mobile app)
- **MPD Web interface** (this project!)

### Autostart on Login

**Task Scheduler method:**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At log on
4. Action: Start program `mpd.exe`
5. Arguments: `--no-daemon "C:/Users/YourName/AppData/Roaming/mpd/mpd.conf"`

---

## ✅ Quick Checklist

After setup, verify:

- [ ] MPD service running: `Get-Service MPD`
- [ ] MPD responding: `Test-NetConnection localhost -Port 6600`
- [ ] Web container running: `docker ps`
- [ ] Web interface accessible: `http://localhost:5003`
- [ ] Music library visible in web UI
- [ ] Audio plays through Windows speakers
- [ ] Database updates automatically

---

**🎉 Enjoy your native Windows MPD setup with Maestro control!**
