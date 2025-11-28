# MPD Web Control Docker Deployment Options

## Quick Start Commands

### Option 1: Full Containerized Setup (Recommended for new users)
```bash
# Copy environment template
cp .env.example .env

# Edit .env to set your MUSIC_DIRECTORY
nano .env

# Start with containerized MPD
COMPOSE_PROFILES=with-mpd docker-compose up -d
```

### Option 2: Connect to Existing MPD Server
```bash
# Copy environment template  
cp .env.example .env

# Edit .env and set:
# MPD_HOST=host.docker.internal (for host MPD)
# MPD_HOST=192.168.1.100 (for remote MPD)
nano .env

# Start web app only
docker-compose up -d
```

### Option 3: One-Command Setup (Future)
```bash
# Interactive setup script (coming soon)
./setup.sh
```

## Available Docker Compose Profiles

| Profile | Services | Use Case |
|---------|----------|----------|
| (default) | web only | Connect to existing MPD |
| `with-mpd` | web + mpd | Full containerized setup |
| `full` | web + mpd | Alias for with-mpd |

## Environment Variables

### Required
- `MUSIC_DIRECTORY`: Path to your music library

### Optional
- `MPD_HOST`: MPD server location (default: mpd)
- `MPD_PORT`: MPD port (default: 6600) 
- `WEB_PORT`: Web interface port (default: 5003)
- `DEFAULT_THEME`: UI theme (dark/light/high-contrast/desert)
- `LASTFM_API_KEY`: Last.fm API key for charts/scrobbling
- `LASTFM_SHARED_SECRET`: Last.fm shared secret

## Volume Mounts

- `${MUSIC_DIRECTORY}:/music:ro` - Your music library (read-only)
- `./data:/app/data` - App data (settings, radio stations)
- `mpd_db:/var/lib/mpd` - MPD database (if using containerized MPD)
- `web_cache:/app/cache` - Album art cache

## Port Mapping

- `5003` - Web interface (configurable via WEB_PORT)
- `6600` - MPD server (if using containerized MPD)

## Health Checks

Both services include health checks:
- Web app: `/api/version` endpoint
- MPD: MPD ping command

## Data Persistence

Your settings and data are preserved across container restarts:
- User settings stored in `./data/settings.json`
- Radio stations in `./data/radio_stations.json`  
- MPD database in named volume
- Album art cache in named volume