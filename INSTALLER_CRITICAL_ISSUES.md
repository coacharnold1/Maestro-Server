# Maestro-Server Installer - Critical Issues

**Date:** December 15, 2025  
**Tested on:** Arch Linux with existing production MPD setup  
**Repository:** https://github.com/coacharnold1/Maestro-Server

---

## 🚨 CRITICAL BUGS - Data Loss Risk

### 1. **MPD Database Rebuilt Without Backup**
**Severity:** CRITICAL - Data Loss

**Problem:**
- Installer restarts MPD with new config
- MPD rebuilds database from scratch
- Lost 128,070 songs down to 4,236 songs
- Only recovered because user had backup from Nov 5

**Impact:**
- Complete loss of MPD database
- Loss of play counts, ratings, playlists statistics
- User lost 526 days of playback history

**Required Fix:**
```bash
# BEFORE any MPD changes:
sudo cp /var/lib/mpd/database /var/lib/mpd/database.backup.$(date +%Y%m%d_%H%M%S)
echo "MPD database backed up to /var/lib/mpd/database.backup.*"
```

---

### 2. **MPD Config Overwritten Without Permission**
**Severity:** CRITICAL - Breaks Audio

**Problem:**
- Installer overwrites `/etc/mpd.conf` without asking
- Destroys working audio configuration
- User had: `device "hw:CARD=Lite,DEV=0"` (Topping E30 II USB DAC)
- Installer changed to: `device "hw:1,0"` (generic, broken)
- Lost buffer settings: `buffer_before_play "35%"`, `audio_buffer_size "50000"`
- Lost HTTP stream configuration

**Impact:**
- No audio output
- Music server completely non-functional
- User's custom audio settings lost

**CRITICAL REQUIREMENT:**
**Installer should NEVER touch MPD config on existing installations. MPD configuration should ONLY be modified through the admin panel's "tweak" page when user explicitly requests it.**

**Required Fix:**
```bash
# Check for existing config - if found, DO NOT TOUCH IT
if [ -f /etc/mpd.conf ]; then
    echo "✓ Existing MPD configuration detected - will NOT be modified"
    echo "  Use the admin panel to adjust MPD settings after installation"
    MPD_INSTALL_TYPE="preserve_existing"
else
    # Only install basic config on fresh systems
    echo "Installing default MPD configuration"
    sudo cp templates/mpd.conf /etc/mpd.conf
fi
```

---

### 3. **File Permission Changes on Network Mounts**
**Severity:** HIGH - System Errors

**Problem:**
- Installer runs: `sudo chown $USER:$USER "$MUSIC_DIR"`
- Fails on read-only NFS/SMB mounts
- Causes installer errors and confusion
- Line in installer: `sudo chown $USER:$USER "/media/music"` failed with read-only filesystem errors

**Impact:**
- Installer appears to fail
- Floods terminal with permission errors
- Actually not needed at all

**Required Fix:**
```bash
# Don't change ownership of music directory
# MPD runs as 'mpd' user and already has read access
# Remove this line entirely:
# sudo chown $USER:$USER "$MUSIC_DIR"
```

---

### 4. **No Distribution Detection (Arch vs Ubuntu)**
**Severity:** CRITICAL - Installation Fails on Arch Linux

**Problem:**
- Installer assumes Ubuntu/Debian conventions
- On Arch Linux, default primary group is `users`, not `$USER`
- Command failed: `chown: invalid group: 'fausto:fausto'`
- Different package managers (pacman vs apt)
- Different service paths and conventions
- Different audio device permissions

**Impact:**
- Installer completely fails on Arch Linux
- Cannot install dependencies
- Permission errors throughout

**Required Fix:**
```bash
# Detect distribution
if [ -f /etc/arch-release ]; then
    DISTRO="arch"
    PRIMARY_GROUP=$(id -gn $USER)  # Usually 'users'
    PKG_MANAGER="pacman"
    INSTALL_CMD="sudo pacman -S --noconfirm"
elif [ -f /etc/lsb-release ] && grep -q Ubuntu /etc/lsb-release; then
    DISTRO="ubuntu"
    PRIMARY_GROUP=$USER
    PKG_MANAGER="apt"
    INSTALL_CMD="sudo apt install -y"
else
    echo "⚠️  Unsupported distribution. Tested on: Arch Linux, Ubuntu 24.04"
    read -p "Continue anyway? (y/N): " CONTINUE
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

echo "Detected: $DISTRO"

# Use detected settings
sudo chown $USER:$PRIMARY_GROUP "$INSTALL_DIR"

# Install dependencies for detected distro
if [ "$DISTRO" = "arch" ]; then
    $INSTALL_CMD python python-pip python-virtualenv mpd mpc
elif [ "$DISTRO" = "ubuntu" ]; then
    $INSTALL_CMD python3 python3-pip python3-venv mpd mpc
fi
```

