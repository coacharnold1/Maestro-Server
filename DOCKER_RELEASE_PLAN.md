# MPD Web Control - Docker Release Implementation Plan

## 📅 Created: November 17, 2025

This document outlines the complete process for creating a clean, user-ready Docker release from your current working system.

## 🎯 **Phase 1: Freeze Current Version**

### **Step 1.1: Create Release Candidate Backup**
```bash
# On your current working system
cd /home/fausto/mpd_web_control_combined_20251104_180921

# Create specifically labeled release backup
./backup.sh "DOCKER_RELEASE_CANDIDATE_v1.0.0_20251117"

# Verify backup creation
ls -la backups/mpd_web_control_backup_*DOCKER_RELEASE*
```

### **Step 1.2: Document Current State**
```bash
# Capture current version info
echo "v1.0.0-docker-$(date +%Y%m%d)" > VERSION_DOCKER_RELEASE
echo "Release Date: $(date)" >> VERSION_DOCKER_RELEASE
echo "Features: 4 Themes, Mobile Responsive, Radio Stations, Auto-Fill" >> VERSION_DOCKER_RELEASE
echo "Templates: $(ls templates/*.html | wc -l) HTML files" >> VERSION_DOCKER_RELEASE
echo "Last Backup: $(ls -t backups/*.tar.gz | head -1)" >> VERSION_DOCKER_RELEASE
```

### **Step 1.3: Transfer to Fresh System**
```bash
# Copy release backup to fresh machine/VM
scp backups/mpd_web_control_backup_*DOCKER_RELEASE*.tar.gz user@fresh-system:~/
```

---

## 🔧 **Phase 2: Fresh System Setup**

### **Step 2.1: Extract & Initialize**
```bash
# On fresh system
mkdir ~/mpd-docker-build && cd ~/mpd-docker-build
tar -xzf ~/mpd_web_control_backup_*DOCKER_RELEASE*.tar.gz
cd mpd_web_control_combined_*/

# Verify extraction
ls -la
echo "✅ Source code extracted successfully"
```

### **Step 2.2: Clean Personal Data**
```bash
# Remove development artifacts
rm -f config.env                    # Personal config
rm -f settings.json                 # Personal theme/lastfm settings  
rm -f radio_stations.json           # Personal radio stations
rm -rf __pycache__/                  # Python cache
rm -rf venv/                         # Virtual environment
rm -rf backups/                      # Backup files
rm -rf .pytest_cache/ .coverage     # Test artifacts (if any)

# Create clean examples
cp config.env.example config.env.docker.example
echo "✅ Personal data cleaned"
```

### **Step 2.3: Remove Admin Features**
```bash
# Search for admin references to remove
grep -r "Maestro Config" templates/
grep -r "port.*5000" .

# Remove admin buttons from templates (we'll do this step by step)
echo "⚠️  Manual cleanup needed: Remove admin features from templates"
```

---

## 🐳 **Phase 3: Docker Implementation**

### **Step 3.1: Create Dockerfile**
```dockerfile
# Dockerfile
FROM python:3.13-slim

LABEL maintainer="MPD Web Control"
LABEL version="1.0.0"
LABEL description="Modern web interface for Music Player Daemon with 4 themes"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user
RUN useradd -m -u 1001 mpdweb && \
    mkdir -p /app && \
    chown mpdweb:mpdweb /app

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=mpdweb:mpdweb . .

# Create runtime directories
RUN mkdir -p /app/cache /app/data && \
    chown mpdweb:mpdweb /app/cache /app/data

# Switch to non-root user
USER mpdweb

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:5003/api/status || exit 1

EXPOSE 5003

CMD ["python", "app.py"]
```

### **Step 3.2: Create Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'

services:
  mpd:
    image: vimagick/mpd:latest
    container_name: mpd-server
    volumes:
      - ./docker/mpd.conf:/etc/mpd.conf:ro
      - ${MUSIC_DIRECTORY}:/music:ro
      - mpd_db:/var/lib/mpd
      - mpd_playlists:/var/lib/mpd/playlists
    ports:
      - "6600:6600"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "echo 'ping' | nc localhost 6600 | grep -q 'OK'"]
      interval: 30s
      timeout: 5s
      retries: 3

  web:
    build: .
    container_name: mpd-web-control
    depends_on:
      mpd:
        condition: service_healthy
    environment:
      - MPD_HOST=mpd
      - MPD_PORT=6600
      - MUSIC_DIRECTORY=/music
      - APP_PORT=5003
      - APP_HOST=0.0.0.0
      - DEFAULT_THEME=${DEFAULT_THEME:-dark}
      - LASTFM_API_KEY=${LASTFM_API_KEY:-}
      - LASTFM_SHARED_SECRET=${LASTFM_SHARED_SECRET:-}
      - AUTO_FILL_ENABLED=${AUTO_FILL_ENABLED:-true}
    volumes:
      - ${MUSIC_DIRECTORY}:/music:ro
      - ./data:/app/data
      - web_cache:/app/cache
    ports:
      - "${WEB_PORT:-5003}:5003"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5003/api/status"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  mpd_db:
    driver: local
  mpd_playlists:
    driver: local
  web_cache:
    driver: local

