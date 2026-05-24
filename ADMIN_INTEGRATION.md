# Admin API Integration Guide

The Maestro Admin API has been integrated into the main project.

## Directory Structure

```
Maestro-MPD-Control/
├── app.py                      # Main web UI (port 5003)
├── admin/                      # Admin API (port 5004)
│   ├── admin_api.py           # Flask admin server
│   ├── requirements.txt       # Admin dependencies
│   ├── templates/             # Admin HTML pages
│   │   ├── admin_home.html
│   │   ├── library_management.html
│   │   ├── audio_tweaks.html
│   │   └── system_admin.html
│   └── README.md
├── templates/                  # Web UI templates
├── static/                     # Web UI assets
└── install-maestro.sh         # Complete installer
```

## Quick Start

### Option 1: Fresh Installation (Recommended)

```bash
./install-maestro.sh
```

This installs everything to `~/maestro/` with systemd services.

### Option 2: Manual Setup

```bash
# Install web UI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py  # Runs on port 5003

# In another terminal, install admin API
cd admin
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 admin_api.py  # Runs on port 5004
```

## Services

Both services run independently:

- **Web UI (5003)**: Music player interface
- **Admin API (5004)**: System configuration

## Configuration Files

- `~/.config/maestro/mounts.json` - Network mount configurations
- `~/.config/maestro/audio.json` - Audio settings
- `/etc/mpd.conf` - MPD configuration

## Sudo Configuration

Required for system operations:

```bash
# /etc/sudoers.d/maestro
user ALL=(ALL) NOPASSWD: /usr/bin/apt
user ALL=(ALL) NOPASSWD: /usr/bin/systemctl
user ALL=(ALL) NOPASSWD: /sbin/shutdown
user ALL=(ALL) NOPASSWD: /bin/mount
user ALL=(ALL) NOPASSWD: /bin/umount
```

(Created automatically by installer)

## Linking Admin to Web UI

Add link in web UI navigation:

```python
# In app.py or base template
<a href="http://{{request.host.split(':')[0]}}:5004">Admin Panel</a>
```

## Development

Both services use Flask development server. For production, use:

- **gunicorn** (recommended)
- **waitress** 
- **uWSGI**

Example with gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5003 app:app
gunicorn -w 2 -b 0.0.0.0:5004 admin.admin_api:app
```