---

### 5. **No Rollback Capability**
**Severity:** HIGH - Recovery Issues

**Problem:**
- No uninstall script provided
- No way to restore previous state
- User stuck with broken system

**Required Fix:**
Create `uninstall-maestro.sh`:
```bash
#!/bin/bash
# Stop and remove services
sudo systemctl stop maestro-web maestro-admin
sudo systemctl disable maestro-web maestro-admin
sudo rm /etc/systemd/system/maestro-web.service
sudo rm /etc/systemd/system/maestro-admin.service
sudo systemctl daemon-reload

# Remove installation
rm -rf ~/maestro

# Restore MPD config if backup exists
if [ -f /etc/mpd.conf.backup.* ]; then
    LATEST_BACKUP=$(ls -t /etc/mpd.conf.backup.* | head -1)
    sudo cp "$LATEST_BACKUP" /etc/mpd.conf
    sudo systemctl restart mpd
fi

echo "Maestro uninstalled. MPD config restored from backup."
```

---

## ⚠️ NON-CRITICAL ISSUES

### 6. **No Data Migration from Existing Installations**
**Severity:** HIGH - User Loses All Customizations

**Problem:**
- Installer doesn't detect existing Maestro installations
- Creates duplicate systems side-by-side
- User has both `/home/fausto/mpd_web_control` (production) and `~/maestro` (new)
- New system has no data: radio stations, playlists, settings, artwork cache
- User must manually recreate everything

**Impact:**
- Lost radio station configurations (JSON files)
- Lost custom playlists
- Lost user preferences and settings
- Lost cached album artwork
- Wasted storage with duplicate installations

**Required Fix:**
```bash
# Check for existing installations
OLD_INSTALL=""
if [ -d "/home/$USER/mpd_web_control" ]; then
    OLD_INSTALL="/home/$USER/mpd_web_control"
elif [ -d "/home/$USER/Maestro-MPD-Control" ]; then
    OLD_INSTALL="/home/$USER/Maestro-MPD-Control"
fi

if [ -n "$OLD_INSTALL" ]; then
    echo "⚠️  Existing Maestro installation found at: $OLD_INSTALL"
    echo ""
    read -p "Migrate data from existing installation? (Y/n): " MIGRATE
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "Migrating data..."
        
        # Copy radio stations
        if [ -f "$OLD_INSTALL/radio_stations.json" ]; then
            cp "$OLD_INSTALL/radio_stations.json" ~/maestro/web/
            echo "✓ Radio stations migrated"
        fi
        
        # Copy settings
        if [ -f "$OLD_INSTALL/settings.json" ]; then
            cp "$OLD_INSTALL/settings.json" ~/maestro/web/
            echo "✓ Settings migrated"
        fi
        
        # Copy playlists if different from MPD playlists
        if [ -d "$OLD_INSTALL/playlists" ]; then
            cp -r "$OLD_INSTALL/playlists" ~/maestro/web/
            echo "✓ Playlists migrated"
        fi
        
        echo ""
        echo "Data migration complete!"
        echo "Old installation preserved at: $OLD_INSTALL"
        echo "You can remove it manually after verifying everything works."
    fi
fi
```

---

### 7. **Admin Panel Cannot Set Audio Device**
**Severity:** HIGH - Critical Feature Broken

**Problem:**
- Admin panel "tweak" page cannot detect or set audio devices
- On Arch Linux: `aplay -l` requires root/audio group permissions
- Returns "no soundcards found" when run as user
- User cannot configure audio without manually editing MPD config
- This defeats the purpose of the admin panel

**Impact:**
- Audio configuration must be done manually via SSH
- Admin panel unusable for primary function
- Especially problematic on Arch Linux

**Required Fixes:**

**1. Fix audio group permissions (Arch Linux):**
```bash
# During installation, add user to audio group
if [ "$DISTRO" = "arch" ]; then
    sudo usermod -a -G audio $USER
    echo "Added $USER to audio group (re-login required)"
fi
``# 9. **Service File Compatibility Issues**
**Problem:**
- Service files may use Ubuntu-specific paths
- Python paths differ: `/usr/bin/python3` (Ubuntu) vs `/usr/bin/python` (Arch)
- Virtual environment activation differs between distros
- Service user/group assumptions

**Required Fix:**
```bash
# Detect Python path
if [ "$DISTRO" = "arch" ]; then
    PYTHON_BIN="/usr/bin/python"
