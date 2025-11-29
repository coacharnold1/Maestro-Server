#!/bin/bash

# MPD Web Control - Complete Uninstall Script
# This script removes all installations and resets the environment
# while preserving source code

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

echo "=========================================="
echo "🧹 MPD Web Control Complete Uninstall"
echo "=========================================="
echo

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

log_info "Working directory: $SCRIPT_DIR"
echo

# Ask for confirmation
echo "This will completely uninstall and reset MPD Web Control:"
echo "  ✓ Stop and remove Docker containers"
echo "  ✓ Remove Docker images"
echo "  ✓ Remove Docker networks and volumes"
echo "  ✓ Remove systemd service"
echo "  ✓ Remove Python virtual environment"
echo "  ✓ Remove configuration files"
echo "  ✓ Reset to clean state"
echo
echo "  ⚠️  SOURCE CODE WILL BE PRESERVED"
echo

read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Uninstall cancelled"
    exit 0
fi

echo
log_info "Starting complete uninstall..."
echo

# Function to stop and remove Docker containers
cleanup_docker_containers() {
    log_info "Cleaning up Docker containers..."
    
    # Stop and remove containers related to this project
    local containers=(
        "mpd-web-control"
        "maestro-mpd-control"
        "mpd-maestro"
        "mpd-web-control-app"
        "mpd-web-control-mpd"
    )
    
    for container in "${containers[@]}"; do
        if docker ps -a --format "table {{.Names}}" | grep -q "^${container}$" 2>/dev/null; then
            log_info "Stopping and removing container: $container"
            docker stop "$container" 2>/dev/null || true
            docker rm "$container" 2>/dev/null || true
            log_success "Container $container removed"
        fi
    done
    
    # Stop containers from docker-compose files
    if [ -f "docker-compose.yml" ]; then
        log_info "Stopping docker-compose services..."
        docker-compose down --remove-orphans 2>/dev/null || true
    fi
    
    if [ -f "docker-compose.windows.yml" ]; then
        log_info "Stopping Windows docker-compose services..."
        docker-compose -f docker-compose.windows.yml down --remove-orphans 2>/dev/null || true
    fi
    
    if [ -f "docker-compose.native-mpd.yml" ]; then
        log_info "Stopping native MPD docker-compose services..."
        docker-compose -f docker-compose.native-mpd.yml down --remove-orphans 2>/dev/null || true
    fi
}

# Function to remove Docker images
cleanup_docker_images() {
    log_info "Cleaning up Docker images..."
    
    local images=(
        "mpd-web-control"
        "maestro-mpd-control"
        "mpd-maestro"
    )
    
    for image in "${images[@]}"; do
        if docker images --format "table {{.Repository}}" | grep -q "^${image}$" 2>/dev/null; then
            log_info "Removing Docker image: $image"
            docker rmi "$image" --force 2>/dev/null || true
            log_success "Image $image removed"
        fi
    done
    
    # Remove any dangling images
    log_info "Removing dangling images..."
    docker image prune -f 2>/dev/null || true
}

# Function to remove Docker networks
cleanup_docker_networks() {
    log_info "Cleaning up Docker networks..."
    
    local networks=(
        "mpd-web-control_default"
        "maestro-mpd-control_default"
        "mpd_network"
    )
    
    for network in "${networks[@]}"; do
        if docker network ls --format "table {{.Name}}" | grep -q "^${network}$" 2>/dev/null; then
            log_info "Removing Docker network: $network"
            docker network rm "$network" 2>/dev/null || true
            log_success "Network $network removed"
        fi
    done
}

# Function to remove Docker volumes
cleanup_docker_volumes() {
    log_info "Cleaning up Docker volumes..."
    
    local volumes=(
        "mpd_data"
        "music_data"
        "mpd-web-control_mpd_data"
        "maestro-mpd-control_mpd_data"
        "mpd_db"
        "mpd_playlists"
    )
    
    for volume in "${volumes[@]}"; do
        if docker volume ls --format "table {{.Name}}" | grep -q "^${volume}$" 2>/dev/null; then
            log_info "Removing Docker volume: $volume"
            docker volume rm "$volume" 2>/dev/null || true
            log_success "Volume $volume removed"
        fi
    done
    
    # Remove any unused volumes
    log_info "Removing unused volumes..."
    docker volume prune -f 2>/dev/null || true
}

# Function to clean up Docker users and system
cleanup_docker_users() {
    log_info "Cleaning up Docker users and system resources..."
    
    # Remove any orphaned containers
    log_info "Removing orphaned containers..."
    docker container prune -f 2>/dev/null || true
    
    # Clean up any build cache
    log_info "Cleaning Docker build cache..."
    docker builder prune -f 2>/dev/null || true
    
    # Clean up any unused images (not just project-specific ones)
    read -p "🗑️  Remove ALL unused Docker images? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Removing all unused Docker images..."
        docker image prune -a -f 2>/dev/null || true
        log_success "All unused images removed"
    else
        log_info "Skipping unused image cleanup"
    fi
    
    # Clean up any docker-compose project resources
    log_info "Cleaning up any remaining docker-compose resources..."
    docker system prune -f 2>/dev/null || true
    
    log_success "Docker system cleanup completed"
}

