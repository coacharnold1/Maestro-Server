# 🎵 Maestro MPD Server v2.0

**Complete Music Server Solution** with Web UI and System Administration

A modern, feature-rich Music Player Daemon (MPD) controller with web interface and comprehensive system management capabilities.

---

## ✨ Features

### 🎧 Web UI (Port 5003)
- Full MPD control (play, pause, volume, playlists)
- Album/artist/genre browsing
- **Recent albums** page (configurable directory)
- Search functionality
- Queue management
- HTTP audio streaming
- **Multiple themes** (Dark, Light, High Contrast, Desert)
- Mobile-responsive design
- Last.fm scrobbling support

### ⚙️ Admin API (Port 5004)
- **System Monitoring**: Real-time CPU, RAM, disk, network stats
- **Library Management**: 
  - Configure NFS/SMB network mounts
  - View existing MPD library structure with mount status
  - Trigger library updates with verification
  - Smart file counting (optimized for network shares)
- **Audio Configuration**:
  - Audio device scanning and selection
  - Current device display
  - Automatic MPD config updates
  - Bit-perfect playback settings
  - System audio optimizations (CPU governor, swappiness)
- **System Administration**:
  - OS package updates with progress tracking
  - System reboot with countdown
  - Service management

---

## 🚀 Quick Installation

### Fresh Ubuntu/Debian Server

```bash
git clone https://github.com/coacharnold1/Maestro-Server.git
cd Maestro-Server
./install-maestro.sh
```

The installer will:
1. **Detect existing MPD** or install new (preserves custom builds)
2. Configure music directory and recent albums folder
3. **Select UI theme** (Dark, Light, High Contrast, Desert)
4. Set up Web UI (port 5003)
5. Set up Admin API (port 5004)
6. Create systemd services
7. Configure sudo permissions and audio group membership

**Installation time:** ~5 minutes

---

## 📋 Requirements

### Supported Operating Systems
- Ubuntu Server 20.04+
- Debian 11+
- Arch Linux

### System Requirements
- 1GB RAM minimum (2GB+ recommended)
- 1GB disk space (+ music storage)
- Network connectivity
- Audio output device (optional for headless)

### Pre-installed Dependencies
The installer handles all dependencies automatically:
- MPD + MPC
- Python 3.8+
- ALSA utilities
- NFS/CIFS tools

---

## 📦 What Gets Installed

```
~/maestro/
├── web/                    # Web UI
│   ├── venv/              # Python virtual environment
│   ├── app.py             # Flask web server
│   └── templates/         # HTML pages
├── admin/                  # Admin API
│   ├── venv/              # Python virtual environment
│   ├── admin_api.py       # Flask admin server
│   └── templates/         # Admin pages
└── logs/                   # Application logs

/etc/systemd/system/
├── maestro-web.service     # Web UI service
└── maestro-admin.service   # Admin API service

/etc/mpd.conf               # MPD configuration
/media/music/               # Music directory (configurable)
```

---

## 🌐 Access

After installation completes, the installer will display:

```
Web UI:    http://YOUR_IP:5003
Admin API: http://YOUR_IP:5004
MPD:       YOUR_IP:6600
```

---

## 🎛️ Configuration

### Music Directory

Default: `/media/music`

Add music via:
1. **Local**: Copy files to `/media/music/`
2. **Network**: Use Admin API → Library Management → Add Mount

### Audio Settings

Configure via Admin API → Audio Tweaks:
- Buffer size (2048-16384)
- Output format (native/bit-perfect recommended)
- Resampling quality
- Mixer type
- DSD playback mode

### Network Mounts

Add NFS/SMB shares via Admin API:
1. Navigate to Library Management
2. Click "Add Mount"
3. Configure share details
4. Mounts are created under `/media/music/`

---

## 🔧 Service Management

```bash
# Web UI
sudo systemctl {start|stop|restart|status} maestro-web

# Admin API
sudo systemctl {start|stop|restart|status} maestro-admin

# MPD
sudo systemctl {start|stop|restart|status} mpd
```

### View Logs

```bash
# Web UI
journalctl -u maestro-web -f

# Admin API
journalctl -u maestro-admin -f

# MPD
journalctl -u mpd -f
```

---

## 🌟 Smart Features

### MPD Detection
- Automatically detects existing MPD installations
- Preserves custom-built MPD binaries
- Option to use existing, install new, or skip

