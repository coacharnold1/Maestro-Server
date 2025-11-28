# 🎵 Maestro MPD Control - Quick Setup

## One-Command Installation

```bash
git clone <repository-url>
cd maestro-mpd-control 
./setup.sh
```

**That's it!** The setup script will automatically:

- ✅ **Detect your audio system** (PipeWire/PulseAudio/ALSA)
- ✅ **Configure native audio** for your system  
- ✅ **Set up HTTP streaming** as backup
- ✅ **Handle Docker permissions** automatically
- ✅ **Optimize performance** for your hardware

## What You Get

### 🎧 **Automatic Audio**
- **Native System Audio**: Music plays through your speakers/headphones
- **HTTP Streaming**: `http://localhost:8001` for browser/remote access
- **No Manual Configuration**: Audio system auto-detected

### 🎛️ **Web Interface** 
- **Full Control**: `http://localhost:5003`
- **4 Themes**: Dark, Light, High Contrast, Desert
- **Mobile Responsive**: Works on phones/tablets
- **Fast Controls**: Optimized for performance

### 📂 **Smart Features**
- **Recent Albums**: Auto-scans configured directories
- **Last.fm Integration**: Scrobbling and charts (optional)
- **Radio Stations**: Built-in internet radio
- **Auto-fill Playlists**: Smart playlist generation

## Audio Systems Supported

| System | Detection | Configuration |
|--------|-----------|---------------|
| **PipeWire** | ✅ Auto | Native audio + HTTP backup |
| **PulseAudio** | ✅ Auto | Native audio + HTTP backup |  
| **ALSA** | ✅ Auto | Direct hardware access |
| **Other/None** | ✅ Auto | HTTP streaming only |

## Troubleshooting

### No Sound?
The setup script will tell you exactly what to do:
```bash
# Usually just:
sudo usermod -aG audio $USER
# Then log out/in or run: newgrp audio
```

### Slow Controls?
```bash
# Edit .env file:
MPD_TIMEOUT=3  # Faster response
# Then: docker-compose restart
```

### Want External MPD?
```bash
# In .env file:
MPD_HOST=localhost
MPD_PORT=6600
# Then: docker-compose up web  # Only web interface
```

## For Advanced Users

### Manual Audio Configuration
```bash
# Edit docker/mpd.conf to enable specific outputs:
audio_output {
    type        "pulse"     # or "alsa" or "httpd"
    name        "My Audio"
    enabled     "yes"
}
```

### Performance Tuning
```bash
# See PERFORMANCE.md for detailed optimizations
# Quick fixes in .env:
RECENT_MUSIC_DIRS=      # Disable recent scanning  
AUTO_FILL_ENABLED=false # Disable auto-fill
MPD_TIMEOUT=2           # Faster timeouts
```

### Custom Themes
```bash
# Edit templates/*.html and static/styles
# Or contribute new themes to the project!
```

## Post-Installation

1. **Open**: `http://localhost:5003`
2. **Configure**: Settings → Last.fm API (optional)
3. **Enjoy**: Your music with native audio! 🎵

---

**Questions?** Check [README.md](README.md) for comprehensive documentation.