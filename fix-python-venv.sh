#!/bin/bash

#==============================================================================
# Maestro MPD Control - Fix Python Virtual Environments
# Use this script after system Python updates that break the venvs
#==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

INSTALL_DIR="$HOME/maestro"

# Print banner
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║     MAESTRO - FIX PYTHON VIRTUAL ENVIRONMENTS             ║"
echo "║                                                            ║"
echo "║  Rebuilds venvs after Python system updates               ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Check if maestro is installed
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}Error: Maestro is not installed in $INSTALL_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}This script will recreate Python virtual environments${NC}"
echo -e "${YELLOW}after a system Python update has broken them.${NC}"
echo ""
echo -e "Current Python version: ${GREEN}$(python3 --version)${NC}"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo -e "${GREEN}[1/4] Stopping services...${NC}"
sudo systemctl stop maestro-web.service maestro-admin.service
echo -e "${GREEN}✓ Services stopped${NC}"

echo ""
echo -e "${GREEN}[2/4] Recreating web virtual environment...${NC}"
cd "$INSTALL_DIR/web"
if [ -d "venv" ]; then
    echo -e "${YELLOW}Removing old venv...${NC}"
    rm -rf venv
fi
echo -e "${YELLOW}Creating new venv...${NC}"
python3 -m venv venv
echo -e "${YELLOW}Installing dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    pip install -r "$INSTALL_DIR/requirements.txt"
else
    pip install Flask flask-socketio python-mpd2 Pillow requests eventlet python-dotenv psutil Werkzeug
fi
deactivate
echo -e "${GREEN}✓ Web venv recreated${NC}"

echo ""
echo -e "${GREEN}[3/4] Recreating admin virtual environment...${NC}"
cd "$INSTALL_DIR/admin"
if [ -d "venv" ]; then
    echo -e "${YELLOW}Removing old venv...${NC}"
    rm -rf venv
fi
echo -e "${YELLOW}Creating new venv...${NC}"
python3 -m venv venv
echo -e "${YELLOW}Installing dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install Flask flask-socketio psutil python-engineio python-socketio python-mpd2 discid
fi
deactivate
echo -e "${GREEN}✓ Admin venv recreated${NC}"

echo ""
echo -e "${GREEN}[4/4] Starting services...${NC}"
sudo systemctl start maestro-web.service maestro-admin.service
sleep 3

# Check service status
echo ""
echo -e "${BLUE}Service Status:${NC}"
if systemctl is-active --quiet maestro-web.service; then
    echo -e "${GREEN}✓ maestro-web.service is running${NC}"
else
    echo -e "${RED}✗ maestro-web.service is NOT running${NC}"
    echo -e "${YELLOW}Check logs with: sudo journalctl -u maestro-web.service -n 50${NC}"
fi

if systemctl is-active --quiet maestro-admin.service; then
    echo -e "${GREEN}✓ maestro-admin.service is running${NC}"
else
    echo -e "${RED}✗ maestro-admin.service is NOT running${NC}"
    echo -e "${YELLOW}Check logs with: sudo journalctl -u maestro-admin.service -n 50${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Fix Complete!                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