### Safe Uninstallation
- Never removes user music files
- Preserves MPD configurations and data
- Only removes Maestro-installed components
- Tracks installation info to avoid conflicts

### Audio Device Management
- Scans and displays available audio hardware
- Shows currently configured device
- One-click device switching
- Automatic MPD configuration updates
- Requires MPD restart to apply changes

### Performance Optimizations
- Smart file counting skips network mounts
- Fast page loads even with large libraries
- Configurable timeouts for slow storage
- Optimized for NFS/SMB shares

---

## 🛠️ Manual Setup (Development)

If you prefer not to use the installer:

### 1. Install Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install mpd mpc python3 python3-pip python3-venv alsa-utils nfs-common cifs-utils
```

**Arch Linux:**
```bash
sudo pacman -S mpd mpc python python-pip alsa-utils nfs-utils cifs-utils
```

### 2. Configure MPD

```bash
sudo systemctl enable mpd
sudo systemctl start mpd
# Edit /etc/mpd.conf as needed
```

### 3. Setup Web UI

```bash
cd Maestro-MPD-Control
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

### 4. Setup Admin API

```bash
cd Maestro-MPD-Control/admin
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 admin_api.py
```

---

## 📚 Documentation

- **[Admin Integration Guide](ADMIN_INTEGRATION.md)** - Detailed integration documentation
- **[Admin API README](admin/README.md)** - API endpoints and usage
- **[MPD Documentation](https://www.musicpd.org/doc/)** - Official MPD docs

---

## 🎯 Usage Examples

### Add Network Music Share

1. Open Admin API: `http://YOUR_IP:5004`
2. Navigate to **Library Management**
3. Click **Add Mount**
4. Fill in NFS/SMB details
5. Click **Mount** to connect
6. Click **Update MPD Library** to scan

### Configure Audio for Audiophile Playback

1. Open Admin API: `http://YOUR_IP:5004`
2. Navigate to **Audio Tweaks**
3. Set **Output Format**: Native (bit-perfect)
4. Set **Resample Quality**: Disabled
5. Set **Mixer Type**: None (use DAC volume)
6. Click **Save** and restart MPD

### Update System Packages

1. Open Admin API: `http://YOUR_IP:5004`
2. Navigate to **System Admin**
3. Click **Update OS Packages**
4. View progress: package count, duration, changes

---

## 🔐 Security Notes

### Sudo Configuration

The installer configures passwordless sudo for specific commands in `/etc/sudoers.d/maestro`. This is required for:
- System updates (`apt`, `pacman`)
- Service management (`systemctl`)
- Mount/unmount operations
- System reboot

### Network Security

Both services bind to `0.0.0.0` (all interfaces). To restrict access:

```bash
# Edit service files
sudo systemctl edit maestro-web
sudo systemctl edit maestro-admin

# Add under [Service]:
Environment="FLASK_RUN_HOST=127.0.0.1"
```

Or use a reverse proxy (nginx, apache) with authentication.

---

## 🐛 Troubleshooting

### Web UI won't start

```bash
# Check status
sudo systemctl status maestro-web

# View logs
journalctl -u maestro-web -n 50

# Test manually
cd ~/maestro/web
source venv/bin/activate
python3 app.py
```

### MPD connection failed

```bash
# Check MPD status
sudo systemctl status mpd

# Test connection
mpc status

# Verify port
sudo netstat -tlnp | grep 6600
```

### Audio device not found

```bash
# Scan devices (needs sudo)
sudo aplay -l

# Check ALSA configuration
aplay -L
```

### Mount operation failed

```bash
# Test mount manually
sudo mount -t nfs server:/path /media/music/test

# Check network connectivity
ping server_ip

# Verify NFS/CIFS tools installed
which mount.nfs
which mount.cifs
```

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📜 License

[Your License Here]

---

## 🙏 Credits

Built with:
- [Music Player Daemon (MPD)](https://www.musicpd.org/)
- [Flask](https://flask.palletsprojects.com/)
- [python-mpd2](https://github.com/Mic92/python-mpd2)
- [psutil](https://github.com/giampaolo/psutil)

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/coacharnold1/Maestro-MPD-Control/issues)
- **Discussions**: [GitHub Discussions](https://github.com/coacharnold1/Maestro-MPD-Control/discussions)

---

**Enjoy your music! 🎵**
