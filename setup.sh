#!/bin/bash
set -e

# Maestro MPD Control - Docker Setup Script
# Interactive configuration and deployment

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emoji symbols
MUSIC="🎵"
DOCKER="🐳"
GEAR="⚙️"
ROCKET="🚀"
CHECK="✅"
WARN="⚠️"
ERROR="❌"

# Function to print status messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}$CHECK${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}$WARN${NC} $1"
}

print_error() {
    echo -e "${RED}$ERROR${NC} $1"
}

# New: Docker permission check and fix
check_docker_permissions() {
    echo -e "${BLUE}[INFO]${NC} Checking Docker permissions..."
    
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed. Please install Docker first:"
        echo "  • Ubuntu/Debian: sudo apt update && sudo apt install docker.io"
        echo "  • CentOS/RHEL: sudo yum install docker"
        echo "  • Or visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker ps >/dev/null 2>&1; then
        echo -e "${YELLOW}$WARN${NC} Docker permissions need setup..."
        echo "Adding user to docker group..."
        
        if sudo usermod -aG docker "$USER" 2>/dev/null; then
            print_success "Added $USER to docker group"
            echo -e "${YELLOW}$WARN${NC} You need to log out and log back in for Docker permissions to take effect."
            echo "Then run this script again."
            echo ""
            echo -e "${BLUE}Quick alternative:${NC} Run 'newgrp docker' then './setup.sh' again"
            exit 0
        else
            print_error "Failed to add user to docker group. You may need to run with sudo."
            echo "Alternative: Try 'sudo ./setup.sh' (not recommended for production)"
            exit 1
        fi
    fi
    
    print_success "Docker permissions OK"
}

# New: Check for Docker Compose
check_docker_compose() {
    if ! command -v docker-compose >/dev/null 2>&1; then
        print_error "Docker Compose is not installed."
        echo "Installing Docker Compose..."
        
        if command -v apt >/dev/null 2>&1; then
            sudo apt update && sudo apt install docker-compose-plugin -y
        elif command -v yum >/dev/null 2>&1; then
            sudo yum install docker-compose -y
        else
            echo "Please install Docker Compose manually:"
            echo "https://docs.docker.com/compose/install/"
            exit 1
        fi
    fi
    
    print_success "Docker Compose available"
}

# New: Port conflict detection and resolution
check_port_conflicts() {
    echo -e "${BLUE}[INFO]${NC} Checking for port conflicts..."
    
    # Check MPD port
    if command -v netstat >/dev/null 2>&1; then
        if netstat -tuln 2>/dev/null | grep -q ":6600 "; then
            echo -e "${YELLOW}$WARN${NC} Port 6600 is already in use (probably your existing MPD server)"
            echo -e "${GREEN}$CHECK${NC} This is fine! Container will use port 6601 (isolated setup)"
            export MPD_EXTERNAL_PORT=6601
        fi
        
        # Check web port
        WEB_PORT=${WEB_PORT:-5003}
        if netstat -tuln 2>/dev/null | grep -q ":$WEB_PORT "; then
            echo -e "${YELLOW}$WARN${NC} Port $WEB_PORT is already in use"
            read -p "Enter alternative web port (e.g., 5004): " NEW_PORT
            if [[ "$NEW_PORT" =~ ^[0-9]+$ ]] && [ "$NEW_PORT" -ge 1024 ] && [ "$NEW_PORT" -le 65535 ]; then
                export WEB_PORT="$NEW_PORT"
                echo -e "${GREEN}$CHECK${NC} Using port $WEB_PORT for web interface"
            else
                print_error "Invalid port number. Exiting."
                exit 1
            fi
        fi
    fi
}