elif [ "$DISTRO" = "ubuntu" ]; then
    PYTHON_BIN="/usr/bin/python3"
fi

# Generate service files with correct paths
cat > /tmp/maestro-web.service <<EOF
[Unit]
Description=Maestro MPD Web Interface
After=network.target mpd.service

[Service]
Type=simple
User=$USER
Group=$PRIMARY_GROUP
WorkingDirectory=$HOME/maestro/web
Environment="PATH=$HOME/maestro/web/venv/bin:$PATH"
ExecStart=$HOME/maestro/web/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/maestro-web.service /etc/systemd/system/
```

---

##`

**2. Fix admin_api.py to handle permissions:**
```python
def get_audio_devices():
    try:
        # Try without sudo first
        result = subprocess.run(['aplay', '-l'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        
        if "no soundcards found" in result.stderr.lower():
            # Try with sudo on Arch Linux
            result = subprocess.run(['sudo', 'aplay', '-l'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
        
        return parse_audio_devices(result.stdout)
    except Exception as e:
        return {"error": f"Cannot detect audio devices: {e}"}
```

**3. Add sudoers rule for audio commands:**
```bash
# Allow audio device detection without password
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/aplay" | sudo tee /etc/sudoers.d/maestro-audio
sudo chmod 440 /etc/sudoers.d/maestro-audio
```

---

### 8. **HTTP Stream Not Preserved**
**Problem:**
- Original config had HTTP stream output
- Installer config template doesn't match user's needs
- Lost streaming capability

**Required Fix:**
Document in README that users should review and customize audio outputs.

---

## 📋 RECOMMENDED CHANGES

### Installation Flow Should Be:

1. **Pre-flight checks:**
   - Detect existing installations
   - Detect existing MPD configs
   - Check for network mounts
   - Show what will be changed

2. **Confirmation:**
   - List all changes to be made
   - Require explicit confirmation
   - Offer custom vs automatic install

3. **Backup everything:**
   - MPD database: `/var/lib/mpd/database`
   - MPD config: `/etc/mpd.conf`
   - Existing services
   - Document backup locations

4. **Install with safety:**
   - Skip permission changes on music directories
   - Use correct user groups
   - Don't restart services until user confirms

5. **Post-install:**
   - Verify all services running
   - Test audio output
   - Display rollback instructions
   - Provide uninstall script

---

## 🧪 TESTING CHECKLIST

Before releasing installer:
- [ ] Test on fresh Ubuntu 24.04 install
- [ ] Test on fresh Arch Linux install
- [ ] Test with existing MPD installation
- [ ] Test with USB DAC audio device
- [ ] Test with network music mounts (NFS/SMB)
- [ ] Test rollback/uninstall process
- [ ] Verify MPD database preserved
- [ ] Verify audio configuration preserved

---

## � SOURCE CODE BUGS

### 10. **Wrong Directory Name in Code**
**Severity:** LOW - Misleading Log Messages

**Problem:**
- Source code in GitHub repository has typo
- File: `app.py` line ~3067
- Code says: `print(f"Getting recent albums from 'down' and 'cloyd' directories...")`
- Should say: `print(f"Getting recent albums from 'down' and 'gidney' directories...")`
- Directory 'cloyd' doesn't exist, code actually checks correct directories `['gidney', 'down']`
- Only affects log messages, feature works correctly

**Impact:**
- Confusing log messages for debugging
- Users think wrong directory is being scanned
- Misleading during troubleshooting

**Required Fix in app.py:**
```python
# Line ~3067 - Fix typo in print statement
print(f"Getting recent albums from 'down' and 'gidney' directories...")
```

---

## 💡 SUGGESTED IMPROVEMENTS

1. **Interactive vs Automatic Mode**
   - `--automatic` flag for fresh installs
   - Interactive mode (default) asks before each change

2. **Dry-run Mode**
   - `--dry-run` shows what would be changed without doing it

3. **Backup Script**
   - Separate `backup-maestro.sh` to backup current state
   - Run before installer

4. **Better Error Handling**
   - Don't fail on permission errors for read-only mounts
   - Continue installation with warnings
   - Log errors to file for debugging

5. **Code Quality Checks**
   - Run linters/spell checkers on source code
   - Test all hardcoded paths match actual directory structures
   - Validate print statements match actual code behavior

---

## 📞 CONTACT

These issues discovered during production installation on December 15, 2025.

System: Arch Linux, MPD 0.24.6, 128k song library, USB DAC (Topping E30 II Lite)

All issues are reproducible and critical for production environments.
