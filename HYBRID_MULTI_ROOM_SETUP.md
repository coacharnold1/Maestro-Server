# Hybrid Multi-Room Audio Setup
## Synchronized OR Independent Playback

This guide documents a flexible multi-room audio architecture that supports **both** synchronized and independent playback modes without external dependencies like Snapcast.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     MASTER SERVER                            │
│  - Maestro MPD Server with full library                     │
│  - NFS export of music directory                            │
│  - HTTP streaming enabled (for sync mode)                   │
│  - Database available for sync                              │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │                   │
        ┌───────────▼─────┐   ┌────────▼──────┐
        │  CLIENT PI #1   │   │  CLIENT PI #2  │
        │                 │   │                │
        │  Local MPD      │   │  Local MPD     │
        │  + MPV Player   │   │  + MPV Player  │
        │  + NFS Mount    │   │  + NFS Mount   │
        └─────────────────┘   └────────────────┘
```

### Two Playback Modes

**Mode 1: Synchronized Playback (Party Mode)**
- All clients connect via MPV to master's HTTP stream
- Same music plays in all rooms simultaneously
- Lower quality (MP3 192kbps) but perfectly synchronized
- Controlled from master Maestro web interface
- Use case: Parties, whole-house audio events

**Mode 2: Independent Playback (Normal Use)**
- Each client runs local MPD connected to NFS library
- Bit-perfect FLAC playback from original files
- Each room plays different music independently
- Each room can have its own Maestro web interface
- Use case: Daily listening, different music per room

## Benefits

✅ **Flexibility**: Switch between modes as needed  
✅ **No External Dependencies**: Pure MPD/MPV solution  
✅ **Bit-Perfect Audio**: When using independent mode  
✅ **Perfect Sync**: When using party mode  
✅ **Simple Architecture**: All built on proven tools  
✅ **Low Bandwidth**: Independent mode only reads files once  

---

## Master Server Setup

Your existing Maestro server needs minimal changes:

### 1. Enable NFS Export

Edit `/etc/exports`:

```bash
/media/music 192.168.1.0/24(ro,sync,no_subtree_check,no_root_squash)
```

Apply changes:
```bash
sudo exportfs -ra
sudo systemctl restart nfs-kernel-server
```

### 2. Enable HTTP Streaming

**Option A: Via Maestro Admin UI**
1. Navigate to `http://your-server:5004`
2. Go to **Audio Tweaks**
3. Enable **HTTP Streaming Configuration**
4. Use default settings (port 8000, LAME encoder, 192kbps)

**Option B: Manual Configuration**

Edit `/etc/mpd.conf`, add:

```conf
audio_output {
    type        "httpd"
    name        "Maestro HTTP Stream"
    encoder     "lame"
    port        "8000"
    bitrate     "192"
    format      "44100:16:2"
    max_clients "0"
    bind_to_address "0.0.0.0"
}
```

Restart MPD:
```bash
sudo systemctl restart mpd
```

### 3. Allow Firewall Access

```bash
sudo ufw allow 2049/tcp  # NFS
sudo ufw allow 8000/tcp  # HTTP stream
sudo ufw allow 6600/tcp  # MPD
```

---

## Client Pi Setup

Each client Raspberry Pi needs both MPD and MPV installed.

### Hardware Requirements

**Minimum:**
- Raspberry Pi 3A+, Zero 2 W, or better
- 8GB+ SD card (for OS only, no music storage needed)
- USB DAC (optional but recommended)
- Wired Ethernet preferred (WiFi works but higher latency)

**Recommended:**
- Raspberry Pi 4 (2GB RAM) - $45
- 32GB SD card for headroom
- Quality USB DAC for best audio

### Software Installation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y mpd mpc mpv nfs-common alsa-utils

