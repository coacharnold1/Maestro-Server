# Maestro MPD Control v2.0 - Quick Reference

## Installation (Fresh Server)

```bash
git clone https://github.com/coacharnold1/Maestro-MPD-Control.git
cd Maestro-MPD-Control
./install-maestro.sh
```

## Service Management

```bash
sudo systemctl {start|stop|restart|status} maestro-web
sudo systemctl {start|stop|restart|status} maestro-admin
sudo systemctl {start|stop|restart|status} mpd
```

## View Logs

```bash
journalctl -u maestro-web -f
journalctl -u maestro-admin -f
journalctl -u mpd -f
```

## Access URLs

- Web UI: `http://YOUR_IP:5003`
- Admin API: `http://YOUR_IP:5004`
- MPD: `YOUR_IP:6600`

## Admin API Pages

| URL | Purpose |
|-----|---------|
| `/` | Dashboard - System monitoring |
| `/library` | Library management & mounts |
| `/audio` | Audio configuration |
| `/system` | System updates & reboot |

## Configuration Files

- `~/.config/maestro/mounts.json` - Network mounts
- `~/.config/maestro/audio.json` - Audio settings
- `/etc/mpd.conf` - MPD configuration
- `/etc/sudoers.d/maestro` - Sudo permissions

## Installation Directory

```
~/maestro/
├── web/          # Web UI (port 5003)
├── admin/        # Admin API (port 5004)
└── logs/         # Application logs
```

## Music Directory

Default: `/media/music`

Add music:
1. Copy files to `/media/music/`
2. Or add network shares via Admin API
3. Update library: `mpc update` or via Admin UI

## Troubleshooting

### Service won't start
```bash
sudo systemctl status maestro-{web|admin}
journalctl -u maestro-{web|admin} -n 50
```

### MPD connection failed
```bash
sudo systemctl status mpd
mpc status
sudo netstat -tlnp | grep 6600
```

### Audio device not found
```bash
sudo aplay -l
aplay -L
```

### Mount failed
```bash
sudo mount -t nfs server:/path /media/music/test
ping server_ip
```

## Common Commands

```bash
# Update MPD library
mpc update

# Check MPD status
mpc status

# Restart all services
sudo systemctl restart mpd maestro-web maestro-admin

# View all services
sudo systemctl status mpd maestro-web maestro-admin

# Check system audio
aplay -l                    # List devices
speaker-test -c 2           # Test stereo output

# Monitor system resources
htop
df -h                       # Disk usage
free -h                     # Memory usage
```

## File Structure Reference

```
Maestro-MPD-Control/
├── app.py                           # Web UI server
├── admin/
│   ├── admin_api.py                # Admin server
│   ├── requirements.txt
│   └── templates/                  # Admin pages
├── templates/                       # Web UI pages
├── static/                          # Web UI assets
├── install-maestro.sh              # Complete installer
├── test-integration.sh             # Integration test
├── README_NEW.md                   # User documentation
├── ADMIN_INTEGRATION.md            # Integration guide
└── INTEGRATION_SUMMARY.md          # Technical summary
```

## Default Ports

| Service | Port | Purpose |
|---------|------|---------|
| Web UI | 5003 | Music player interface |
| Admin API | 5004 | System management |
| MPD | 6600 | Music daemon |
| HTTP Stream | 8000 | Audio streaming |

## Requirements

- Ubuntu 20.04+ / Debian 11+ / Arch Linux
- 1GB RAM minimum (2GB+ recommended)
- Python 3.8+
- MPD 0.21+
- Network connectivity

## Support

- GitHub: https://github.com/coacharnold1/Maestro-MPD-Control
- Issues: https://github.com/coacharnold1/Maestro-MPD-Control/issues
