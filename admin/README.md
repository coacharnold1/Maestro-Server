# Maestro Admin API

System administration and configuration interface for Maestro MPD Control.

## Features

- **System Monitoring**: Real-time CPU, RAM, disk, network stats
- **Library Management**: Configure NFS/SMB network mounts
- **Audio Configuration**: Audiophile-optimized MPD settings
- **System Administration**: OS updates, reboot control

## Ports

- Admin API: **5004**
- Web UI: **5003**
- MPD: **6600**

## Running

```bash
# Development
cd admin
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 admin_api.py
```

## Production

Use systemd service (created by installer):
```bash
sudo systemctl start maestro-admin
sudo systemctl enable maestro-admin
```

## Access

Open in browser: `http://localhost:5004`

## Pages

- `/` - Dashboard with system metrics
- `/library` - Library management (mounts, MPD library)
- `/audio` - Audio configuration and device scan
- `/system` - System updates and reboot

## API Endpoints

### System
- `GET /api/system/info` - System metrics
- `POST /api/system/update` - OS package update
- `POST /api/system/reboot` - System reboot

### Library
- `GET /api/library/mounts` - List configured mounts
- `POST /api/library/mounts` - Add new mount
- `POST /api/library/mounts/<id>/mount` - Mount share
- `POST /api/library/mounts/<id>/unmount` - Unmount share
- `DELETE /api/library/mounts/<id>` - Delete mount config
- `GET /api/library/mpd-info` - MPD library info
- `POST /api/library/update` - Trigger MPD library update

### Audio
- `GET /api/audio/devices` - Scan audio devices
- `GET /api/audio/config` - Get audio configuration
- `POST /api/audio/config` - Save audio configuration
- `POST /api/audio/system-tweaks` - Apply system optimizations
