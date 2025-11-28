# Docker Deployment Plan for MPD Web Control

## 📅 **Updated: November 17, 2025 - Desert Theme & Mobile Optimizations**

### 🎨 **New Features Since Last Update**
- **Desert Theme**: Complete 4th theme option (Dark/Light/High Contrast/Desert)
- **Mobile Optimizations**: Responsive footer design, fixed input overflows
- **UI Consistency**: Standardized border-radius values, improved mobile controls
- **Enhanced Templates**: All 15+ templates updated with complete theming

### 📁 **Current Project Structure**
```
mpd_web_control_combined_20251104_180921/
├── 🐍 Core Application
│   ├── app.py                    # Main Flask application
│   ├── requirements.txt          # Python dependencies
│   └── rudimentary_search.py     # Search functionality
├── ⚙️ Configuration & Setup
│   ├── config.env.example        # Environment template
│   ├── config.env               # Local configuration (gitignored)
│   ├── setup.sh                 # Virtual environment setup
│   ├── start_app.sh             # Service startup script
│   └── install_service.sh       # systemd service installer
├── 💾 Data & Storage
│   ├── settings.json            # User preferences & theme selection
│   ├── radio_stations.json      # Saved genre combinations
│   ├── backup.sh               # Backup management script
│   └── backups/                # Auto-managed backup retention
├── 🎨 Frontend
│   ├── templates/              # 15+ HTML templates with 4 themes
│   │   ├── index.html          # Main dashboard
│   │   ├── playlist.html       # Queue management
│   │   ├── add_music.html      # Random music & radio stations
│   │   ├── search*.html        # Search functionality
│   │   ├── browse_*.html       # Music library browsing
│   │   ├── charts.html         # Last.fm integration
│   │   └── base_layout.html    # Settings page
│   └── static/                 # CSS, JS, images
│       └── manifest.json       # PWA manifest
├── 📚 Documentation
│   ├── README.md               # User guide & features
│   ├── FIXES.md               # Changelog & version history
│   ├── DEPLOYMENT.md          # Standard deployment guide
│   ├── DOCKER_DEPLOYMENT_PLAN.md  # This file
│   └── docs/                  # Additional documentation
└── 🔧 Runtime
    ├── __pycache__/           # Python cache (excluded from backups)
    └── venv/                  # Virtual environment (excluded)
```

## 🔒 **Security Cleanup for Public Deployment**

### 🚨 **Items to Remove/Secure**

#### 1. **Theme System Considerations**
- **4 Complete Themes**: Dark, Light, High Contrast, Desert (all production-ready)
- **Mobile Responsive**: All themes work on mobile with proper footer handling
- **Settings Storage**: Theme preferences stored in settings.json (needs volume persistence)
- **Default Theme**: Should be configurable via environment variable

#### 2. **Radio Stations Feature**
- **Data Persistence**: radio_stations.json needs volume mounting
- **Genre Dependencies**: Requires access to MPD music database for genre enumeration
- **Auto-Fill Integration**: Complex playlist management system needs testing in container

#### 3. **Last.fm Integration**
- **API Keys**: Already externalized to environment variables (LASTFM_API_KEY, LASTFM_SHARED_SECRET)
- **Session Storage**: Last.fm session tokens stored in settings.json
- **Chart Functionality**: Needs network access for Last.fm API calls

#### 4. **File System Dependencies**
- **Album Art**: Requires read access to music files for embedded artwork
- **Search Index**: MPD database access for search functionality
- **Recent Albums**: Scans music directory for recent additions
- **Cache Management**: Album art cache needs writable volume

#### 5. **MPD Config App References (Port 5000)** - TO REMOVE
- Remove "Maestro Config" button from index.html
- Strip out any admin/configuration links  
- Remove references in templates and backend routes

#### 6. **Hardcoded Directory Paths** - TO CONFIGURE
- Make music directories configurable via environment variables
- Remove any system-specific path references
- Add validation for directory existence during startup

### 🐳 **Docker Deployment Strategy**

#### **Version Variants**
```
├── Personal Version (Current)
│   ├── Full admin features
│   ├── Maestro Config integration
│   └── Development settings
│
└── Public/Docker Version (Future)
    ├── Stripped admin features
    ├── Environment-based config
    └── Production hardening
```

