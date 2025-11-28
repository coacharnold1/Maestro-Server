# Performance Optimization Guide

## For Slower Systems

If you experience slow control responses, try these optimizations:

### 1. Quick Performance Mode
```bash
# Stop containers
sudo docker-compose down

# Edit .env file to reduce timeouts
sed -i 's/MPD_TIMEOUT=10/MPD_TIMEOUT=3/' .env

# Restart with performance optimizations
sudo docker-compose up -d
```

### 2. Disable Resource-Heavy Features
```bash
# In .env file, set:
RECENT_MUSIC_DIRS=    # Empty = disable recent scanning
AUTO_FILL_ENABLED=false
```

### 3. Use External MPD (Fastest)
Instead of containerized MPD, connect to system MPD:
```bash
# Install system MPD
sudo apt install mpd

# Configure external connection in .env:
MPD_HOST=localhost
MPD_PORT=6600

# Run only web interface
docker-compose up web
```

### 4. Direct Audio Access (Linux)
For minimal latency, use direct audio:
```bash
# Add to .env:
ENABLE_DIRECT_AUDIO=true

# Requires host audio access
```

## Performance Tips

### Control Responsiveness
- **Timeout**: Lower `MPD_TIMEOUT` (3s vs 10s)
- **Memory**: Limit container memory usage  
- **Health Checks**: Reduce frequency

### Audio Quality vs Performance
- **HTTP Stream**: 320kbps (good quality, more CPU)
- **Lower Bitrate**: Edit `docker/mpd.conf` → `bitrate "192"`
- **Disable Effects**: Remove crossfade, EQ

### System Resources
```bash
# Check Docker resource usage
docker stats

# Monitor system load
htop

# Free up memory
sudo docker system prune
```

## Troubleshooting Slow Performance

### Symptoms: Controls take 5-10 seconds
**Cause**: Docker overhead + slow disk I/O
**Solution**: Use external MPD or reduce timeouts

### Symptoms: Audio stuttering  
**Cause**: CPU/memory bottleneck
**Solution**: Lower bitrate, close other apps

### Symptoms: Web interface freezing
**Cause**: JavaScript/browser performance  
**Solution**: Use simpler browser, disable extensions

## Alternative: Lightweight Setup

For very slow systems, consider this minimal setup:
```bash
# Use system MPD + simple web controls
sudo apt install mpd ncmpcpp
# Edit ~/.config/mpd/mpd.conf for HTTP output
# Access via ncmpcpp (terminal) + browser stream
```