# New: Comprehensive deployment validation
validate_deployment() {
    echo -e "${BLUE}[INFO]${NC} Validating deployment..."
    local validation_failed=false
    
    # Check if containers are running
    if docker-compose ps | grep -q "Up"; then
        print_success "Containers are running"
    else
        print_error "Containers are not running properly"
        validation_failed=true
    fi
    
    # Test web interface
    local web_port=${WEB_PORT:-5003}
    echo -e "${BLUE}[INFO]${NC} Testing web interface on port $web_port..."
    
    if curl -s -f http://localhost:$web_port >/dev/null; then
        print_success "Web interface responding at http://localhost:$web_port"
    else
        print_error "Web interface not responding"
        echo "Try waiting 30 seconds and check: http://localhost:$web_port"
        validation_failed=true
    fi
    
    # Check MPD connection (if containerized)
    if [ "$USE_CONTAINER_MPD" = "true" ] || grep -q "with-mpd" .env 2>/dev/null; then
        if docker-compose ps | grep mpd-server | grep -q "Up"; then
            print_success "MPD server container running"
        else
            print_warning "MPD server container not running - check logs"
        fi
    fi
    
    # Check music directory mount
    if [ -n "$MUSIC_DIRECTORY" ] && [ -d "$MUSIC_DIRECTORY" ]; then
        print_success "Music directory accessible: $MUSIC_DIRECTORY"
    else
        print_warning "Music directory may not be accessible"
    fi
    
    if [ "$validation_failed" = false ]; then
        echo ""
        print_success "🎉 Deployment validation successful!"
        echo ""
        echo -e "${GREEN}$CHECK Quick Start:${NC}"
        echo "  1. Open: ${BLUE}http://localhost:$web_port${NC}"
        echo "  2. Browse your music library"
        echo "  3. Click play on any song"
        echo "  4. Audio streams through your browser or http://localhost:8000"
        echo ""
        echo -e "${CYAN}$INFO Useful Commands:${NC}"
        echo "  View logs:     docker-compose logs -f"
        echo "  Stop:          docker-compose down"
        echo "  Restart:       docker-compose restart"
        return 0
    else
        echo ""
        print_error "Validation found issues"
        echo ""
        echo -e "${YELLOW}Troubleshooting:${NC}"
        echo "  • Check container status: docker-compose ps"
        echo "  • View detailed logs: docker-compose logs -f"
        echo "  • Wait 1-2 minutes for services to fully start"
        echo "  • Ensure music directory exists and is accessible"
        return 1
    fi
}

print_warning() {
    echo -e "${YELLOW}$WARN${NC} $1"
}

print_error() {
    echo -e "${RED}$ERROR${NC} $1"
}

## MAIN SCRIPT EXECUTION START ##

echo -e "${PURPLE}$MUSIC Maestro MPD Control - Docker Setup $MUSIC${NC}"
echo -e "${PURPLE}===========================================${NC}"
echo ""

# Pre-flight checks
echo -e "${CYAN}$GEAR Pre-flight Checks${NC}"
check_docker_permissions
check_docker_compose  
check_port_conflicts
echo ""

# Audio system detection and configuration
auto_detect_audio() {
    echo -e "${CYAN}🔊 Audio System Detection${NC}"
    echo "=============================="
    echo ""
    
    # Check what audio system is running
    if pgrep -x "pipewire" > /dev/null; then
        AUDIO_SYSTEM="pipewire"
        AUDIO_METHOD="pulse"  # PipeWire uses PulseAudio protocol
        echo "✅ Detected: PipeWire (modern audio)"
    elif pgrep -x "pulseaudio" > /dev/null; then
        AUDIO_SYSTEM="pulseaudio" 
        AUDIO_METHOD="pulse"
        echo "✅ Detected: PulseAudio"
    elif ls /dev/snd/pcm* &>/dev/null; then
        AUDIO_SYSTEM="alsa"
        AUDIO_METHOD="alsa"
        echo "✅ Detected: ALSA (direct hardware)"
    else
        AUDIO_SYSTEM="none"
        AUDIO_METHOD="http"
        echo "⚠️  No audio system detected - using HTTP streaming"
    fi
    
    echo ""
    echo "Audio configuration: $AUDIO_SYSTEM ($AUDIO_METHOD)"
    
    # Auto-configure based on detection
    if [ "$AUDIO_SYSTEM" = "pipewire" ] || [ "$AUDIO_SYSTEM" = "pulseaudio" ]; then
        echo "✅ Native audio will work automatically"
        USE_PULSE_AUDIO="true"
    elif [ "$AUDIO_SYSTEM" = "alsa" ]; then
        echo "✅ Direct ALSA audio will be used"
        USE_PULSE_AUDIO="false"
    else
        echo "ℹ️  Will use HTTP streaming (browser playback)"
        USE_PULSE_AUDIO="false"
    fi
    
    echo ""
}