#### **Installation Script Features**
```bash
# docker-setup.sh (Future Project)
#!/bin/bash

# 1. Environment Setup
echo "Setting up MPD Web Control Docker deployment..."

# 2. Secrets Management
read -s -p "Enter Last.fm API Key (optional): " LASTFM_KEY
read -s -p "Enter Last.fm Secret (optional): " LASTFM_SECRET

# 3. Recent Albums Configuration
echo ""
echo "Recent Albums Configuration:"
echo "Enter directories to scan for recent albums (comma-separated)"
echo "Example: downloads,new_music,staging"
echo "Leave empty to scan entire music library (slower)"
read -p "Recent Albums Directories: " RECENT_DIRS

# 4. Configuration Generation
cat > .env << EOF
LASTFM_API_KEY=$LASTFM_KEY
LASTFM_SECRET=$LASTFM_SECRET
MPD_HOST=host.docker.internal
MPD_PORT=6600
RECENT_ALBUMS_DIRS=$RECENT_DIRS
FLASK_ENV=production
EOF

# 4. Security Hardening
docker-compose up --build -d
```

#### **Docker Compose Structure**
```yaml
# docker-compose.yml (Future)
version: '3.8'
services:
  mpd-web:
    build: .
    ports:
      - "5003:5003"
    environment:
      - LASTFM_API_KEY=${LASTFM_API_KEY}
      - LASTFM_SECRET=${LASTFM_SECRET}
      - MPD_HOST=${MPD_HOST:-host.docker.internal}
      - MPD_PORT=${MPD_PORT:-6600}
      - MUSIC_DIRECTORY=${MUSIC_DIRECTORY}
      - APP_PORT=${APP_PORT:-5003}
      - APP_HOST=${APP_HOST:-0.0.0.0}
    volumes:
      - ./cache:/app/cache
      - ./settings.json:/app/settings.json
      - ./radio_stations.json:/app/radio_stations.json
      - type: bind
        source: ${MUSIC_DIRECTORY}
        target: /music
        read_only: true
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5003/api/status"]
    depends_on:
      - mpd
  
  mpd:
    image: musicpd/mpd:latest
    volumes:
      - ./mpd.conf:/etc/mpd.conf
      - type: bind
        source: ${MUSIC_DIRECTORY}
        target: /music
        read_only: true
      - mpd_db:/var/lib/mpd
    ports:
      - "6600:6600"  # Expose MPD port
    restart: unless-stopped
    
volumes:
  mpd_db:
```

#### **Production Dockerfile**
```dockerfile
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1001 mpd-web && \
    mkdir -p /app/cache /app/static && \
    chown -R mpd-web:mpd-web /app

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=mpd-web:mpd-web . .

# Switch to non-root user
USER mpd-web

# Create necessary directories
RUN mkdir -p /app/cache

# Expose port
EXPOSE 5003

# Health check using internal status endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:5003/api/status || exit 1

# Run application
CMD ["python", "app.py"]
```

### 📋 **Future Project Checklist**

#### **Phase 1: Security Audit** 
- [ ] Remove all admin/config references
- [ ] Externalize all secrets to environment variables
- [ ] Add production security headers
- [ ] Remove debug endpoints
- [ ] Audit file system access permissions
- [ ] Remove any hardcoded paths or system-specific references

#### **Phase 2: Docker Preparation**
- [ ] Create production Dockerfile
- [ ] Docker compose with proper networking
- [ ] Health checks and restart policies
- [ ] Volume management for cache/data
- [ ] Multi-stage build for smaller image size
- [ ] Non-root user execution

#### **Phase 3: Installation Automation**
- [ ] Interactive setup script
- [ ] Secrets management
- [ ] MPD connectivity validation
- [ ] Production configuration templates
- [ ] Documentation for deployment
- [ ] Example environment files

#### **Phase 4: Production Hardening**
- [ ] Security headers (HTTPS, CSP, etc.)
- [ ] Rate limiting
- [ ] Input validation and sanitization
- [ ] Logging and monitoring setup
- [ ] Resource limits and constraints
- [ ] Backup and recovery procedures

### 🔧 **Required Code Changes**

