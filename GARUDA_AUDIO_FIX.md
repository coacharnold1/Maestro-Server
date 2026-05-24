# Garuda Linux Audio Configuration Fix

## Problem

On Garuda Linux, MPD audio playback to speakers doesn't work despite:
- Master volume being at 100%
- Audio devices being detected correctly
- Services starting without errors

**Root Cause:** PipeWire (Garuda's default audio system) blocks direct ALSA device access that MPD typically uses.

**Status on Other Distros:**
- ✅ **Ubuntu:** Works with default ALSA configuration
- ✅ **Arch:** Works with default ALSA configuration  
- ❌ **Garuda:** Requires HTTP streaming workaround

## Solution

A Garuda-specific fix script has been created at:
```
scripts/fix-mpd-garuda-audio.sh
```

### What the script does:
1. Disables direct ALSA output (which PipeWire blocks)
2. Enables MPD's HTTP stream encoder (port 8001, MP3 320kbps)
3. Creates a systemd service (`maestro-ffplay`) that plays the HTTP stream via ffplay
4. This chains: MPD → HTTP → ffplay → PipeWire → Speakers

### Installation

If audio isn't working on your Garuda install, run:
```bash
./scripts/fix-mpd-garuda-audio.sh
```

The script will:
- Detect your OS and only run on Garuda
- Backup your original MPD config
- Configure everything for PipeWire compatibility
- Test the setup

### Revert

If you need to undo the changes:
```bash
sudo cp /etc/mpd.conf.backup.* /etc/mpd.conf
sudo systemctl restart mpd
sudo systemctl disable maestro-ffplay
sudo rm /etc/systemd/system/maestro-ffplay.service
```

## Why Not Modify Main Install Script

The main `install-maestro.sh` remains **unchanged** because:
- ✅ Arch users get native ALSA support (works great)
- ✅ Ubuntu users get native ALSA support (works great)
- ⚠️ Garuda-specific fix is optional and only needed on Garuda
- 🔒 Prevents breaking existing installs on Arch/Ubuntu

**Only Garuda users experiencing audio issues need to run the fix script.**

## Audio Quality

- HTTP stream: MP3 320kbps (high quality for most users)
- If bit-perfect audio needed: Configure ALSA passthrough before running script
- Latency: Minimal (typically <100ms)

## Status

Audio on this system: **Working ✓**
- Playback: Active
- Services: maestro-ffplay running
- Output: PipeWire → Speakers