# Docker audio permissions setup
setup_audio_permissions() {
    if [ "$USE_PULSE_AUDIO" = "true" ]; then
        # Add user to audio group if not already
        if ! groups "$USER" | grep -q "audio"; then
            print_status "Adding $USER to audio group..."
            sudo usermod -aG audio "$USER"
            print_warning "Audio group added. You may need to log out/in for changes to take effect."
        fi
        
        # Check PulseAudio socket
        PULSE_SOCKET_DIR="/run/user/$(id -u)/pulse"
        if [ -d "$PULSE_SOCKET_DIR" ]; then
            print_success "PulseAudio socket found: $PULSE_SOCKET_DIR"
        else
            print_warning "PulseAudio socket not found. Audio may not work until after login."
        fi
    fi
}

# Function to check for existing Docker images
check_existing_docker_images() {
    local web_image_exists=false
    local containers_running=false
    
    # Check if web image exists
    if docker images maestro-mpd-control-web --format "{{.Repository}}" 2>/dev/null | grep -q "maestro-mpd-control-web"; then
        web_image_exists=true
    fi
    
    # Check if containers are running
    if docker ps --format "{{.Names}}" 2>/dev/null | grep -q "mpd-web-control"; then
        containers_running=true
    fi
    
    if [ "$web_image_exists" = true ]; then
        echo ""
        print_warning "Existing Docker image found: maestro-mpd-control-web"
        
        if [ "$containers_running" = true ]; then
            print_status "Containers are currently running"
        fi
        
        echo ""
        echo "Would you like to:"
        echo "1) Use existing image (skip build)"
        echo "2) Rebuild image (recommended for updates)"
        echo "3) Remove existing image and rebuild"
        echo "4) Exit setup"
        echo ""
        read -p "Choice [1/2/3/4]: " docker_choice
        
        case $docker_choice in
            1)
                print_success "Using existing Docker image"
                SKIP_DOCKER_BUILD=true
                return 0
                ;;
            2)
                print_status "Will rebuild Docker image"
                FORCE_DOCKER_BUILD=true
                return 0
                ;;
            3)
                print_status "Removing existing image and rebuilding..."
                if [ "$containers_running" = true ]; then
                    print_status "Stopping running containers..."
                    docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
                fi
                
                print_status "Removing Docker image..."
                docker rmi maestro-mpd-control-web 2>/dev/null || true
                
                # Also remove related images
                docker images --filter="reference=maestro-mpd-control*" -q | xargs -r docker rmi 2>/dev/null || true
                
                print_success "Existing image removed"
                FORCE_DOCKER_BUILD=true
                return 0
                ;;
            4)
                echo "Setup cancelled."
                exit 0
                ;;
            *)
                print_status "Using existing Docker image (default)"
                SKIP_DOCKER_BUILD=true
                return 0
                ;;
        esac
    else
        # No existing image, need to build
        FORCE_DOCKER_BUILD=true
        return 0
    fi
}

# Function to validate existing .env file
validate_env_file() {
    local env_file="$1"
    local validation_failed=false
    
    if [ ! -f "$env_file" ]; then
        return 1
    fi
    
    print_status "Validating existing .env configuration..."
    
    # Check for syntax errors by attempting to source it in a subshell
    if ! (set -e; source "$env_file" >/dev/null 2>&1); then
        print_error "Syntax errors found in .env file"
        validation_failed=true
    fi
    
    # Check for common issues
    if grep -q "RECENT_MUSIC_DIRS=.*[^,]\\s" "$env_file" 2>/dev/null; then
        print_error "Unquoted spaces found in RECENT_MUSIC_DIRS"
        validation_failed=true
    fi
    
    # Check for required variables
    local required_vars=("MUSIC_DIRECTORY" "MPD_HOST" "MPD_PORT" "WEB_PORT")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$env_file" 2>/dev/null; then
            print_warning "Missing required variable: $var"
        fi
    done
    
    if [ "$validation_failed" = true ]; then
        return 1
    else
        print_success "Configuration file validation passed"
        return 0
    fi
}

