#!/bin/bash

#==============================================================================
# Maestro MPD Control - Update Script
# Pulls latest changes from git and updates the installation
#==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

INSTALL_DIR="$HOME/maestro"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Print banner
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║          MAESTRO MPD CONTROL - UPDATE SCRIPT              ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Check if maestro is installed
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}Error: Maestro is not installed in $INSTALL_DIR${NC}"
    echo "Please run install-maestro.sh first."
    exit 1
fi

echo -e "${GREEN}[1/6] Checking for updates...${NC}"
cd "$REPO_DIR"

# Stash any local changes in the repo
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}Stashing local changes in repository...${NC}"
    git stash
fi

# Pull latest changes
echo -e "${GREEN}Pulling latest changes from git...${NC}"
if git pull origin main; then
    echo -e "${GREEN}✓ Successfully pulled latest changes${NC}"
else
    echo -e "${RED}Failed to pull changes from git${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}[2/6] Backing up current configuration...${NC}"
# Backup current settings
if [ -f "$INSTALL_DIR/settings.json" ]; then
    cp "$INSTALL_DIR/settings.json" "$INSTALL_DIR/settings.json.backup"
    echo -e "${GREEN}✓ Backed up settings.json${NC}"
fi

if [ -f "$HOME/.abcde.conf" ]; then
    cp "$HOME/.abcde.conf" "$HOME/.abcde.conf.backup"
    echo -e "${GREEN}✓ Backed up abcde.conf${NC}"
fi

# Update sudoers permissions (critical for backup/restore)
echo -e "${YELLOW}Updating sudo permissions for admin functions...${NC}"
SUDOERS_FILE="/etc/sudoers.d/maestro"
sudo tee "$SUDOERS_FILE" > /dev/null <<EOF
# Maestro MPD Control - Sudo permissions
# Allow user to run system management commands without password