#### **Environment Variable Integration**
```python
# app.py modifications needed
import os
from dotenv import load_dotenv

load_dotenv()

# Current config.env structure:
MPD_HOST = os.getenv('MPD_HOST', 'localhost')
MPD_PORT = int(os.getenv('MPD_PORT', 6600))
MUSIC_DIRECTORY = os.getenv('MUSIC_DIRECTORY', '/music')

# Web Application Settings
APP_PORT = int(os.getenv('APP_PORT', 5003))
APP_HOST = os.getenv('APP_HOST', '0.0.0.0')

# Last.fm API (Optional)
LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_SHARED_SECRET = os.getenv('LASTFM_SHARED_SECRET')

# Auto-Fill Settings
AUTO_FILL_ENABLED = os.getenv('AUTO_FILL_ENABLED', 'true').lower() == 'true'
AUTO_FILL_MIN_TRACKS = int(os.getenv('AUTO_FILL_MIN_TRACKS', 3))
AUTO_FILL_MAX_TRACKS = int(os.getenv('AUTO_FILL_MAX_TRACKS', 7))

# Theme Settings (stored in settings.json, fallback to env)
DEFAULT_THEME = os.getenv('DEFAULT_THEME', 'dark')  # dark, light, high-contrast, desert

# Update get_recent_albums_from_mpd function
def get_recent_albums_from_mpd(limit=25, force_refresh=False):
    directories_to_check = recent_dirs if recent_dirs else ['']  # Empty string = scan all
```

#### **Enhanced docker-setup.sh Script**
```bash
#!/bin/bash
set -e

echo "🎵 MPD Web Control - Docker Setup"
echo "=================================="

# 1. Create .env file
cat > .env << 'EOF'
# MPD Configuration
MPD_HOST=mpd
MPD_PORT=6600
MUSIC_DIRECTORY=/path/to/your/music

# Web Application
APP_PORT=5003
APP_HOST=0.0.0.0

# Theme Settings (dark, light, high-contrast, desert)
DEFAULT_THEME=dark

# Auto-Fill Settings
AUTO_FILL_ENABLED=true
AUTO_FILL_MIN_TRACKS=3
AUTO_FILL_MAX_TRACKS=7

# Last.fm API (Optional - leave empty to disable)
LASTFM_API_KEY=
LASTFM_SHARED_SECRET=

# Production Settings
FLASK_ENV=production
EOF

# 2. Interactive Configuration
echo ""
echo "📁 Music Directory Configuration:"
read -p "Enter path to your music directory: " MUSIC_DIR
sed -i "s|MUSIC_DIRECTORY=.*|MUSIC_DIRECTORY=$MUSIC_DIR|" .env

echo ""
echo "🎨 Default Theme Selection:"
echo "1) Dark (default)"
echo "2) Light" 
echo "3) High Contrast"
echo "4) Desert"
read -p "Choose theme (1-4): " THEME_CHOICE

case $THEME_CHOICE in
    2) sed -i "s|DEFAULT_THEME=.*|DEFAULT_THEME=light|" .env ;;
    3) sed -i "s|DEFAULT_THEME=.*|DEFAULT_THEME=high-contrast|" .env ;;
    4) sed -i "s|DEFAULT_THEME=.*|DEFAULT_THEME=desert|" .env ;;
    *) echo "Using default dark theme" ;;
esac

echo ""
echo "🎵 Last.fm Integration (Optional):"
read -p "Enter Last.fm API Key (leave empty to skip): " LASTFM_KEY
if [ ! -z "$LASTFM_KEY" ]; then
    read -s -p "Enter Last.fm Shared Secret: " LASTFM_SECRET
    echo ""
    sed -i "s|LASTFM_API_KEY=.*|LASTFM_API_KEY=$LASTFM_KEY|" .env
    sed -i "s|LASTFM_SHARED_SECRET=.*|LASTFM_SHARED_SECRET=$LASTFM_SECRET|" .env
fi

# 3. Validate Music Directory
if [ ! -d "$MUSIC_DIR" ]; then
    echo "⚠️  Warning: Music directory '$MUSIC_DIR' does not exist"
    echo "   Make sure to create it before starting the containers"
fi

# 4. Start Services
echo ""
echo "🚀 Starting MPD Web Control..."
docker-compose up -d

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Web Interface: http://localhost:5003"
echo "🎛️  MPD Port: localhost:6600"
echo ""
echo "📋 Management Commands:"
echo "  View logs:     docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart:       docker-compose restart"
echo ""
echo "🎨 Available Themes: Dark • Light • High Contrast • Desert"
```

#### **Template Modifications**
```html
<!-- Remove from index.html -->
{% if maestro_config_url %}
<div class="controls mpd-actions-small">
    <h3>System Configuration</h3>
    <div class="small-actions">
        <a href="{{ maestro_config_url }}" target="_blank"><button class="small-btn">Maestro Config</button></a>
    </div>
</div>
{% endif %}
```