# Function to configure Recent Music Directories
configure_recent_dirs() {
    echo ""
    echo -e "${CYAN}⚡ Recent Albums Performance${NC}"
    echo "=============================="
    echo ""
    echo "For faster 'Recent Albums' loading, you can specify directories"
    echo "within your music library that contain your newest music."
    echo ""
    echo -e "${YELLOW}IMPORTANT: Enter directory NAMES only, not full paths!${NC}"
    echo ""
    echo "If your music library is: /media/music/"
    echo "And you have directories: /media/music/Downloads and /media/music/Recent"
    echo ""
    echo -e "${GREEN}Correct examples:${NC}"
    echo "  • Downloads,Recent"
    echo "  • New Releases,2024,2025"
    echo "  • Latest Albums,New Music"
    echo ""
    echo -e "${RED}Wrong examples:${NC}"
    echo "  • /media/music/Downloads (don't include full path)"
    echo "  • /home/user/Music/Recent (don't include full path)"
    echo ""
    echo "Leave empty to scan entire library (slower but comprehensive)"
    echo ""
    read -p "Recent music directory names (comma-separated) []: " RECENT_DIRS
}

# Function to detect and resolve MPD port conflicts
check_mpd_port_conflict() {
    local mpd_port=${1:-6600}
    
    if netstat -tln 2>/dev/null | grep -q ":${mpd_port}\\s"; then
        print_warning "Port ${mpd_port} is already in use"
        
        # Check if it's MPD
        if pgrep -x "mpd" > /dev/null; then
            print_status "Detected existing MPD server running"
            echo ""
            echo "Options:"
            echo "1) Use existing MPD server (recommended)"
            echo "2) Use containerized MPD on different port"
            echo "3) Stop existing MPD and use containerized"
            echo ""
            read -p "Choice [1/2/3]: " port_choice
            
            case $port_choice in
                1)
                    print_success "Will use existing MPD server"
                    MPD_HOST="localhost"
                    MPD_PORT="6600"
                    USE_CONTAINER_MPD=false
                    return 0
                    ;;
                2)
                    print_success "Will use containerized MPD on port 6601"
                    MPD_EXTERNAL_PORT="6601"
                    return 0
                    ;;
                3)
                    print_warning "Stopping existing MPD..."
                    sudo systemctl stop mpd 2>/dev/null || sudo pkill mpd
                    sleep 2
                    if ! netstat -tln 2>/dev/null | grep -q ":${mpd_port}\\s"; then
                        print_success "Existing MPD stopped"
                        return 0
                    else
                        print_error "Could not stop existing MPD"
                        exit 1
                    fi
                    ;;
                *)
                    print_success "Using existing MPD server (default)"
                    MPD_HOST="localhost"
                    MPD_PORT="6600"
                    USE_CONTAINER_MPD=false
                    return 0
                    ;;
            esac
        else
            print_warning "Port ${mpd_port} occupied by unknown service"
            MPD_EXTERNAL_PORT="6601"
            print_success "Will use port 6601 for containerized MPD"
        fi
    fi
    
    return 0
}

# Check Docker
if ! command -v docker >/dev/null 2>&1; then
    print_error "Docker is required but not installed."
    echo ""
    echo "Please install Docker:"
    echo "• Ubuntu/Debian: curl -fsSL https://get.docker.com | sh"
    echo "• macOS: Download Docker Desktop from docker.com"
    echo "• Windows: Download Docker Desktop from docker.com"
    echo ""
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    print_error "Docker Compose is required but not installed."
    echo ""
    echo "Please install Docker Compose:"
    echo "• Most Docker installations include Compose"
    echo "• Try: 'docker compose version' or install separately"
    echo ""
    exit 1
fi

# Determine compose command
COMPOSE_CMD="docker-compose"
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
fi

print_success "Docker and Docker Compose found"

