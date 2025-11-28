#!/bin/bash

# MPD Web Control - Enhanced Installation Script
# Distribution-agnostic installation with environment detection

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

echo "=================================="
echo "🎵 MPD Web Control Enhanced Installer"
echo "=================================="
echo

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APP_USER=$(whoami)

log_info "Application directory: $SCRIPT_DIR"
log_info "Installing for user: $APP_USER"
echo

# Function to detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    elif command -v lsb_release >/dev/null 2>&1; then
        DISTRO=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
        VERSION=$(lsb_release -sr)
    elif [ -f /etc/redhat-release ]; then
        DISTRO="rhel"
    else
        DISTRO="unknown"
    fi
    
    log_info "Detected OS: $DISTRO $VERSION"
}

# Function to install dependencies based on distro
install_dependencies() {
    log_info "Installing system dependencies..."
    
    case $DISTRO in
        ubuntu|debian)
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv python3-dev mpd
            ;;
        fedora)
            sudo dnf install -y python3 python3-pip python3-virtualenv python3-devel mpd
            ;;
        rhel|centos)
            sudo yum install -y python3 python3-pip python3-virtualenv python3-devel mpd
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm python python-pip python-virtualenv mpd
            ;;
        opensuse*)
            sudo zypper install -y python3 python3-pip python3-virtualenv python3-devel mpd
            ;;
        *)
            log_warning "Unknown distribution. Please install manually:"
            log_warning "- Python 3.7+"
            log_warning "- pip and virtualenv"
            log_warning "- MPD (Music Player Daemon)"
            read -p "Continue anyway? (y/N): " -n 1 -r
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
            ;;
    esac
    
    log_success "Dependencies installation completed"
}

# Function to detect music directory
detect_music_directory() {
    local MUSIC_DIRS=(
        "$HOME/Music"
        "/home/$APP_USER/Music" 
        "/media/music"
        "/mnt/music"
        "/var/lib/mpd/music"
        "/usr/share/mpd/music"
    )
    
    log_info "Detecting music directory..."
    
    for dir in "${MUSIC_DIRS[@]}"; do
        if [ -d "$dir" ] && [ -r "$dir" ]; then
            # Check if directory has music files
            if find "$dir" -name "*.mp3" -o -name "*.flac" -o -name "*.ogg" -o -name "*.m4a" | head -1 | grep -q .; then
                DETECTED_MUSIC_DIR="$dir"
                log_success "Found music directory: $DETECTED_MUSIC_DIR"
                return 0
            fi
        fi
    done
    
    log_warning "No music directory auto-detected"
    return 1
}

# Function to configure MPD
configure_mpd() {
    log_info "Configuring MPD..."
    
    local MPD_CONFIG="/etc/mpd.conf"
    local USER_MPD_CONFIG="$HOME/.config/mpd/mpd.conf"
    local USER_MPD_DIR="$HOME/.config/mpd"
    
    # Check if system MPD is running
    if systemctl is-active --quiet mpd 2>/dev/null; then
        log_success "System MPD service is already running"
        return 0
    fi
    
    # Set up user MPD configuration
    log_info "Setting up user MPD configuration..."
    mkdir -p "$USER_MPD_DIR"
    mkdir -p "$HOME/.local/share/mpd/playlists"
    
    cat > "$USER_MPD_CONFIG" << EOF
# MPD Configuration for MPD Web Control
music_directory    "$MUSIC_DIR"
playlist_directory "$HOME/.local/share/mpd/playlists"
db_file            "$USER_MPD_DIR/mpd.db"
log_file           "$USER_MPD_DIR/mpd.log"
pid_file           "$USER_MPD_DIR/mpd.pid"
state_file         "$USER_MPD_DIR/mpdstate"

bind_to_address    "127.0.0.1"
port               "6600"

audio_output {
    type    "pulse"
    name    "PulseAudio"
}

audio_output {
    type    "alsa"
    name    "ALSA"
}
EOF

    log_success "MPD configuration created at $USER_MPD_CONFIG"
}

# Function to setup Python environment
setup_python_environment() {
    log_info "Setting up Python virtual environment..."
    
    cd "$SCRIPT_DIR"
    
    # Remove existing venv if present
    if [ -d "venv" ]; then
        log_warning "Removing existing virtual environment..."
        rm -rf venv
    fi
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "Python dependencies installed"
    else
        log_error "requirements.txt not found!"
        exit 1
    fi
}

