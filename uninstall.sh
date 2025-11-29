#!/bin/bash
# Maestro MPD Control - Complete Uninstall Script
# This removes all traces of the installation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}🗑️  Maestro MPD Control - Complete Uninstall${NC}"
echo -e "${RED}=============================================${NC}"
echo ""

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[DONE]${NC} $1"
}

# Confirmation
echo "This will completely remove:"
echo "  • All Docker containers and images"
echo "  • All data volumes and databases"
echo "  • All configuration files"
echo "  • User group memberships (docker, audio)"
echo "  • Network configurations"
echo ""
echo -e "${YELLOW}WARNING: This cannot be undone!${NC}"
echo ""
read -p "Are you sure you want to completely uninstall? [y/N]: " confirm

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""
print_status "Starting complete uninstall..."

# Stop and remove all containers
print_status "Stopping and removing containers..."
sudo docker-compose down -v --remove-orphans 2>/dev/null || true
sudo docker stop $(sudo docker ps -aq --filter "name=mpd") 2>/dev/null || true
sudo docker rm $(sudo docker ps -aq --filter "name=mpd") 2>/dev/null || true

# Remove Docker images
print_status "Removing Docker images..."
sudo docker rmi mpd-docker-folder-web 2>/dev/null || true
sudo docker rmi vimagick/mpd:latest 2>/dev/null || true

# Remove Docker volumes
print_status "Removing Docker volumes..."
sudo docker volume rm mpd_db mpd_playlists mpd_web_control_cache 2>/dev/null || true
sudo docker volume prune -f 2>/dev/null || true

# Remove Docker networks
print_status "Removing Docker networks..."
sudo docker network rm mpd-network 2>/dev/null || true
sudo docker network prune -f 2>/dev/null || true

# Remove user from groups (optional)
echo ""
read -p "Remove user from docker and audio groups? [y/N]: " remove_groups
if [[ $remove_groups =~ ^[Yy]$ ]]; then
    print_status "Removing user from docker group..."
    sudo gpasswd -d "$USER" docker 2>/dev/null || true
    
    print_status "Removing user from audio group..."
    sudo gpasswd -d "$USER" audio 2>/dev/null || true
    
    print_warning "Group changes take effect after logout/login"
fi

# Clean up any leftover processes
print_status "Cleaning up processes..."
sudo pkill -f "mpd.*docker" 2>/dev/null || true

# Remove project directory (optional)
echo ""
CURRENT_DIR=$(pwd)
if [[ "$CURRENT_DIR" =~ "MPD-Docker-Folder" ]] || [[ "$CURRENT_DIR" =~ "maestro-mpd-control" ]]; then
    echo "Current directory appears to be the project folder:"
    echo "  $CURRENT_DIR"
    echo ""
    read -p "Remove entire project directory? [y/N]: " remove_dir
    if [[ $remove_dir =~ ^[Yy]$ ]]; then
        cd ..
        print_status "Removing project directory..."
        rm -rf "$CURRENT_DIR"
        print_success "Project directory removed"
    fi
fi

# Clean Docker system (optional)
echo ""
read -p "Clean entire Docker system (removes all unused containers/images)? [y/N]: " clean_docker
if [[ $clean_docker =~ ^[Yy]$ ]]; then
    print_status "Cleaning Docker system..."
    sudo docker system prune -af --volumes
    print_success "Docker system cleaned"
fi

echo ""
print_success "🎉 Complete uninstall finished!"
echo ""
echo "What was removed:"
echo "  ✅ All Maestro MPD containers and images"
echo "  ✅ All data volumes and databases"
echo "  ✅ All Docker networks"
if [[ $remove_groups =~ ^[Yy]$ ]]; then
echo "  ✅ User group memberships"
fi
if [[ $remove_dir =~ ^[Yy]$ ]]; then
echo "  ✅ Project directory"
fi
echo ""
echo "To test fresh installation tomorrow:"
echo "  1. Log out and log back in (if groups were removed)"
echo "  2. git clone <repository-url>"
echo "  3. cd <project-directory>"
echo "  4. ./setup.sh"
echo ""
print_success "Ready for fresh user testing!"