# Check if .env already exists
if [ -f .env ]; then
    echo ""
    print_warning "Existing .env configuration found"
    
    # Validate the existing .env file
    if validate_env_file ".env"; then
        echo ""
        echo "Would you like to:"
        echo "1) Keep existing configuration"
        echo "2) Update Recent Music Directories only"
        echo "3) Reconfigure from scratch"
        echo "4) Exit setup"
        echo ""
        read -p "Choice [1/2/3/4]: " env_choice
        
        case $env_choice in
            1) 
                print_status "Using existing configuration"
                SKIP_CONFIG=true
                ;;
            2)
                print_status "Updating Recent Music Directories configuration"
                SKIP_CONFIG=true
                UPDATE_RECENT_DIRS=true
                ;;
            3) 
                rm -f .env && print_status "Removed existing configuration" 
                ;;
            4) 
                echo "Setup cancelled." && exit 0 
                ;;
            *) 
                print_status "Using existing configuration"
                SKIP_CONFIG=true
                ;;
        esac
    else
        echo ""
        print_error "Configuration file has errors and cannot be used safely"
        echo "Would you like to:"
        echo "1) Reconfigure from scratch (recommended)"
        echo "2) Exit setup"
        echo ""
        read -p "Choice [1/2]: " repair_choice
        
        case $repair_choice in
            1) 
                rm -f .env && print_status "Removed corrupted configuration" 
                ;;
            *) 
                echo "Setup cancelled." && exit 0 
                ;;
        esac
    fi
fi

# Handle Recent Directories update for existing configs
if [ "$UPDATE_RECENT_DIRS" = "true" ]; then
    echo ""
    print_status "Updating Recent Music Directories configuration..."
    
    # Source existing .env to get current values
    source .env 2>/dev/null || true
    
    configure_recent_dirs
    
    # Update just the RECENT_MUSIC_DIRS in existing .env
    if [ -n "$RECENT_DIRS" ]; then
        # Properly quote the value to handle spaces and commas
        escaped_dirs=$(printf '%s' "$RECENT_DIRS" | sed 's/"/\\"/g')
        if grep -q "^RECENT_MUSIC_DIRS=" .env; then
            sed -i "s/^RECENT_MUSIC_DIRS=.*/RECENT_MUSIC_DIRS=\"$escaped_dirs\"/" .env
        else
            echo "RECENT_MUSIC_DIRS=\"$escaped_dirs\"" >> .env
        fi
    else
        if grep -q "^RECENT_MUSIC_DIRS=" .env; then
            sed -i "s/^RECENT_MUSIC_DIRS=.*/RECENT_MUSIC_DIRS=/" .env
        else
            echo "RECENT_MUSIC_DIRS=" >> .env
        fi
    fi
    
    print_success "Recent Music Directories updated in .env"
fi

