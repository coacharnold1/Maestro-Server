#!/bin/bash

# Maestro Server - Uninstallation Script
# Removes MPD, Web UI, Admin API, and all related files/services
# Usage: sudo ./uninstall-maestro.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths
INSTALL_DIR="/opt/maestro"
MUSIC_DIR="/var/music"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: This script must be run as root or with sudo${NC}"
    exit 1
fi

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║       MAESTRO SERVER - UNINSTALLATION SCRIPT v2.0          ║
║                                                            ║
║    This will remove MPD, Web UI, Admin API, and all        ║
║    related files, services, and configurations.            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Confirmation prompt
echo -e "${YELLOW}WARNING: This will completely remove Maestro Server and MPD${NC}"
echo -e "${YELLOW}The following will be removed:${NC}"
echo "  • MPD (Music Player Daemon)"
echo "  • Maestro Web UI"
echo "  • Maestro Admin API"
echo "  • Systemd services"
echo "  • Configuration files"
echo "  • Installation directory ($INSTALL_DIR)"
echo ""
echo -e "${RED}Music files in $MUSIC_DIR will NOT be deleted${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${BLUE}Uninstallation cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}Starting uninstallation...${NC}"
echo ""

# Stop and disable services
stop_services() {
    echo -e "${GREEN}[1/7] Stopping services...${NC}"
    
    systemctl stop maestro-web 2>/dev/null || true
    systemctl stop maestro-admin 2>/dev/null || true
    systemctl stop mpd 2>/dev/null || true
    
    systemctl disable maestro-web 2>/dev/null || true
    systemctl disable maestro-admin 2>/dev/null || true
    systemctl disable mpd 2>/dev/null || true
    
    echo -e "${GREEN}✓ Services stopped${NC}"
}

# Remove systemd service files
remove_services() {
    echo -e "${GREEN}[2/7] Removing systemd services...${NC}"
    
    rm -f /etc/systemd/system/maestro-web.service
    rm -f /etc/systemd/system/maestro-admin.service
    
    systemctl daemon-reload
    
    echo -e "${GREEN}✓ Services removed${NC}"
}

# Remove installation directory
remove_install_dir() {
    echo -e "${GREEN}[3/7] Removing installation directory...${NC}"
    
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        echo -e "${GREEN}✓ Removed $INSTALL_DIR${NC}"
    else
        echo -e "${YELLOW}⚠ Installation directory not found${NC}"
    fi
}

# Remove MPD
remove_mpd() {
    echo -e "${GREEN}[4/7] Checking MPD...${NC}"
    
    local install_info="$INSTALL_DIR/.maestro_install_info"
    local mpd_type=""
    
    [ -f "$install_info" ] && mpd_type=$(grep "^MPD_INSTALL_TYPE=" "$install_info" | cut -d= -f2)
    
    if [ "$mpd_type" = "package" ]; then
        echo -e "  ${YELLOW}Removing MPD (installed by Maestro)${NC}"
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS=$ID
        fi
        
        case "$OS" in
            ubuntu|debian) apt remove -y mpd mpc; apt autoremove -y ;;
            arch|manjaro) pacman -R --noconfirm mpd mpc ;;
        esac
        echo -e "${GREEN}✓ MPD removed${NC}"
    elif [ "$mpd_type" = "existing" ] || [ "$mpd_type" = "skip" ]; then
        echo -e "${GREEN}✓ Preserving MPD ($mpd_type)${NC}"
    else
        echo -e "${YELLOW}⚠ No install info${NC}"
        read -p "Remove MPD package? (y/N): "
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            [ -f /etc/os-release ] && . /etc/os-release && OS=$ID
            case "$OS" in
                ubuntu|debian) apt remove -y mpd mpc; apt autoremove -y ;;
                arch|manjaro) pacman -R --noconfirm mpd mpc ;;
            esac
            echo -e "${GREEN}✓ MPD removed${NC}"
        else
            echo -e "${GREEN}✓ MPD preserved${NC}"
        fi
    fi
}

# Remove MPD data and config
remove_mpd_data() {
    echo -e "${GREEN}[5/7] Handling MPD data...${NC}"
    
    local install_info="$INSTALL_DIR/.maestro_install_info"
    local mpd_type=""
    [ -f "$install_info" ] && mpd_type=$(grep "^MPD_INSTALL_TYPE=" "$install_info" | cut -d= -f2)
    
    if [ -f /etc/mpd.conf ]; then
        cp /etc/mpd.conf /tmp/mpd.conf.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
        echo -e "  ${GREEN}✓ Config backed up${NC}"
    fi
    
    if [ "$mpd_type" = "package" ]; then
        echo -e "  ${YELLOW}Removing MPD config/data${NC}"
        rm -f /etc/mpd.conf
        rm -rf /var/lib/mpd /var/log/mpd /run/mpd
        echo -e "${GREEN}✓ MPD data removed${NC}"
    else
        echo -e "  ${YELLOW}Preserving MPD config/data${NC}"
        echo -e "${GREEN}✓ MPD data preserved${NC}"
    fi
}

# Remove Python virtual environments
remove_venvs() {
    echo -e "${GREEN}[6/7] Cleaning up Python environments...${NC}"
    
    # Note: venvs are in $INSTALL_DIR which is already removed
    echo -e "${GREEN}✓ Virtual environments removed${NC}"
}

# Remove log files
remove_logs() {
    echo -e "${GREEN}[7/7] Removing log files...${NC}"
    
    rm -f /tmp/maestro-web.log
    rm -f /tmp/maestro-admin.log
    
    echo -e "${GREEN}✓ Log files removed${NC}"
}

# Optional: Remove music directory
prompt_remove_music() {
    echo ""
    echo -e "${YELLOW}Music Directory: $MUSIC_DIR${NC}"
    read -p "Do you want to remove the music directory? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        if [ -d "$MUSIC_DIR" ]; then
            echo -e "${YELLOW}⚠ Removing $MUSIC_DIR and all contents...${NC}"
            rm -rf "$MUSIC_DIR"
            echo -e "${GREEN}✓ Music directory removed${NC}"
        else
            echo -e "${YELLOW}⚠ Music directory not found${NC}"
        fi
    else
        echo -e "${BLUE}Music directory preserved: $MUSIC_DIR${NC}"
    fi
}

# Main uninstallation
main() {
    stop_services
    remove_services
    remove_install_dir
    remove_mpd
    remove_mpd_data
    remove_venvs
    remove_logs
    
    echo ""
    prompt_remove_music
    
    echo ""
    echo -e "${BLUE}"
    cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║           MAESTRO SERVER UNINSTALLED SUCCESSFULLY          ║
║                                                            ║
║  All services, files, and configurations have been         ║
║  removed from your system.                                 ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    echo -e "${GREEN}Summary:${NC}"
    echo "  • MPD: Removed"
    echo "  • Web UI: Removed"
    echo "  • Admin API: Removed"
    echo "  • Services: Removed"
    echo "  • Installation: Removed"
    echo ""
    echo -e "${YELLOW}Config backup: /tmp/mpd.conf.backup.*${NC}"
    echo ""
    echo -e "${BLUE}Thank you for using Maestro Server!${NC}"
}

# Run main function
main
