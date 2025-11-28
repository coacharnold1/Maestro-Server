# 🎧 **Critical: Windows Audio Configuration**

**⚠️ Windows + Docker Audio Reality Check:**

Unlike Linux, **Windows Docker containers CANNOT directly access system audio**. Here are your options:

## 🔊 **Audio Solutions for Windows**

### 🌐 **Option 1: HTTP Streaming (Recommended)**
**✅ Works on all Windows versions**

```powershell
# After setup, audio streams to: http://localhost:8001
# Open this URL in any browser or media player:
start http://localhost:8001

# Or use VLC:
# "C:\Program Files\VideoLAN\VLC\vlc.exe" http://localhost:8001
```

**Advantages:**
- ✅ Works immediately after setup
- ✅ No additional configuration
- ✅ Browser playback or external players
- ✅ 320kbps high quality

### 🎵 **Option 2: External Music Player**
**✅ Best audio quality**

```powershell
# Install VLC Media Player
# Download: https://www.videolan.org/vlc/download-windows.html

# Play the stream:
vlc.exe http://localhost:8001

# Or use Windows Media Player (if available):
# File -> Open URL -> http://localhost:8001
```

### 📡 **Option 3: WSL2 Audio Forwarding (Advanced)**
**⚠️ Requires additional setup**

```bash
# In WSL2, install PulseAudio for Windows
sudo apt update && sudo apt install pulseaudio

# Configure audio forwarding (complex setup)
# See: https://wiki.archlinux.org/title/PulseAudio/Examples
```

### 🎆 **Option 4: Native Windows MPD (Alternative)**
**✅ True native audio**

```powershell
# Skip Docker entirely, use native Windows MPD:
# 1. Install MPD for Windows: https://www.musicpd.org/download.html
# 2. Configure for your music directory
# 3. Use only the web interface container:
docker run -p 5003:5003 -e MPD_HOST=localhost maestro-web
```

---

## 🎯 **Recommended Windows Workflow**

For **95% of Windows users**, the HTTP streaming approach works perfectly:

1. **Run setup** (containers start)
2. **Open browser** → `http://localhost:5003` (controls)
3. **Open second tab** → `http://localhost:8001` (audio stream)
4. **Control music** in first tab, **hear audio** in second tab

**Or use a media player:**
1. **Run setup** (containers start)
2. **Open VLC** → Media → Open Network Stream → `http://localhost:8001`
3. **Control via web** → `http://localhost:5003`

---

# 🏠 Windows Setup Instructions

## 📝 Prerequisites

### Required Software
- **Docker Desktop for Windows** (includes Docker Compose)
  - Download: https://www.docker.com/products/docker-desktop/
  - Requires Windows 10/11 Pro, Enterprise, or Education
  - OR Windows 10/11 Home with WSL2

### Audio Requirements
- **Web Browser** (Chrome, Firefox, Edge) for HTTP audio streaming
- **OR Media Player** (VLC, Windows Media Player) for better audio quality
- **Note**: Direct system audio not supported in Windows Docker

### Recommended Setup Options

## 🎯 Option 1: WSL2 (Recommended for Best Experience)

**Why WSL2?** Full Linux compatibility, best performance, native bash script support.

### Step 1: Install WSL2
```powershell
# Run in PowerShell as Administrator
wsl --install
# Restart your computer when prompted
```

### Step 2: Install Docker Desktop
1. Download and install Docker Desktop
2. In Docker Desktop settings, ensure "Use the WSL2 based engine" is enabled
3. Enable integration with your WSL2 distro (usually Ubuntu)

### Step 3: Setup in WSL2
```bash
# Open WSL2 terminal (Ubuntu)
cd /mnt/c/Users/YourUsername/Desktop  # Navigate to where you extracted the project

# Run the setup script (full compatibility)
chmod +x setup.sh
./setup.sh
```

---

## 🔧 Option 2: PowerShell Manual Setup

**For users who prefer staying in Windows environment.**

### Step 1: Prepare Your Music Directory
```powershell
# Create a music directory if you don't have one
mkdir "C:\Music"

# Note: Your music files should be in this directory
# Supported formats: MP3, FLAC, M4A, OGG, WAV
```

### Step 2: Download Project
Extract the Maestro MPD Control files to a directory, for example:
```
C:\Users\YourUsername\Desktop\maestro-mpd-control\
```

### Step 3: Configure Environment
```powershell
# Navigate to project directory
cd "C:\Users\YourUsername\Desktop\maestro-mpd-control"

# Copy the example environment file
copy config.env.example config.env

# Edit config.env with your preferred text editor
notepad config.env
```

### Step 4: Edit Configuration
Update `config.env` with Windows-style paths:

```env
# Music library path (use forward slashes for Docker)
MUSIC_DIRECTORY=C:/Music

# Web interface settings
WEB_PORT=5000
DEFAULT_THEME=dark

# MPD Settings (use containerized MPD)
MPD_HOST=mpd
MPD_PORT=6600

# Last.fm Integration (optional)
LASTFM_API_KEY=
LASTFM_API_SECRET=
```

### Step 5: Start Services
```powershell
# Start the Docker containers
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs if needed
docker-compose logs -f
```

### Step 6: Access the Interface
Open your browser and go to: http://localhost:5000

---

## 🎮 Option 3: Git Bash (Alternative)

**If you have Git for Windows installed with Git Bash.**

### Setup Process
```bash
# Open Git Bash in your project directory
cd /c/Users/YourUsername/Desktop/maestro-mpd-control

# Make script executable
chmod +x setup.sh

# Run setup (may have minor compatibility issues)
./setup.sh

# If network checks fail, continue with manual setup
```

**Note:** Some network connectivity tests may fail in Git Bash, but Docker operations should work.