# Configuration wizard
if [ "$SKIP_CONFIG" != "true" ]; then
    echo ""
    print_status "$GEAR Starting configuration wizard..."
    echo ""
    
    # Music directory configuration
    echo -e "${CYAN}📁 Music Library Setup${NC}"
    echo "=============================="
    echo ""
    echo "Enter the path to your music directory:"
    echo "Examples:"
    echo "  • /home/username/Music"
    echo "  • /media/music"
    echo "  • /mnt/nas/music"
    echo ""
    
    while true; do
        read -p "Music directory: " MUSIC_DIR
        
        if [ -z "$MUSIC_DIR" ]; then
            print_error "Music directory cannot be empty"
            continue
        fi
        
        # Expand tilde
        MUSIC_DIR="${MUSIC_DIR/#\~/$HOME}"
        
        if [ -d "$MUSIC_DIR" ]; then
            # Check if directory has music files
            if find "$MUSIC_DIR" -type f \( -name "*.mp3" -o -name "*.flac" -o -name "*.m4a" -o -name "*.ogg" -o -name "*.wav" \) -print -quit | grep -q .; then
                print_success "Music directory found with audio files"
                break
            else
                print_warning "Directory exists but no audio files found"
                echo "Continue anyway? [y/N]: "
                read -r confirm
                if [[ $confirm =~ ^[Yy]$ ]]; then
                    break
                fi
            fi
        else
            print_error "Directory not found: $MUSIC_DIR"
            echo "Create it? [y/N]: "
            read -r create_dir
            if [[ $create_dir =~ ^[Yy]$ ]]; then
                mkdir -p "$MUSIC_DIR" 2>/dev/null || {
                    print_error "Failed to create directory. Check permissions."
                    continue
                }
                print_success "Directory created"
                break
            fi
        fi
    done
    
    echo ""
    # MPD server configuration
    echo -e "${CYAN}🎛️  MPD Server Configuration${NC}"
    echo "=============================="
    echo ""
    echo "Choose MPD setup:"
    echo "1) Use containerized MPD (recommended for new users)"
    echo "2) Connect to existing MPD server"
    echo ""
    read -p "Choice [1/2]: " mpd_choice
    
    case $mpd_choice in
        2)
            echo ""
            echo "Enter MPD server details:"
            read -p "MPD Host-(Some Users May need to put their local IP in here as opposed to) [localhost]: " MPD_HOST
            MPD_HOST=${MPD_HOST:-localhost}
            
            read -p "MPD Port [6600]: " MPD_PORT
            MPD_PORT=${MPD_PORT:-6600}
            
            # Test connection
            print_status "Testing MPD connection..."
            if timeout 3 bash -c "</dev/tcp/$MPD_HOST/$MPD_PORT" 2>/dev/null; then
                print_success "MPD server is reachable"
            else
                print_warning "Cannot connect to $MPD_HOST:$MPD_PORT"
                echo "Continue anyway? [y/N]: "
                read -r continue_anyway
                if [[ ! $continue_anyway =~ ^[Yy]$ ]]; then
                    echo "Setup cancelled."
                    exit 1
                fi
            fi
            
            USE_CONTAINER_MPD="false"
            ;;
        *)
            print_status "Using containerized MPD"
            MPD_HOST="mpd"
            MPD_PORT="6600"
            USE_CONTAINER_MPD="true"
            
            # Check for port conflicts with containerized MPD
            check_mpd_port_conflict 6600
            
            if [ "$USE_CONTAINER_MPD" = "true" ]; then
                print_success "Will use containerized MPD server"
            else
                print_success "Switched to existing MPD server"
            fi
            ;;
    esac
    
    echo ""
    # Web interface configuration
    echo -e "${CYAN}🌐 Web Interface Configuration${NC}"
    echo "=============================="
    echo ""
    read -p "Web interface port [5003]: " WEB_PORT
    WEB_PORT=${WEB_PORT:-5003}
    
    # Check if port is available
    if command -v netstat >/dev/null 2>&1; then
        if netstat -tuln 2>/dev/null | grep -q ":$WEB_PORT "; then
            print_warning "Port $WEB_PORT appears to be in use"
        fi
    fi
    
    echo ""
    # Theme selection
    echo -e "${CYAN}🎨 Default Theme Selection${NC}"
    echo "=============================="
    echo ""
    echo "Choose default theme:"
    echo "1) Dark (default)"
    echo "2) Light"
    echo "3) High Contrast"
    echo "4) Desert"
    echo ""
    read -p "Theme choice [1/2/3/4]: " theme_choice
    
    case $theme_choice in
        2) DEFAULT_THEME="light" ;;
        3) DEFAULT_THEME="high-contrast" ;;
        4) DEFAULT_THEME="desert" ;;
        *) DEFAULT_THEME="dark" ;;
    esac
    
    echo ""
    # Last.fm integration
    echo -e "${CYAN}🎵 Last.fm Integration (Optional)${NC}"
    echo "=============================="
    echo ""
    echo "Last.fm provides music charts and scrobbling features."
    echo "You'll need API credentials from: https://www.last.fm/api"
    echo ""
    echo "Enable Last.fm integration? [y/N]: "
    read -r enable_lastfm
    
    LASTFM_API_KEY=""
    LASTFM_SECRET=""
    if [[ $enable_lastfm =~ ^[Yy]$ ]]; then
        echo ""
        read -p "Last.fm API Key: " LASTFM_API_KEY
        read -s -p "Last.fm Shared Secret: " LASTFM_SECRET
        echo ""
        
        if [ -n "$LASTFM_API_KEY" ] && [ -n "$LASTFM_SECRET" ]; then
            print_success "Last.fm credentials configured"
        else
            print_warning "Last.fm credentials incomplete, features will be disabled"
            LASTFM_API_KEY=""
            LASTFM_SECRET=""
        fi
    fi
    
    # Recent Albums performance configuration
    configure_recent_dirs
    
    # Automatic audio system detection
    echo ""
    auto_detect_audio
    setup_audio_permissions
    
    # Generate .env file
    print_status "Generating configuration..."
    
    cat > .env << EOF
