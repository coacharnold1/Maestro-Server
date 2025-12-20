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
if systemctl is-active --quiet maestro.service; then
    sudo systemctl restart maestro.service
    echo -e "${GREEN}✓ Restarted maestro.service${NC}"
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

if systemctl is-active --quiet maestro.service; then
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