### 🎯 **Key Benefits of This Approach**

1. **Clean separation** between personal and public versions
2. **Zero secrets** in the container image
3. **Easy deployment** with guided setup
4. **Production hardening** built-in
5. **Maintainable** - can merge security updates from personal version
6. **Portable** - runs on any Docker host
7. **Scalable** - easy to add reverse proxy, SSL, monitoring

### 🚀 **Deployment Options**

#### **Option A: Connect to Host MPD (Simplest)**
- Container connects to MPD running on host
- Minimal changes required
- Good for single-server deployments

#### **Option B: Multi-Container Setup**
- Separate MPD container + Web app container
- More complex but fully containerized
- Better for cloud/Kubernetes deployments

#### **Option C: All-in-One Container**
- MPD + Web app in single container
- Easiest for end users
- Requires more setup but most portable

### 📝 **Documentation Requirements**

#### **User Documentation**
- [ ] Installation guide
- [ ] Configuration options
- [ ] Troubleshooting guide
- [ ] Security considerations

#### **Developer Documentation**
- [ ] Build instructions
- [ ] Development environment setup
- [ ] API documentation
- [ ] Contributing guidelines

---

## 🚀 **Current Project Status & Implementation Timeline**

### ✅ **Already Completed (November 2025)**
- **Complete Theme System**: 4 themes (Dark/Light/High Contrast/Desert) fully implemented
- **Mobile Responsive**: All templates optimized for mobile devices
- **Environment Configuration**: config.env system ready for containerization
- **Radio Stations**: Advanced genre-based playlist system
- **Settings Persistence**: JSON-based user preferences storage
- **Backup System**: Automated backup/restore with retention policies
- **Auto-Fill System**: Intelligent playlist management with configurable parameters
- **Last.fm Integration**: Charts and scrobbling with external API key management

### 🔧 **Ready for Docker Implementation**

#### **Phase 1: Security & Environment Prep** (1-2 days)
- [x] Environment variable system already implemented
- [ ] Remove hardcoded admin references (Maestro Config button)
- [ ] Audit and remove any debug endpoints
- [x] Last.fm API keys already externalized
- [x] Music directory configuration system in place
- [x] Production-ready theme system complete

#### **Phase 2: Containerization** (2-3 days)  
- [ ] Create multi-stage Dockerfile
- [ ] Docker compose with MPD + web app services
- [ ] Volume management for persistent data (settings.json, radio_stations.json)
- [ ] Network configuration for MPD connectivity
- [ ] Health checks and restart policies
- [x] Requirements.txt already optimized

#### **Phase 3: Installation Automation** (1-2 days)
- [ ] Interactive docker-setup.sh script
- [ ] Environment file generation
- [ ] MPD configuration templates
- [ ] First-run setup automation
- [ ] Backup/restore procedures for containers

#### **Phase 4: Production Hardening** (2-3 days)
- [ ] Security headers and CSP
- [ ] Non-root user execution
- [ ] Resource limits and constraints
- [ ] Logging and monitoring integration
- [ ] Production configuration validation

#### **Phase 5: Documentation & Testing** (1-2 days)
- [ ] Docker deployment guide
- [ ] Troubleshooting documentation
- [ ] Performance optimization guide
- [ ] Multi-architecture support (ARM64/AMD64)

### 🎯 **Key Docker Advantages**

1. **Complete Theme System**: All 4 themes work out-of-the-box
2. **Mobile Ready**: Responsive design already implemented
3. **Feature Complete**: Radio stations, auto-fill, search all containerizable
4. **Settings Persistence**: User preferences survive container restarts
5. **External Configuration**: Already environment-variable driven
6. **Backup System**: Can be adapted for container volume backup
7. **Health Monitoring**: Status endpoints ready for container health checks

### 📊 **Updated Implementation Estimate**

- **Phase 1 (Security)**: 1-2 days *(mostly audit work)*
- **Phase 2 (Docker)**: 2-3 days *(containerization)*  
- **Phase 3 (Automation)**: 1-2 days *(setup scripts)*
- **Phase 4 (Hardening)**: 2-3 days *(security & performance)*
- **Phase 5 (Documentation)**: 1-2 days *(guides & testing)*

**Total Estimate**: ~1-2 weeks for production-ready Docker deployment

**Confidence Level**: HIGH - Most infrastructure already in place

---

*Last Updated: November 17, 2025 - Ready for Docker implementation with complete theme system and mobile optimizations*