# Maestro MPD Control - Docker Configuration
# Generated on $(date)

# Music Library
MUSIC_DIRECTORY=$MUSIC_DIR

# MPD Configuration
MPD_HOST=$MPD_HOST
MPD_PORT=$MPD_PORT
MPD_TIMEOUT=10

# Web Interface
WEB_PORT=$WEB_PORT
DEFAULT_THEME=$DEFAULT_THEME

# Last.fm Integration (Optional)
LASTFM_API_KEY=$LASTFM_API_KEY
LASTFM_SHARED_SECRET=$LASTFM_SECRET

# Auto-Fill Settings
AUTO_FILL_ENABLED=true
AUTO_FILL_MIN_TRACKS=3
AUTO_FILL_MAX_TRACKS=7

# Recent Albums Performance
RECENT_MUSIC_DIRS="$RECENT_DIRS"

# Audio Configuration (auto-detected)
AUDIO_SYSTEM=$AUDIO_SYSTEM
USE_PULSE_AUDIO=$USE_PULSE_AUDIO

# Security
SECRET_KEY=maestro-docker-$(date +%s)-$(shuf -i 1000-9999 -n 1)

# Docker Settings
EOF
    
    if [ "$USE_CONTAINER_MPD" = "true" ]; then
        echo "COMPOSE_PROFILES=with-mpd" >> .env
    fi
    
    print_success "Configuration saved to .env"
fi

# Create data directory for persistent storage
mkdir -p data
print_status "Created data directory for persistent storage"

echo ""
print_status "$DOCKER Starting Docker deployment..."

# Check for existing Docker images
check_existing_docker_images

# Build and start services
if [ -f .env ]; then
    source .env
fi

# Determine which profile to use
if [ "$USE_CONTAINER_MPD" = "true" ] || grep -q "COMPOSE_PROFILES.*with-mpd" .env 2>/dev/null; then
    PROFILE_ARG="--profile with-mpd"
    print_status "Starting with containerized MPD server"
else
    PROFILE_ARG=""
    print_status "Starting web interface (connecting to external MPD)"
fi

# Pre-create and fix MPD volumes if using containerized MPD
if [ "$USE_CONTAINER_MPD" = "true" ] || grep -q "COMPOSE_PROFILES.*with-mpd" .env 2>/dev/null; then
    print_status "Preparing MPD volumes with correct permissions..."
    
    # Create volumes with proper ownership
    docker run --rm \
        -v mpd_web_control_db:/var/lib/mpd \
        -v mpd_web_control_playlists:/var/lib/mpd/playlists \
        --user root \
        vimagick/mpd:latest \
        sh -c "
            mkdir -p /var/lib/mpd/playlists
            chown -R 1000:1000 /var/lib/mpd
            chmod -R 755 /var/lib/mpd
        " 2>/dev/null || print_warning "Volume preparation failed (may already exist)"
fi

# Start services
if [ "$SKIP_DOCKER_BUILD" = "true" ]; then
    print_status "Starting services with existing Docker image..."
    if $COMPOSE_CMD $PROFILE_ARG up -d; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services with existing image"
        echo ""
        echo "The existing image may be incompatible. Try rebuilding:"
        echo "  $COMPOSE_CMD $PROFILE_ARG up -d --build"
        exit 1
    fi
else
    print_status "Building and starting containers..."
    if $COMPOSE_CMD $PROFILE_ARG up -d --build; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        echo ""
        echo "Check logs with: $COMPOSE_CMD logs"
        exit 1
    fi
fi

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 10

# Health check
print_status "Checking service health..."

# Check web service
if curl -s -f "http://localhost:${WEB_PORT:-5003}/api/version" >/dev/null 2>&1; then
    print_success "Web interface is healthy"
    WEB_HEALTHY=true