# Function to configure application
configure_application() {
    log_info "Configuring application settings..."
    
    # Create config.env from template if it doesn't exist
    if [ ! -f "$SCRIPT_DIR/config.env" ]; then
        if [ -f "$SCRIPT_DIR/config.env.example" ]; then
            cp "$SCRIPT_DIR/config.env.example" "$SCRIPT_DIR/config.env"
            log_success "Created config.env from template"
        else
            log_error "No configuration template found!"
            exit 1
        fi
    fi
    
    # Update music directory in config
    if [ -n "$MUSIC_DIR" ]; then
        sed -i "s|MUSIC_DIRECTORY=.*|MUSIC_DIRECTORY=$MUSIC_DIR|" "$SCRIPT_DIR/config.env"
        log_success "Updated music directory in config: $MUSIC_DIR"
    fi
    
    # Generate a secure secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" "$SCRIPT_DIR/config.env"
    log_success "Generated secure secret key"
    
    # Prompt for Last.fm API keys
    echo
    log_info "Last.fm API configuration (optional - press Enter to skip):"
    read -p "Enter Last.fm API Key (or press Enter): " LASTFM_KEY
    read -p "Enter Last.fm Shared Secret (or press Enter): " LASTFM_SECRET
    
    if [ -n "$LASTFM_KEY" ]; then
        sed -i "s|LASTFM_API_KEY=.*|LASTFM_API_KEY=$LASTFM_KEY|" "$SCRIPT_DIR/config.env"
        log_success "Last.fm API key configured"
    fi
    
    if [ -n "$LASTFM_SECRET" ]; then
        sed -i "s|LASTFM_SHARED_SECRET=.*|LASTFM_SHARED_SECRET=$LASTFM_SECRET|" "$SCRIPT_DIR/config.env"
        log_success "Last.fm shared secret configured"
    fi
}

# Function to setup systemd service
setup_service() {
    echo
    read -p "🔧 Install as system service? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "$SCRIPT_DIR/install_service.sh" ]; then
            sudo "$SCRIPT_DIR/install_service.sh"
        else
            log_error "Service installation script not found!"
            exit 1
        fi
    else
        log_info "Skipping service installation. Run manually with: python app.py"
    fi
}

# Function to test installation
test_installation() {
    log_info "Testing installation..."
    
    cd "$SCRIPT_DIR"
    source venv/bin/activate
    
    # Quick Python import test
    python3 -c "import flask; import python_mpd2; print('✅ Core dependencies OK')" || {
        log_error "Dependency test failed!"
        exit 1
    }
    
    log_success "Installation test passed"
}

# Main installation flow
main() {
    detect_distro
    echo
    
    # Check for root privileges for dependency installation
    if [ "$EUID" -eq 0 ]; then
        log_error "Don't run this script as root! Run as your regular user."
        exit 1
    fi
    
    # Install dependencies (will ask for sudo)
    install_dependencies
    
    # Detect music directory
    if detect_music_directory; then
        MUSIC_DIR="$DETECTED_MUSIC_DIR"
    else
        echo
        read -p "Enter your music directory path: " MUSIC_DIR
        if [ ! -d "$MUSIC_DIR" ]; then
            log_error "Directory $MUSIC_DIR does not exist!"
            exit 1
        fi
    fi
    
    # Configure MPD
    configure_mpd
    
    # Setup Python environment
    setup_python_environment
    
    # Configure application
    configure_application
    
    # Test installation
    test_installation
    
    # Setup service
    setup_service
    
    echo
    echo "======================================="
    log_success "Installation completed successfully!"
    echo "======================================="
    echo
    log_info "Next steps:"
    echo "  1. Start MPD: mpd ~/.config/mpd/mpd.conf"
    echo "  2. Access web interface at: http://localhost:5003"
    echo "  3. Check logs: journalctl -u mpd-web-control -f (if using service)"
    echo
    log_info "Configuration file: $SCRIPT_DIR/config.env"
    log_info "Music directory: $MUSIC_DIR"
    echo
}

# Run main function
main "$@"