# NFS Monitoring & Health Check Guide

## Overview
Automated monitoring of all 8 NFS mounts from server 192.168.1.110

## Quick Commands

### View Current Status
```bash
~/Maestro-Server/scripts/nfs-health-report.sh
```
Shows real-time status of all NFS mounts with color-coded output.

### View Health Log
```bash
sudo tail -f /var/log/maestro-nfs-health.log
```
Watch the monitoring log in real-time.

### Manual Health Check
```bash
sudo /home/fausto/Maestro-Server/scripts/nfs-health-check.sh
```
Run an immediate health check (also runs automatically every 5 minutes).

### Check Monitoring Schedule
```bash
sudo systemctl list-timers nfs-health-check.timer
```
Shows when the next automatic check will run.

### View Recent Check Results
```bash
sudo journalctl -u nfs-health-check.service -n 50
```
View systemd journal entries for the health check service.

## Automatic Monitoring

**Service:** `nfs-health-check.service`  
**Timer:** `nfs-health-check.timer`  
**Frequency:** Every 5 minutes  
**First Run:** 2 minutes after boot

### Control the Service
```bash
# Stop monitoring
sudo systemctl stop nfs-health-check.timer

# Start monitoring
sudo systemctl start nfs-health-check.timer

# Disable (won't start at boot)
sudo systemctl disable nfs-health-check.timer

# Enable (start at boot)
sudo systemctl enable nfs-health-check.timer

# Check status
sudo systemctl status nfs-health-check.timer
```

## What Gets Monitored

1. **NFS Server Reachability** (192.168.1.110)
2. **Mount Status** for all 8 music shares:
   - /media/music/mrbig
   - /media/music/borris
   - /media/music/natasha
   - /media/music/gidney
   - /media/music/cloyd
   - /media/music/bullwinkle
   - /media/music/rocky
   - /media/music/down
3. **Access Test** (can we actually read the mount?)
4. **Stale Handle Detection**
5. **NFS Statistics** (retransmissions, timeouts)

## Log Files

**Main Log:** `/var/log/maestro-nfs-health.log`  
**Alert Flag:** `/tmp/nfs-alert-needed` (created when issues detected)

### Log Entry Types
- `INFO:` Normal operation, all healthy
- `WARNING:` Minor issues detected (e.g., stale handles)
- `ERROR:` Serious issues (mount not accessible, server unreachable)

## Troubleshooting

### If NFS Server is Down
```bash
# Check network connectivity
ping 192.168.1.110

# Check from NFS server side (if you have access)
ssh user@192.168.1.110
sudo systemctl status nfs-server
```

### If a Mount is Stale
```bash
# Remount the specific share (example: bullwinkle)
sudo umount /media/music/bullwinkle
sudo mount /media/music/bullwinkle

# Or remount all
sudo umount /media/music/*
sudo mount -av
```

### If Getting Too Many Alerts
Adjust check frequency in `/etc/systemd/system/nfs-health-check.timer`:
```ini
OnUnitActiveSec=15min  # Change from 5min to 15min
```
Then reload: `sudo systemctl daemon-reload && sudo systemctl restart nfs-health-check.timer`

## Current NFS Mount Settings

- **Timeout:** 60 seconds (timeo=600)
- **Retries:** 3 attempts (retrans=3)
- **Mode:** Soft mount (fails gracefully instead of hanging)
- **Caching:** 3 second attribute cache (actimeo=3)
- **Server:** 192.168.1.110
- **Client IP:** 192.168.1.142

## Integration with Maestro

The monitoring runs independently but logs all issues. MPD service is configured to:
- Wait for NFS mounts at startup
- Restart on failure (with 10s delay)
- Handle stale mounts gracefully

See: `/etc/systemd/system/mpd.service.d/nfs-wait.conf`

## Future Enhancements

To add email/notification alerts, edit `/home/fausto/Maestro-Server/scripts/nfs-health-check.sh` 
and add notification commands when `$ALERT_FILE` is created.
