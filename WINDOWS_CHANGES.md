# 🪟 Windows Implementation Changes - Nov 19, 2025

## 📍 Context for Linux-side Development
This document explains changes made during Windows testing/implementation so the Linux version can be properly restored while maintaining Windows compatibility.

---

## 🔧 Changes Made on Windows Machine

### 1. **docker-compose.yml - Removed Linux Audio Config**
**Lines removed (17-25):**
```yaml
- /run/user/1000/pulse:/run/user/1000/pulse:rw  # PulseAudio socket
devices:
  - /dev/snd:/dev/snd  # Audio device access
group_add:
  - audio  # Add to audio group
user: "1000:1000"  # Run as user for PulseAudio access
environment:
  - PULSE_RUNTIME_PATH=/run/user/1000/pulse
  - PULSE_SOCKET=unix:/run/user/1000/pulse/native
```

**Reason:** Docker on Windows runs in a Linux VM and cannot access Windows audio devices. These configs caused container startup issues on Windows.

**Current state:** Only HTTP streaming on port 8001 (works on both platforms)

---

### 2. **.env File - Windows Music Path**
**Changed:**
```bash
# Old (Linux):
MUSIC_DIRECTORY=/home/fausto/Music

# New (Windows):
MUSIC_DIRECTORY=C:/Users/coach/Music
```

**Important:** Docker Desktop on Windows requires:
- Forward slashes: `C:/Users/...` ✅
- NOT backslashes: `C:\Users\...` ❌
- NOT WSL format: `/c/Users/...` ❌

---

### 3. **config.env File - Also Updated**
This file was updated but `.env` is what docker-compose actually reads. Keep both in sync.

---

## 🎯 Current Working State (Windows)

### ✅ What Works:
- Docker containers start successfully
- Music library mounts correctly at `/music`
- MPD server running on `localhost:6600`
- Web interface on `localhost:5003`
- HTTP audio stream on `localhost:8001`

### ❌ What Doesn't Work on Windows:
- Direct system audio output (Windows audio devices not accessible from Linux container)
- PulseAudio/PipeWire (Linux-only)

### 🎧 Windows Audio Solution:
Users open `http://localhost:8001` in:
- VLC Player (recommended)
- Web browser
- Windows Media Player

---

## 🐧 TODO: Restore Linux Compatibility

### Strategy: Make docker-compose.yml Universal

**Option A: Profile-based (Recommended)**
```yaml
services:
  mpd:
    image: vimagick/mpd:latest
    # ... base config ...
    ports:
      - "6600:6600"
      - "8001:8001"  # HTTP streaming (works everywhere)
    
    # Linux audio as optional profile
    profiles:
      - with-mpd
      - linux-audio  # NEW: Enable with --profile linux-audio
    
    # When linux-audio profile active:
    volumes:
      - /run/user/1000/pulse:/run/user/1000/pulse:rw
    devices:
      - /dev/snd:/dev/snd
    # etc...
```

**Linux users run:**
```bash
docker-compose --profile with-mpd --profile linux-audio up -d
```

**Windows users run:**
```bash
docker-compose --profile with-mpd up -d
```

---

## 📋 Implementation Tasks

### Phase 1: Make Universal (Immediate)
- [ ] Restore Linux PulseAudio config as `linux-audio` profile
- [ ] Test on Linux machine (fausto's setup)
- [ ] Update README with platform-specific commands

### Phase 2: Windows Native MPD Option (Next)
- [ ] Create `docker-compose.native-mpd.yml`
  - Only runs web container
  - Points to `host.docker.internal:6600`
- [ ] Create `WINDOWS_NATIVE_MPD.md` guide
  - How to install MPD for Windows
  - Configure for WASAPI/DirectSound output
  - Run hybrid setup
- [ ] Update `.env.example` with Windows path examples

### Phase 3: Documentation (Final)
- [ ] Update main README with Windows section
- [ ] Add troubleshooting for Windows paths
- [ ] Document three deployment modes:
  1. Linux: Full containerized (PulseAudio)
  2. Windows: Containerized (HTTP streaming)
  3. Windows: Hybrid (Native MPD + Docker web UI)

---

## 🔄 Syncing Back to Linux Machine

### Git Method:
```bash
# On Windows (this machine):
git add .
git commit -m "Add Windows compatibility - audio config changes"
git push

# On Linux machine:
git pull
# Your .env is gitignored, so Linux paths preserved!
```

### Manual Method:
1. Copy changed files to Linux machine
2. **DO NOT overwrite Linux `.env`** - paths are different!
3. Use Linux `.env.example` to verify settings

---

## 🎵 Files Modified

| File | Change | Linux Impact |
|------|--------|--------------|
| `docker-compose.yml` | Removed PulseAudio lines | ⚠️ Needs restore as profile |
| `.env` | Windows music path | ✅ Gitignored, no impact |
| `config.env` | Windows music path | ⚠️ Reference file, update docs |
| `.env.example` | None yet | 📝 Add Windows path examples |

---

## 🧪 Testing Checklist

### Windows Testing (Complete ✅):
- [x] Containers start without errors
- [x] Music library accessible
- [x] Web interface loads
- [x] MPD responds to commands
- [x] HTTP stream works on port 8001

### Linux Testing (TODO):
- [ ] PulseAudio profile works
- [ ] Direct audio output functional
- [ ] Existing .env paths work
- [ ] No regression in functionality

---

## 💡 Key Insights

1. **Single folder CAN work for both OS** - use profiles
2. **HTTP streaming is universal fallback** - keep always enabled
3. **Windows paths need forward slashes** in Docker context
4. **.env is gitignored** - each machine has own paths
5. **Native MPD option** gives Windows users true system audio

---

## 🚀 Next Steps

**For Linux-side Claude:**
1. Read this document thoroughly
2. Review current `docker-compose.yml` 
3. Implement profile-based Linux audio restoration
4. Test on Linux machine before committing
5. Update documentation for both platforms

**Current Status:** Windows working, Linux compatibility needs restoration via profiles.

---

## 📞 Contact Info
- Windows setup by: Claude (Sonnet 4.5) on Nov 19, 2025
- Linux machine: fausto's original dev environment
- Windows machine: coach's testing environment