---

## 🚨 Common Windows Issues & Solutions

### Issue 1: Docker Desktop Not Starting
**Problem:** Docker Desktop fails to start or shows WSL2 errors.

**Solutions:**
```powershell
# Enable required Windows features
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart computer, then update WSL2
wsl --update
```

### Issue 2: File Path Issues
**Problem:** Music directory not mounting correctly.

**Solutions:**
- Use forward slashes in `config.env`: `C:/Music` not `C:\Music`
- Ensure the path exists before starting Docker
- Check Docker Desktop -> Settings -> Resources -> File Sharing

### Issue 3: Permission Denied Errors
**Problem:** Docker containers can't access music files.

**Solutions:**
```powershell
# In your music directory, ensure files aren't read-only
attrib -R C:\Music\*.* /S

# Restart Docker Desktop and try again
```

### Issue 4: Port Already in Use
**Problem:** Port 5000 is already occupied.

**Solutions:**
```powershell
# Find what's using the port
netstat -ano | findstr :5000

# Kill the process (replace PID with actual process ID)
taskkill /F /PID <PID>

# Or change the port in config.env
# WEB_PORT=5001
```

### Issue 5: Setup Script Network Checks Fail
**Problem:** Script can't test MPD connectivity on Windows.

**Solutions:**
1. Skip connectivity tests and proceed with Docker setup
2. Use manual PowerShell setup method instead
3. Test connectivity after containers are running:
```powershell
# Test if MPD container is responding
docker-compose exec mpd nc -z localhost 6600
```

---

## 📁 Windows File Structure Example

```
C:\Users\YourUsername\Desktop\maestro-mpd-control\
├── app.py
├── docker-compose.yml
├── Dockerfile
├── config.env                 # Your configuration
├── requirements.txt
├── setup.sh                   # Use with WSL2/Git Bash
├── README.md
├── WINDOWS_SETUP.md          # This file
└── static/
    ├── manifest.json
    └── ...
```

```
C:\Music\                      # Your music library
├── Artist 1/
│   └── Album 1/
│       ├── 01 Track.mp3
│       └── 02 Track.mp3
├── Artist 2/
│   └── Album 2/
│       └── song.flac
└── ...
```

---

## 🔧 Manual Commands Reference

### Docker Management
```powershell
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# Update containers
docker-compose pull
docker-compose up -d

# Remove everything (keeps music files)
docker-compose down -v
```

### Troubleshooting Commands
```powershell
# Check Docker status
docker version
docker-compose version

# Check running containers
docker ps

# Check container logs
docker-compose logs mpd
docker-compose logs web

# Enter container for debugging
docker-compose exec web bash
docker-compose exec mpd bash
```

---

## 🔊 **Windows Audio Testing Guide**

After setup is complete, **test your audio immediately:**

### 🎯 **Step 1: Verify HTTP Stream**
```powershell
# Check if audio stream is available
curl http://localhost:8001
# Should return: "ICY 200 OK" or start streaming
```

### 🌐 **Step 2: Browser Audio Test**
1. **Open Chrome/Firefox/Edge**
2. **Go to:** `http://localhost:8001`
3. **You should see:** "Audio stream starting..." or hear music
4. **If no sound:** Check Windows volume mixer

### 🎵 **Step 3: VLC Audio Test (Recommended)**
```powershell
# Download VLC if not installed
# https://www.videolan.org/vlc/download-windows.html

# Test the stream in VLC
"C:\Program Files\VideoLAN\VLC\vlc.exe" http://localhost:8001
```

### 📱 **Step 4: Control + Audio Workflow**
1. **Control Tab:** `http://localhost:5003` (main interface)
2. **Audio Tab:** `http://localhost:8001` (sound output)
3. **Test:** Play music in control tab, verify sound in audio tab

### ⚠️ **Common Windows Audio Issues**

**Problem: "No audio stream"**
```powershell
# Check if MPD is running
docker-compose logs mpd

# Look for: "Output plugin opened audio output"
# If missing: MPD audio setup failed
```

**Problem: "Stream connection refused"**
```powershell
# Verify port 8001 is open
netstat -an | findstr :8001

# Should show: TCP 0.0.0.0:8001 LISTENING
```

**Problem: "Static/crackling audio"**
- **Browser:** Try Chrome instead of Edge/Firefox
- **VLC:** Use VLC for better audio quality
- **Network:** Check if localhost connection is stable

### ✅ **Expected Windows Audio Workflow**
```
1. Start containers → docker-compose up -d
2. Open control interface → http://localhost:5003
3. Add music to library (via web interface)
4. Start VLC → Media → Open Network Stream → http://localhost:8001
5. Play music via web controls
6. Audio plays through VLC with high quality
```

---

## 🎵 Last.fm Setup on Windows

1. **Get API Keys:**
   - Visit: https://www.last.fm/api/account/create
   - Create application: "Maestro MPD Control"
   - Copy API Key and Shared Secret

2. **Configure:**
   - Edit `config.env` in Notepad or your preferred editor
   - Add your API credentials:
   ```env
   LASTFM_API_KEY=your_api_key_here
   LASTFM_API_SECRET=your_shared_secret_here
   ```

3. **Restart containers:**
   ```powershell
   docker-compose down
   docker-compose up -d
   ```

---

## 🎯 Quick Start Summary

**For WSL2 Users (Recommended):**
```bash
# In WSL2 terminal
./setup.sh
# Follow prompts, done!
```

**For PowerShell Users:**
```powershell
# Edit configuration
copy config.env.example config.env
notepad config.env

# Start containers  
docker-compose up -d

# Open browser to http://localhost:5000
```

**Need Help?** Check the main README.md for additional troubleshooting and feature documentation.