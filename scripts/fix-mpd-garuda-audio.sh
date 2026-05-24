#!/bin/bash
#==============================================================================
# Maestro MPD Audio Fix for Garuda Linux
# Configures MPD to work with PipeWire audio system
# This script is ONLY needed on Garuda - Arch and Ubuntu don't need it
#==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Maestro MPD Audio Fix for Garuda Linux${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo -e "${RED}Cannot detect OS${NC}"
    exit 1
fi

if [ "$OS" != "garuda" ]; then
    echo -e "${YELLOW}⚠ This script is for Garuda Linux only${NC}"
    echo "Your system: $OS"
    echo "On Ubuntu and Arch, MPD audio should work without this fix."
    exit 0
fi

echo -e "${YELLOW}This script configures MPD to work with Garuda's PipeWire audio system.${NC}"
echo ""

# Check if MPD is installed
if ! command -v mpd &> /dev/null; then
    echo -e "${RED}Error: MPD is not installed${NC}"
    echo "Please run the main Maestro installer first."
    exit 1
fi

# Backup original config
echo -e "${GREEN}[1/3] Backing up MPD configuration...${NC}"
sudo cp /etc/mpd.conf /etc/mpd.conf.backup.$(date +%Y%m%d_%H%M%S)
echo -e "  ${GREEN}✓ Backed up to /etc/mpd.conf.backup${NC}"
echo ""

# Update MPD config for HTTP streaming (PipeWire compatible)
echo -e "${GREEN}[2/3] Configuring MPD for PipeWire compatibility...${NC}"
sudo tee /etc/mpd.conf > /dev/null <<'EOF'
# Maestro MPD Configuration - Garuda Linux (PipeWire)
# Music directory
music_directory     "/media/music"

# Database and state files
playlist_directory  "/var/lib/mpd/playlists"
db_file             "/var/lib/mpd/database"
log_file            "/var/log/mpd/mpd.log"
pid_file            "/run/mpd/pid"
state_file          "/var/lib/mpd/state"
sticker_file        "/var/lib/mpd/sticker.sql"

# Network settings
bind_to_address     "0.0.0.0"
port                "6600"

# User and permissions
user                "mpd"

# Audio output - HTTP Stream for PipeWire compatibility on Garuda
audio_output {
    type            "httpd"
    name            "HTTP Stream (PipeWire)"
    encoder         "lame"
    port            "8001"
    bitrate         "320"
    format          "48000:16:2"
    always_on       "yes"
    tags            "yes"
}

# Audiophile settings
audio_buffer_size   "4096"
max_output_buffer_size  "16384"

# Logging
log_level           "default"

# Playback settings
auto_update         "yes"
auto_update_depth   "3"
EOF

echo -e "  ${GREEN}✓ MPD configured for HTTP streaming${NC}"
echo ""

# Create ffplay player service
echo -e "${GREEN}[3/3] Setting up audio player service...${NC}"
sudo tee /etc/systemd/system/maestro-ffplay.service > /dev/null <<'EOF'
[Unit]
Description=Maestro Audio Player (ffplay)
After=network.target mpd.service
Wants=mpd.service

[Service]
Type=simple
User=fausto
ExecStart=/usr/bin/ffplay -nodisp -autoexit http://localhost:8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable maestro-ffplay.service
sudo systemctl restart maestro-ffplay.service

echo -e "  ${GREEN}✓ Audio player service configured and started${NC}"
echo ""

# Restart MPD
echo -e "${YELLOW}Restarting MPD...${NC}"
sudo systemctl restart mpd
sleep 3

# Test
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Configuration Complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Audio Setup:"
echo "  • MPD HTTP Stream: port 8001"
echo "  • Player Service: maestro-ffplay (auto-starts)"
echo "  • Backend: PipeWire (via ffplay)"
echo ""
echo "Test playback:"
echo "  $ mpc play"
echo ""
echo "View status:"
echo "  $ systemctl status maestro-ffplay"
echo "  $ journalctl -u maestro-ffplay -f"
echo ""
echo "To revert changes:"
echo "  $ sudo cp /etc/mpd.conf.backup.* /etc/mpd.conf"
echo "  $ sudo systemctl restart mpd"
echo ""