# Function to remove systemd service
cleanup_systemd_service() {
    log_info "Cleaning up systemd service..."
    
    local services=(
        "mpd-web-control.service"
        "maestro-mpd-control.service"
    )
    
    for service in "${services[@]}"; do
        if systemctl list-unit-files | grep -q "$service" 2>/dev/null; then
            log_info "Stopping and disabling service: $service"
            sudo systemctl stop "$service" 2>/dev/null || true
            sudo systemctl disable "$service" 2>/dev/null || true
            
            if [ -f "/etc/systemd/system/$service" ]; then
                log_info "Removing service file: /etc/systemd/system/$service"
                sudo rm -f "/etc/systemd/system/$service"
            fi
            
            log_success "Service $service removed"
        fi
    done
    
    # Reload systemd
    if command -v systemctl >/dev/null 2>&1; then
        log_info "Reloading systemd daemon..."
        sudo systemctl daemon-reload 2>/dev/null || true
    fi
}

# Function to remove Python virtual environment
cleanup_python_env() {
    log_info "Cleaning up Python virtual environment..."
    
    if [ -d "venv" ]; then
        log_info "Removing virtual environment directory: venv/"
        rm -rf venv/
        log_success "Virtual environment removed"
    else
        log_info "No virtual environment found"
    fi
    
    # Remove Python cache
    if [ -d "__pycache__" ]; then
        log_info "Removing __pycache__ directory"
        rm -rf __pycache__/
        log_success "Python cache removed"
    fi
    
    # Find and remove all __pycache__ directories
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # Remove .pyc files
    find . -name "*.pyc" -delete 2>/dev/null || true
}

# Function to remove configuration files
cleanup_config_files() {
    log_info "Cleaning up configuration files..."
    
    local config_files=(
        "config.env"
        "settings.json"
        "radio_stations.json"
        "maestro-setup.conf"
    )
    
    for file in "${config_files[@]}"; do
        if [ -f "$file" ]; then
            log_info "Removing configuration file: $file"
            rm -f "$file"
            log_success "File $file removed"
        fi
    done
    
    # Remove any backup files
    log_info "Removing backup files..."
    rm -f *.bak *.backup 2>/dev/null || true
    
    # Remove logs
    if [ -d "logs" ]; then
        log_info "Removing logs directory"
        rm -rf logs/
        log_success "Logs removed"
    fi
}

# Function to clean up temporary files
cleanup_temp_files() {
    log_info "Cleaning up temporary files..."
    
    # Remove temporary directories
    rm -rf tmp/ temp/ .tmp/ 2>/dev/null || true
    
    # Remove editor temp files
    rm -f .*.swp .*.swo *~ 2>/dev/null || true
    
    # Remove OS specific files
    rm -f .DS_Store Thumbs.db 2>/dev/null || true
    
    # Remove test artifacts
    rm -rf .pytest_cache/ .coverage htmlcov/ 2>/dev/null || true
    
    log_success "Temporary files cleaned"
}

# Function to reset git state (optional)
reset_git_state() {
    echo
    read -p "🔄 Reset git repository to clean state? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Resetting git repository..."
        
        # Reset any uncommitted changes
        git reset --hard HEAD 2>/dev/null || true
        
        # Clean untracked files (but preserve source code)
        git clean -fd -e "*.py" -e "*.html" -e "*.css" -e "*.js" -e "*.md" -e "*.txt" 2>/dev/null || true
        
        log_success "Git repository reset to clean state"
    fi
}

# Main uninstall execution
main() {
    # Check if Docker is available
    if command -v docker >/dev/null 2>&1; then
        cleanup_docker_containers
        cleanup_docker_images
        cleanup_docker_networks
        cleanup_docker_volumes
        cleanup_docker_users
        log_success "Docker cleanup completed"
    else
        log_warning "Docker not found, skipping Docker cleanup"
    fi
    
    echo
    
    # Check if systemd is available
    if command -v systemctl >/dev/null 2>&1; then
        cleanup_systemd_service
        log_success "Systemd cleanup completed"
    else
        log_warning "Systemctl not found, skipping service cleanup"
    fi
    
    echo
    
    cleanup_python_env
    log_success "Python environment cleanup completed"
    
    echo
    
    cleanup_config_files
    log_success "Configuration cleanup completed"
    
    echo
    
    cleanup_temp_files
    log_success "Temporary files cleanup completed"
    
    echo
    
    # Optional git reset
    reset_git_state
    
    echo
    echo "=========================================="
    log_success "Uninstall completed successfully!"
    echo "=========================================="
    echo
    log_info "What was removed:"
    echo "  • Docker containers, images, networks, and volumes"
    echo "  • Systemd service files"
    echo "  • Python virtual environment"
    echo "  • Configuration files (config.env, settings.json, etc.)"
    echo "  • Temporary and cache files"
    echo
    log_info "What was preserved:"
    echo "  • Source code files (*.py, *.html, *.css, *.js)"
    echo "  • Documentation (*.md)"
    echo "  • Requirements and setup scripts"
    echo "  • Docker configuration files"
    echo
    echo "✅ You can now run setup.sh to reinstall cleanly"
    echo
}

# Run the uninstall
main "$@"