# Stop default MPD (we'll configure it)
sudo systemctl stop mpd
sudo systemctl disable mpd
```

### NFS Mount Setup

Create mount point:
```bash
sudo mkdir -p /media/music
```

Edit `/etc/fstab`, add:
```
192.168.1.XXX:/media/music  /media/music  nfs  ro,vers=4,hard,intr,rsize=8192,wsize=8192,timeo=14  0  0
```
*(Replace `192.168.1.XXX` with your master server IP)*

Mount it:
```bash
sudo mount -a
```

Verify:
```bash
ls /media/music
# Should show your music library
```

### MPD Configuration (Independent Mode)

Edit `/etc/mpd.conf`:

```conf
# Basic MPD Configuration for Client
music_directory     "/media/music"
playlist_directory  "/var/lib/mpd/playlists"
db_file             "/var/lib/mpd/database"
log_file            "/var/log/mpd/mpd.log"
pid_file            "/run/mpd/pid"
state_file          "/var/lib/mpd/state"
sticker_file        "/var/lib/mpd/sticker.sql"

# Bind to localhost + network
bind_to_address     "localhost"
bind_to_address     "0.0.0.0"
port                "6600"

# User and permissions
user                "mpd"
group               "audio"

# Input cache (important for NFS)
input {
    plugin "curl"
}

# Audio output to your DAC
audio_output {
    type            "alsa"
    name            "My USB DAC"
    device          "hw:1,0"        # Adjust for your DAC
    mixer_type      "hardware"
    mixer_device    "default"
    mixer_control   "PCM"
    auto_resample   "no"
    auto_channels   "no"
    auto_format     "no"
    dop             "no"
}

# Disable resampling for bit-perfect
replaygain          "off"
volume_normalization "no"
```

**Find your DAC device:**
```bash
aplay -l
# Look for your USB DAC, typically hw:1,0 or hw:2,0
```

### Create Systemd Services

#### Service 1: Independent Mode (Local MPD)

Create `/etc/systemd/system/maestro-client-independent.service`:

```ini
[Unit]
Description=Maestro Client - Independent Mode (Local MPD)
After=network.target nfs-client.target
Requires=nfs-client.target
Conflicts=maestro-client-sync.service

[Service]
Type=forking
ExecStartPre=/bin/sleep 3
ExecStart=/usr/bin/mpd /etc/mpd.conf
ExecStop=/usr/bin/mpd --kill
User=mpd
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Service 2: Sync Mode (HTTP Streaming)

Create `/etc/systemd/system/maestro-client-sync.service`:

```ini
[Unit]
Description=Maestro Client - Sync Mode (HTTP Stream)
After=network.target
Conflicts=maestro-client-independent.service

[Service]
Type=simple
User=pi
ExecStartPre=/usr/bin/systemctl stop maestro-client-independent || true
ExecStartPre=/usr/bin/mpd --kill || true
ExecStart=/usr/bin/mpv --no-video --audio-device=alsa/hw:1,0 http://192.168.1.XXX:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```
*(Replace `192.168.1.XXX` with your master server IP and adjust audio device)*

### Enable Default Mode

Choose which mode should start on boot:

**For Independent Mode (Recommended Default):**
```bash
sudo systemctl daemon-reload
sudo systemctl enable maestro-client-independent
sudo systemctl start maestro-client-independent
```

**For Sync Mode:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable maestro-client-sync
sudo systemctl start maestro-client-sync
```

---

## Switching Between Modes

### Method 1: SSH Command (Simple)

**Switch to Sync Mode:**
```bash
sudo systemctl stop maestro-client-independent
sudo systemctl start maestro-client-sync
```

**Switch to Independent Mode:**
```bash
sudo systemctl stop maestro-client-sync
sudo systemctl start maestro-client-independent
```

### Method 2: Create Helper Scripts

Create `/usr/local/bin/switch-to-sync`:
```bash
#!/bin/bash
sudo systemctl stop maestro-client-independent
sudo systemctl start maestro-client-sync
echo "Switched to SYNC mode - streaming from master"
```

Create `/usr/local/bin/switch-to-independent`:
```bash
#!/bin/bash
sudo systemctl stop maestro-client-sync
sudo systemctl start maestro-client-independent
echo "Switched to INDEPENDENT mode - playing from local MPD"
```

Make executable:
```bash
sudo chmod +x /usr/local/bin/switch-to-sync
sudo chmod +x /usr/local/bin/switch-to-independent
```

Usage:
```bash
switch-to-sync
# or
switch-to-independent
```

### Method 3: Web Interface Toggle (Future Enhancement)

A web interface could be added to Maestro Admin that:
1. Discovers client Pis on the network
2. Shows current mode for each client
3. Provides one-click toggle between modes
4. Uses SSH to execute systemctl commands on clients

*(This would be a future feature to implement)*

---

## Initial Database Build (Independent Mode)

When first starting independent mode, MPD needs to scan the NFS library:

```bash
# SSH into client Pi
mpc update