$USER ALL=(ALL) NOPASSWD: /usr/bin/apt update
$USER ALL=(ALL) NOPASSWD: /usr/bin/apt upgrade
$USER ALL=(ALL) NOPASSWD: /usr/bin/apt upgrade -y
$USER ALL=(ALL) NOPASSWD: /usr/bin/pacman
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart mpd
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop mpd
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl start mpd
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl reboot
$USER ALL=(ALL) NOPASSWD: /sbin/shutdown
$USER ALL=(ALL) NOPASSWD: /sbin/reboot
$USER ALL=(ALL) NOPASSWD: /bin/mount
$USER ALL=(ALL) NOPASSWD: /bin/umount
$USER ALL=(ALL) NOPASSWD: /usr/bin/mount
$USER ALL=(ALL) NOPASSWD: /usr/bin/umount
$USER ALL=(ALL) NOPASSWD: /usr/bin/aplay
$USER ALL=(ALL) NOPASSWD: /usr/bin/journalctl
$USER ALL=(ALL) NOPASSWD: /usr/bin/tee /etc/mpd.conf
$USER ALL=(ALL) NOPASSWD: /usr/bin/dpkg --configure -a
# MPD Database Backup/Restore commands
$USER ALL=(ALL) NOPASSWD: /usr/bin/cp /var/lib/mpd/database /var/lib/mpd/database.backup.*
$USER ALL=(ALL) NOPASSWD: /usr/bin/cp /var/lib/mpd/database.backup.* /var/lib/mpd/database
$USER ALL=(ALL) NOPASSWD: /usr/bin/find /var/lib/mpd/ -name database.backup.* -type f
$USER ALL=(ALL) NOPASSWD: /usr/bin/du -h /var/lib/mpd/database*
$USER ALL=(ALL) NOPASSWD: /usr/bin/stat -c %y /var/lib/mpd/database*
$USER ALL=(ALL) NOPASSWD: /usr/bin/test -f /var/lib/mpd/database*
# CD Ripping commands
$USER ALL=(ALL) NOPASSWD: /usr/bin/cdparanoia
$USER ALL=(ALL) NOPASSWD: /usr/bin/cd-discid
$USER ALL=(ALL) NOPASSWD: /usr/bin/abcde
$USER ALL=(ALL) NOPASSWD: /usr/bin/eject
# File management commands for imported music
$USER ALL=(ALL) NOPASSWD: /usr/bin/mv /media/music/*
$USER ALL=(ALL) NOPASSWD: /usr/bin/rm /media/music/*
$USER ALL=(ALL) NOPASSWD: /usr/bin/rm -rf /media/music/*
EOF
sudo chmod 440 "$SUDOERS_FILE"
echo -e "${GREEN}✓ Updated sudo permissions${NC}"

# Ensure ripped directory exists for CD ripping
if [ ! -d "/media/music/ripped" ]; then
    echo -e "${YELLOW}Creating ripped directory for CD ripping...${NC}"
    sudo mkdir -p /media/music/ripped
    sudo chown mpd:audio /media/music/ripped
    echo -e "${GREEN}✓ Created /media/music/ripped${NC}"
fi

# Update CD auto-rip scripts and udev rule
echo -e "${YELLOW}Updating CD auto-rip configuration...${NC}"
mkdir -p "$INSTALL_DIR/scripts"
mkdir -p "$INSTALL_DIR/logs"

if [ -f "$REPO_DIR/scripts/cd-inserted.sh" ]; then
    cp "$REPO_DIR/scripts/cd-inserted.sh" "$INSTALL_DIR/scripts/"
    chmod +x "$INSTALL_DIR/scripts/cd-inserted.sh"
    echo -e "${GREEN}✓ Updated CD insert handler${NC}"
fi

if [ -f "$REPO_DIR/udev/99-maestro-cd.rules" ]; then
    sed "s/%u/$USER/g" "$REPO_DIR/udev/99-maestro-cd.rules" | sudo tee /etc/udev/rules.d/99-maestro-cd.rules > /dev/null
    sudo udevadm control --reload-rules
    echo -e "${GREEN}✓ Updated udev rule for CD detection${NC}"
fi

echo ""
echo -e "${GREEN}[3/6] Updating main application...${NC}"
# Copy main app files
sudo cp -r "$REPO_DIR/templates" "$INSTALL_DIR/"
sudo cp -r "$REPO_DIR/static" "$INSTALL_DIR/"
sudo cp "$REPO_DIR/app.py" "$INSTALL_DIR/"
sudo cp "$REPO_DIR/requirements.txt" "$INSTALL_DIR/"
echo -e "${GREEN}✓ Updated main application files${NC}"

echo ""
echo -e "${GREEN}[4/6] Updating admin interface...${NC}"
# Copy admin files
sudo cp "$REPO_DIR/admin/admin_api.py" "$INSTALL_DIR/admin/"
sudo cp "$REPO_DIR/admin/requirements.txt" "$INSTALL_DIR/admin/"
sudo cp -r "$REPO_DIR/admin/templates" "$INSTALL_DIR/admin/"
echo -e "${GREEN}✓ Updated admin interface files${NC}"

echo ""
echo -e "${GREEN}[5/6] Updating Python dependencies...${NC}"
# Update main app dependencies (use virtual environment)
if [ -d "$INSTALL_DIR/web/venv" ]; then
    cd "$INSTALL_DIR/web"
    source venv/bin/activate
    pip install --upgrade -r "$INSTALL_DIR/requirements.txt" --quiet
    deactivate
    echo -e "${GREEN}✓ Updated main app dependencies${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment not found at $INSTALL_DIR/web/venv${NC}"
fi

# Update admin dependencies (use virtual environment)
if [ -d "$INSTALL_DIR/admin/venv" ]; then
    cd "$INSTALL_DIR/admin"
    source venv/bin/activate
    pip install --upgrade -r requirements.txt --quiet
    deactivate
    echo -e "${GREEN}✓ Updated admin dependencies${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment not found at $INSTALL_DIR/admin/venv${NC}"
fi

echo ""
echo -e "${GREEN}[6/6] Restarting services...${NC}"
# Restart services
if systemctl is-active --quiet maestro-web.service; then
    sudo systemctl restart maestro-web.service
    echo -e "${GREEN}✓ Restarted maestro-web.service${NC}"
fi

if systemctl is-active --quiet maestro-admin.service; then
    sudo systemctl restart maestro-admin.service
    echo -e "${GREEN}✓ Restarted maestro-admin.service${NC}"
fi

# Wait a moment for services to start
sleep 2

# Check service status
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Service Status:${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if systemctl is-active --quiet maestro-web.service; then
    echo -e "Web UI:    ${GREEN}✓ Running${NC}"
else
    echo -e "Web UI:    ${RED}✗ Not running${NC}"
fi

if systemctl is-active --quiet maestro-admin.service; then
    echo -e "Admin API: ${GREEN}✓ Running${NC}"
else
    echo -e "Admin API: ${RED}✗ Not running${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║             UPDATE COMPLETED SUCCESSFULLY!                 ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Your settings have been preserved in:"
echo -e "  ${YELLOW}$INSTALL_DIR/settings.json${NC}"
echo ""
echo -e "Backups created:"
echo -e "  ${YELLOW}$INSTALL_DIR/settings.json.backup${NC}"
[ -f "$HOME/.abcde.conf.backup" ] && echo -e "  ${YELLOW}$HOME/.abcde.conf.backup${NC}"
echo ""