networks:
  default:
    name: mpd-network
```

### **Step 3.3: Create Setup Scripts**

#### **Main Setup Script**
```bash
#!/bin/bash
# setup.sh - One-command Docker installation

set -e

echo "🎵 MPD Web Control - Docker Edition"
echo "===================================="
echo ""

# Check prerequisites
command -v docker >/dev/null 2>&1 || {
    echo "❌ Docker is required but not installed."
    echo "   Please install Docker and try again."
    echo "   https://docs.docker.com/get-docker/"
    exit 1
}

command -v docker-compose >/dev/null 2>&1 || {
    echo "❌ Docker Compose is required but not installed."
    echo "   Please install Docker Compose and try again."
    exit 1
}

# Run configuration wizard
echo "🔧 Starting configuration wizard..."
./scripts/configure.sh

# Start services
echo ""
echo "🚀 Building and starting services..."
docker-compose up -d --build

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 15

# Health check
if curl -s http://localhost:${WEB_PORT:-5003}/api/status > /dev/null; then
    echo ""
    echo "✅ MPD Web Control is ready!"
    echo ""
    echo "🌐 Web Interface: http://localhost:${WEB_PORT:-5003}"
    echo "🎨 Available Themes: Dark • Light • High Contrast • Desert"
    echo "📋 Default Login: No authentication required"
    echo ""
    echo "📖 Management Commands:"
    echo "   View logs:     docker-compose logs -f"
    echo "   Stop services: docker-compose down"
    echo "   Restart:       docker-compose restart"
else
    echo "❌ Service health check failed. Check logs with: docker-compose logs"
    exit 1
fi
```

#### **Configuration Wizard**
```bash
#!/bin/bash
# scripts/configure.sh - Interactive configuration

echo "📁 Music Library Configuration"
echo "=============================="

# Music directory
while true; do
    read -p "Enter path to your music directory: " MUSIC_DIR
    if [ -d "$MUSIC_DIR" ]; then
        echo "✅ Music directory found: $MUSIC_DIR"
        break
    else
        echo "❌ Directory not found: $MUSIC_DIR"
        echo "   Please enter a valid path to your music collection"
    fi
done

# Web port
read -p "Web interface port [5003]: " WEB_PORT
WEB_PORT=${WEB_PORT:-5003}

# Theme selection
echo ""
echo "🎨 Theme Selection"
echo "=================="
echo "1) Dark (default)"
echo "2) Light"
echo "3) High Contrast" 
echo "4) Desert"
read -p "Choose default theme [1]: " THEME_CHOICE
THEME_CHOICE=${THEME_CHOICE:-1}

case $THEME_CHOICE in
    2) DEFAULT_THEME="light" ;;
    3) DEFAULT_THEME="high-contrast" ;;
    4) DEFAULT_THEME="desert" ;;
    *) DEFAULT_THEME="dark" ;;
esac

# Last.fm (optional)
echo ""
echo "🎵 Last.fm Integration (Optional)"
echo "================================="
echo "Last.fm provides music charts and scrobbling features."
read -p "Enable Last.fm integration? [y/N]: " ENABLE_LASTFM

LASTFM_API_KEY=""
LASTFM_SECRET=""
if [[ $ENABLE_LASTFM =~ ^[Yy]$ ]]; then
    read -p "Last.fm API Key: " LASTFM_API_KEY
    read -s -p "Last.fm Shared Secret: " LASTFM_SECRET
    echo ""
fi

# Generate .env file
cat > .env << EOF
# MPD Web Control - Docker Configuration
# Generated on $(date)

# Music Library
MUSIC_DIRECTORY=$MUSIC_DIR

# Web Interface
WEB_PORT=$WEB_PORT
DEFAULT_THEME=$DEFAULT_THEME

# Last.fm Integration (Optional)
LASTFM_API_KEY=$LASTFM_API_KEY
LASTFM_SHARED_SECRET=$LASTFM_SECRET

# Auto-Fill Settings
AUTO_FILL_ENABLED=true
AUTO_FILL_MIN_TRACKS=3
AUTO_FILL_MAX_TRACKS=7