# Monitor progress
watch -n 1 'mpc stats'
```

**Note:** Only the first scan takes time (5-30 minutes depending on library size). After that, updates are fast.

### Sync Database from Master (Optional Advanced)

Instead of each client scanning independently, you can copy the master's database:

```bash
# On master server
sudo systemctl stop mpd
sudo scp /var/lib/mpd/database pi@CLIENT_IP:/tmp/
sudo systemctl start mpd

# On each client
sudo systemctl stop maestro-client-independent
sudo mv /tmp/database /var/lib/mpd/database
sudo chown mpd:audio /var/lib/mpd/database
sudo systemctl start maestro-client-independent
```

This is instant and ensures all clients have identical library views.

---

## Testing & Verification

### Test Independent Mode

```bash
# On client Pi
mpc status
mpc listall | head -20  # Should see your library
mpc random
mpc play
```

Browse to `http://CLIENT_IP:6600` with any MPD client to control.

### Test Sync Mode

```bash
# On client Pi
sudo systemctl status maestro-client-sync
# Should show mpv running and connected to master stream

# On master server, play something
# All sync-mode clients should play the same audio
```

### Test Audio Output

```bash
# Play test tone through ALSA
speaker-test -D hw:1,0 -c 2 -t wav

# Check ALSA devices
aplay -l
```

---

## Network Considerations

### Bandwidth Usage

**Independent Mode:**
- FLAC streaming from NFS: ~1 Mbps per client (only when playing)
- Minimal when paused/stopped
- 10 clients playing simultaneously: ~10 Mbps

**Sync Mode:**
- MP3 stream from master: ~0.2 Mbps per client
- 10 clients: ~2 Mbps total
- More efficient for many simultaneous clients

### Latency

**Independent Mode:**
- NFS read latency: 1-5ms (wired), 10-50ms (WiFi)
- Imperceptible during playback
- Buffering handles any network hiccups

**Sync Mode:**
- HTTP buffering: 1-3 seconds initial buffer
- Perfect sync between clients after buffer fills
- Slight delay between master button press and audio change

### WiFi vs Ethernet

**Ethernet (Recommended):**
- Stable, low latency
- Bit-perfect reliability
- Multiple simultaneous clients no problem

**WiFi (Works but...):**
- Higher latency (still acceptable)
- Occasional buffer underruns possible
- Use 5GHz for best results
- Limit simultaneous clients to 5-6

---

## Maestro Web Interface on Clients

You can optionally install Maestro web interface on each client for local control:

```bash
# On client Pi
git clone https://github.com/coacharnold1/Maestro-Server.git
cd Maestro-Server

# Minimal web-only install
sudo apt install python3-mpd2 python3-flask python3-flask-socketio
sudo cp app.py /home/pi/maestro-web/
sudo cp -r templates static /home/pi/maestro-web/

# Create systemd service for web interface
# (Similar to maestro-web.service on master)
```

Then each room can be controlled independently via:
- Master server: `http://master-ip:5003` (controls all sync-mode clients)
- Client 1: `http://client1-ip:5003` (independent control)
- Client 2: `http://client2-ip:5003` (independent control)

---

## Troubleshooting

### NFS Mount Issues

**Problem:** Mount fails or hangs
```bash
# Check NFS server is running on master
systemctl status nfs-kernel-server

# Check exports on master
showmount -e MASTER_IP

# Test mount manually
sudo mount -t nfs -o vers=4 MASTER_IP:/media/music /media/music

# Check firewall
sudo ufw status
```

### MPD Won't Start

**Problem:** MPD fails to start in independent mode
```bash
# Check logs
sudo journalctl -u maestro-client-independent -n 50

# Common issues:
# 1. NFS not mounted yet - increase ExecStartPre sleep time
# 2. Database corruption - delete /var/lib/mpd/database and rescan
# 3. Permissions - ensure mpd user can read NFS mount
```

### No Audio Output