else
    print_warning "Web interface health check failed"
    WEB_HEALTHY=false
fi

# Check MPD if containerized
if [ "$USE_CONTAINER_MPD" = "true" ] || grep -q "COMPOSE_PROFILES.*with-mpd" .env 2>/dev/null; then
    if echo "ping" | nc -w 2 localhost 6600 2>/dev/null | grep -q "OK"; then
        print_success "MPD server is healthy"
        MPD_HEALTHY=true
    else
        print_warning "MPD server health check failed - attempting to fix..."
        
        # Fix MPD volume permissions
        print_status "Fixing MPD database permissions..."
        
        # Stop MPD container first
        $COMPOSE_CMD stop mpd 2>/dev/null
        
        # Fix volume ownership using a temporary container
        docker run --rm \
            -v mpd_web_control_db:/var/lib/mpd \
            -v mpd_web_control_playlists:/var/lib/mpd/playlists \
            --user root \
            vimagick/mpd:latest \
            sh -c "
                chown -R 1000:1000 /var/lib/mpd
                chmod -R 755 /var/lib/mpd
                mkdir -p /var/lib/mpd/playlists
                chown -R 1000:1000 /var/lib/mpd/playlists
            " 2>/dev/null
            
        print_success "Fixed MPD volume permissions"
        
        # Restart MPD container
        print_status "Restarting MPD container..."
        $COMPOSE_CMD $PROFILE_ARG up -d mpd
        
        # Wait and test again
        sleep 5
        if echo "ping" | nc -w 3 localhost 6600 2>/dev/null | grep -q "OK"; then
            print_success "MPD server is now healthy"
            MPD_HEALTHY=true
        else
            print_warning "MPD server still unhealthy - check logs: $COMPOSE_CMD logs mpd"
            MPD_HEALTHY=false
        fi
    fi
fi

echo ""
if [ "$WEB_HEALTHY" = "true" ]; then
    echo -e "${GREEN}$ROCKET Setup Complete! $ROCKET${NC}"
    echo ""
    echo -e "${CYAN}🌐 Web Interface:${NC} http://localhost:${WEB_PORT:-5003}"
    echo -e "${CYAN}🎨 Available Themes:${NC} Dark • Light • High Contrast • Desert"
    echo -e "${CYAN}📱 Mobile Support:${NC} Fully responsive design"
    
    if [ -n "$LASTFM_API_KEY" ]; then
        echo -e "${CYAN}🎵 Last.fm Features:${NC} Charts and scrobbling enabled"
    fi
    
    echo ""
    echo -e "${BLUE}📋 Management Commands:${NC}"
    echo "  View logs:     $COMPOSE_CMD logs -f"
    echo "  Stop services: $COMPOSE_CMD down"
    echo "  Restart:       $COMPOSE_CMD restart"
    echo "  Update:        $COMPOSE_CMD pull && $COMPOSE_CMD up -d"
    
    if [ "$USE_CONTAINER_MPD" = "true" ] || grep -q "COMPOSE_PROFILES.*with-mpd" .env 2>/dev/null; then
        echo ""
        echo -e "${BLUE}🎛️  MPD Information:${NC}"
        echo "  MPD Port:      localhost:6600"
        echo "  Music Scan:    Automatic on container start"
        echo "  Database:      Persistent across restarts"
    fi
    
    echo ""
    echo -e "${BLUE}💾 Data Persistence:${NC}"
    echo "  Settings:      ./data/settings.json"
    echo "  Radio Stations:./data/radio_stations.json"
    echo "  Album Cache:   Docker volume 'mpd_web_control_cache'"
    
else
    echo -e "${YELLOW}$WARN Setup completed with warnings${NC}"
    echo ""
    echo "Some services may not be ready yet. Check status with:"
    echo "  $COMPOSE_CMD ps"
    echo "  $COMPOSE_CMD logs"
    echo ""
    echo "Web interface should be available at: http://localhost:${WEB_PORT:-5003}"
fi

# Post-deployment validation
echo ""
echo -e "${CYAN}$ROCKET Post-Deployment Validation${NC}"
validate_deployment

echo ""
echo -e "${PURPLE}🎵 Enjoy your music! 🎵${NC}"