# Advanced Settings (usually don't need to change)
MPD_HOST=mpd
MPD_PORT=6600
APP_HOST=0.0.0.0
EOF

echo ""
echo "✅ Configuration saved to .env"
echo "   You can edit this file later if needed"
```

---

## 📦 **Phase 4: GitHub Release Package**

### **Step 4.1: Create Release Structure**
```bash
# Create clean release directory
mkdir ~/mpd-web-control-docker-release
cd ~/mpd-web-control-docker-release

# Copy application files
cp -r ~/mpd-docker-build/mpd_web_control_combined_*/* .

# Create release-specific directories
mkdir -p docker scripts docs

# Organize files
mv Dockerfile docker/
mv configure.sh scripts/
```

### **Step 4.2: Create Documentation**
```markdown
# README.md for Docker Release

# 🎵 MPD Web Control - Docker Edition

Modern, responsive web interface for Music Player Daemon with 4 beautiful themes.

## ✨ Features

- 🎨 **4 Beautiful Themes**: Dark, Light, High Contrast, Desert
- 📱 **Mobile Responsive**: Perfect on any device
- 📻 **Radio Stations**: Save genre combinations as preset stations
- 🔀 **Smart Auto-Fill**: Intelligent playlist management
- 🔍 **Powerful Search**: Find music across your entire library
- 📊 **Last.fm Integration**: Charts and scrobbling support
- 🎵 **Rich Playlist Management**: Album art, metadata, easy organization

## 🚀 Quick Start

1. **Clone or Download**
   ```bash
   git clone https://github.com/yourusername/mpd-web-control-docker.git
   cd mpd-web-control-docker
   ```

2. **One-Command Setup**
   ```bash
   ./setup.sh
   ```

3. **Access Your Music**
   Open http://localhost:5003

## 📋 Requirements

- Docker & Docker Compose
- Music directory accessible to Docker
- MPD compatible music library

## 🎨 Screenshots

[Include screenshots of all 4 themes]

## 📖 Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Configuration Options](docs/CONFIGURATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
```

### **Step 4.3: Create Release Archive**
```bash
# Create distributable archive
cd ~/
tar -czf mpd-web-control-docker-v1.0.0.tar.gz mpd-web-control-docker-release/

# Create GitHub release files
cd ~/mpd-web-control-docker-release
git init
git add .
git commit -m "Initial Docker release v1.0.0"
```

---

## 🎯 **Phase 5: Testing & Validation**

### **Step 5.1: Fresh Install Test**
```bash
# Test complete setup on another fresh system
mkdir ~/test-install && cd ~/test-install
tar -xzf mpd-web-control-docker-v1.0.0.tar.gz
cd mpd-web-control-docker-release/
./setup.sh
```

### **Step 5.2: Feature Validation**
- [ ] All 4 themes work correctly
- [ ] Mobile responsive design functions
- [ ] Radio stations can be created and played
- [ ] Search functionality works
- [ ] Auto-fill system operates properly
- [ ] Settings persist across container restarts
- [ ] Last.fm integration works (if configured)

### **Step 5.3: Documentation Verification**
- [ ] Setup process works from README alone
- [ ] All configuration options documented
- [ ] Troubleshooting guide is helpful
- [ ] Docker commands work as documented

---

## 📊 **Timeline & Effort Estimate**

| Phase | Tasks | Time Estimate |
|-------|--------|---------------|
| **Phase 1** | Backup & freeze current version | 1 hour |
| **Phase 2** | Fresh system setup & cleanup | 2-3 hours |
| **Phase 3** | Docker implementation | 1-2 days |
| **Phase 4** | GitHub release packaging | 4-6 hours |
| **Phase 5** | Testing & validation | 1 day |

**Total Estimate**: 3-4 days for complete Docker release

## ✅ **Success Criteria**

1. **User Experience**: New user can install with one command
2. **Feature Parity**: All current features work in Docker
3. **Documentation**: Complete guides for installation and usage
4. **Reliability**: Services start correctly and stay running
5. **Security**: No personal data or admin features in release
6. **Portability**: Works on different Linux distributions

---

## 📋 **Next Steps Checklist**

### **When Ready to Start:**
- [ ] Create release candidate backup
- [ ] Set up fresh system/VM
- [ ] Extract and begin cleanup process
- [ ] Follow this plan step by step
- [ ] Test thoroughly before GitHub release

**This plan ensures a professional, user-ready Docker release while protecting your working system.**

---

*Created: November 17, 2025 - Ready for implementation when version freeze is desired*