**Problem:** MPD plays but no sound
```bash
# Check ALSA device
aplay -l

# Update mpd.conf with correct device
# Test with speaker-test
speaker-test -D hw:1,0 -c 2

# Check MPD can access audio group
groups mpd
# Should include 'audio'
```

### Sync Mode Not Working

**Problem:** MPV can't connect to stream
```bash
# Check master's HTTP stream is enabled
curl http://MASTER_IP:8000
# Should return HTTP response

# Test stream manually
mpv http://MASTER_IP:8000

# Check firewall on master
sudo ufw allow 8000/tcp
```

---

## Performance Tips

### Optimize NFS for Audio

Add these mount options in `/etc/fstab`:
```
rsize=8192,wsize=8192,timeo=14,intr
```

### Reduce MPD Memory Usage

In `/etc/mpd.conf`:
```conf
audio_buffer_size   "4096"  # Default is 4096, can reduce to 2048
buffer_before_play  "10%"   # Start playback sooner
```

### Optimize Network

**On client Pi:**
```bash
# Disable WiFi power management
sudo iw dev wlan0 set power_save off

# Increase network buffer sizes
sudo sysctl -w net.core.rmem_max=16777216
sudo sysctl -w net.core.wmem_max=16777216
```

---

## Use Cases

### Scenario 1: Dinner Party
**Setup:** All rooms in sync mode  
**Control:** Master Maestro web interface  
**Audio:** Same playlist throughout house  
**Mode Switch:** Run `switch-to-sync` on all clients before party

### Scenario 2: Normal Evening
**Setup:** All rooms in independent mode  
**Control:** Each room's own Maestro interface (or master for all)  
**Audio:** Kitchen plays jazz, bedroom plays audiobook, living room plays classical  
**Mode:** Default independent mode, no switching needed

### Scenario 3: Mixed Mode
**Setup:** Living room + kitchen in sync, bedroom independent  
**Control:** Sync rooms controlled from master, bedroom local  
**Audio:** Party in main area, kids sleeping in bedroom with different audio  
**Mode Switch:** Only switch living room + kitchen to sync mode

---

## Future Enhancements

### Potential Features to Add:

1. **Web UI for Mode Switching**
   - Admin panel showing all discovered clients
   - One-click mode toggle per client
   - Status indicator (sync/independent/offline)

2. **Automatic Client Discovery**
   - Scan network for Maestro clients
   - Auto-configure client list
   - Health monitoring

3. **Database Auto-Sync**
   - Master pushes database updates to clients
   - No manual database copying needed
   - Triggered after library updates

4. **Zone Grouping**
   - Define zones (e.g., "downstairs", "upstairs")
   - Switch entire zones to sync mode
   - Maintain sync between zone members

5. **Mobile App Integration**
   - Control mode switching from phone
   - See all room statuses
   - Quick scene presets ("Party Mode", "Independent Mode")

---

## Comparison Matrix

| Feature | Independent Mode | Sync Mode | Snapcast |
|---------|-----------------|-----------|----------|
| Audio Quality | Bit-perfect FLAC | MP3 192kbps | PCM (bit-perfect) |
| Sync Accuracy | N/A | ±100ms | <1ms |
| Bandwidth/Client | ~1 Mbps | ~0.2 Mbps | ~1.4 Mbps |
| Independent Playback | ✅ Yes | ❌ No | ❌ No |
| Per-Room Control | ✅ Yes | ❌ No | ❌ No |
| Setup Complexity | Medium | Easy | Hard |
| Dependencies | NFS + MPD | MPV only | Snapcast server/client |
| Our Code | ✅ Yes | ✅ Yes | ❌ External |

---

## Summary

This hybrid architecture gives you the best of both worlds:

✅ **Bit-perfect audio** when you want quality  
✅ **Synchronized playback** when you want party mode  
✅ **Simple switching** between modes  
✅ **All your own code** - no external dependencies  
✅ **Flexible** - works with 2 rooms or 20  

The key insight: You don't need Snapcast for synchronized playback if you're willing to accept MP3 quality during parties. For critical listening (independent mode), each room gets full bit-perfect FLAC.

**Recommended Default Setup:**
- Independent mode as default (best quality)
- Quick switch to sync mode for parties/events
- Master Maestro controls everything

Start with 2-3 client Pis and expand as needed. Total cost per room: ~$60 (Pi + DAC + SD card).
