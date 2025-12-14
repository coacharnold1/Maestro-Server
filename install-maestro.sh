#!/bin/bash

#==============================================================================
# Maestro MPD Control - Complete Installation Script
# Supports: Ubuntu Server 20.04+, Debian 11+, Arch Linux
# Components: MPD, Web UI (port 5003), Admin API (port 5004)
#==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/maestro"
WEB_PORT=5003
ADMIN_PORT=5004
MPD_PORT=6600
MUSIC_DIR="/media/music"

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    else
        echo -e "${RED}Cannot detect OS. Unsupported system.${NC}"
        exit 1
    fi
}

# Print banner
print_banner() {
    clear
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║          MAESTRO MPD CONTROL - INSTALLER v2.0             ║"
    echo "║                                                            ║"
    echo "║  Complete Music Server with Web UI and Admin Interface    ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        echo -e "${RED}Please do NOT run this script as root!${NC}"
        echo "Run as normal user. Sudo will be used when needed."
        exit 1
    fi
}

# Install system dependencies
install_dependencies() {
    echo -e "${GREEN}[1/8] Installing system dependencies...${NC}"
    
    case "$OS" in
        ubuntu|debian)
            sudo apt update
            sudo apt install -y \
                mpd mpc \
                python3 python3-pip python3-venv \
                alsa-utils \
                nfs-common cifs-utils \
                curl wget git \
                build-essential
            ;;
        arch|manjaro)
            sudo pacman -Syu --noconfirm \
                mpd mpc \
                python python-pip \
                alsa-utils \
                nfs-utils cifs-utils \
                curl wget git \
                base-devel
            ;;
        *)
            echo -e "${RED}Unsupported OS: $OS${NC}"
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}✓ Dependencies installed${NC}"
}

# Configure MPD
configure_mpd() {
    echo -e "${GREEN}[2/8] Configuring MPD...${NC}"
    
    # Create music directory
    sudo mkdir -p "$MUSIC_DIR"
    sudo chown $USER:$USER "$MUSIC_DIR"
    
    # Backup existing MPD config
    if [ -f /etc/mpd.conf ]; then
        sudo cp /etc/mpd.conf /etc/mpd.conf.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Create MPD config
    sudo tee /etc/mpd.conf > /dev/null <<EOF
# Maestro MPD Configuration
# Music directory
music_directory     "$MUSIC_DIR"

# Database and state files
playlist_directory  "/var/lib/mpd/playlists"
db_file             "/var/lib/mpd/database"
log_file            "/var/log/mpd/mpd.log"
pid_file            "/run/mpd/pid"
state_file          "/var/lib/mpd/state"
sticker_file        "/var/lib/mpd/sticker.sql"

# Network settings
bind_to_address     "0.0.0.0"
port                "$MPD_PORT"

# User and permissions
user                "mpd"

# Audio output (ALSA)
audio_output {
    type            "alsa"
    name            "ALSA Output"
    mixer_type      "none"
}

# Audio output (HTTP stream)
audio_output {
    type            "httpd"
    name            "HTTP Stream"
    encoder         "lame"
    port            "8000"
    bitrate         "320"
    format          "44100:16:2"
    always_on       "yes"
    tags            "yes"
}

# Audiophile settings
audio_buffer_size   "4096"
buffer_before_play  "10%"
max_output_buffer_size  "16384"

# Resampling (disabled for bit-perfect)
#samplerate_converter    "Fastest Sinc Interpolator"

# Logging
log_level           "default"

# Auto-update database
auto_update         "yes"
auto_update_depth   "3"
EOF

    # Create necessary directories
    sudo mkdir -p /var/lib/mpd/playlists
    sudo mkdir -p /var/log/mpd
    sudo chown -R mpd:audio /var/lib/mpd /var/log/mpd
    
    # Enable and start MPD
    sudo systemctl enable mpd
    sudo systemctl restart mpd
    
    # Wait for MPD to start
    sleep 2
    
    echo -e "${GREEN}✓ MPD configured and running${NC}"
}

# Create installation directory
create_install_dir() {
    echo -e "${GREEN}[3/8] Creating installation directory...${NC}"
    
    mkdir -p "$INSTALL_DIR"/{web,admin,config,logs}
    
    echo -e "${GREEN}✓ Directory structure created${NC}"
}

# Install Web UI
install_web_ui() {
    echo -e "${GREEN}[4/8] Installing Web UI...${NC}"
    
    # Copy web UI files
    if [ -f "$HOME/Maestro-Server/app.py" ]; then
        cp -r "$HOME/Maestro-Server"/{app.py,templates,static,requirements.txt} "$INSTALL_DIR/web/" 2>/dev/null || true
        cp -r "$HOME/Maestro-Server"/data "$INSTALL_DIR/web/" 2>/dev/null || true
    elif [ -f "app.py" ]; then
        # Running from Maestro-Server directory
        cp -r {app.py,templates,static,requirements.txt} "$INSTALL_DIR/web/" 2>/dev/null || true
        cp -r data "$INSTALL_DIR/web/" 2>/dev/null || true
    elif [ -f "$HOME/Maestro-MPD-Control/app.py" ]; then
        cp -r "$HOME/Maestro-MPD-Control"/{app.py,templates,static,requirements.txt} "$INSTALL_DIR/web/" 2>/dev/null || true
    else
        echo -e "${YELLOW}Warning: Web UI source not found in ~/Maestro-Server, current directory, or ~/Maestro-MPD-Control${NC}"
        return
    fi
    # Create virtual environment
    cd "$INSTALL_DIR/web"
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install --upgrade pip
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt
    else
        # Install common dependencies
        pip install flask flask-socketio python-mpd2 werkzeug
    fi
    
    deactivate
    
    echo -e "${GREEN}✓ Web UI installed${NC}"
}

# Install Admin API
install_admin_api() {
    echo -e "${GREEN}[5/8] Installing Admin API...${NC}"
    
    # Check if admin API exists
    if [ -d "$HOME/Maestro-Server/admin" ]; then
        cp -r "$HOME/Maestro-Server/admin"/* "$INSTALL_DIR/admin/"
    elif [ -d "admin" ]; then
        # Running from Maestro-Server directory
        cp -r admin/* "$INSTALL_DIR/admin/"
    else
        # Create admin API from scratch
        mkdir -p "$INSTALL_DIR/admin/templates"
        
        # Create requirements.txt
        cat > "$INSTALL_DIR/admin/requirements.txt" <<EOF
Flask==3.0.0
flask-socketio==5.3.5
psutil==5.9.6
python-engineio==4.8.0
python-socketio==5.10.0
python-mpd2==3.1.0
EOF
        
        echo -e "${YELLOW}Warning: Admin API source not found. Creating placeholder...${NC}"
    fi
    
    # Create virtual environment
    cd "$INSTALL_DIR/admin"
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install --upgrade pip
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt
    else
        pip install Flask flask-socketio psutil python-mpd2
    fi
    
    deactivate
    
    # Create config directory
    mkdir -p "$HOME/.config/maestro"
    
    echo -e "${GREEN}✓ Admin API installed${NC}"
}

# Configure sudo permissions
configure_sudo() {
    echo -e "${GREEN}[6/8] Configuring sudo permissions...${NC}"
    
    SUDOERS_FILE="/etc/sudoers.d/maestro"
    
    sudo tee "$SUDOERS_FILE" > /dev/null <<EOF
# Maestro MPD Control - Sudo permissions
# Allow user to run system management commands without password

$USER ALL=(ALL) NOPASSWD: /usr/bin/apt update
$USER ALL=(ALL) NOPASSWD: /usr/bin/apt upgrade
$USER ALL=(ALL) NOPASSWD: /usr/bin/pacman
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart mpd
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop mpd
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl start mpd
$USER ALL=(ALL) NOPASSWD: /sbin/shutdown
$USER ALL=(ALL) NOPASSWD: /sbin/reboot
$USER ALL=(ALL) NOPASSWD: /bin/mount
$USER ALL=(ALL) NOPASSWD: /bin/umount
$USER ALL=(ALL) NOPASSWD: /usr/sbin/aplay
EOF
    
    sudo chmod 440 "$SUDOERS_FILE"
    
    echo -e "${GREEN}✓ Sudo permissions configured${NC}"
}

# Create systemd services
create_systemd_services() {
    echo -e "${GREEN}[7/8] Creating systemd services...${NC}"
    
    # Web UI service
    sudo tee /etc/systemd/system/maestro-web.service > /dev/null <<EOF
[Unit]
Description=Maestro Web UI
After=network.target mpd.service
Wants=mpd.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR/web
Environment="PATH=$INSTALL_DIR/web/venv/bin"
ExecStart=$INSTALL_DIR/web/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Admin API service
    sudo tee /etc/systemd/system/maestro-admin.service > /dev/null <<EOF
[Unit]
Description=Maestro Admin API
After=network.target mpd.service
Wants=mpd.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR/admin
Environment="PATH=$INSTALL_DIR/admin/venv/bin"
ExecStart=$INSTALL_DIR/admin/venv/bin/python3 admin_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable services
    sudo systemctl enable maestro-web.service
    sudo systemctl enable maestro-admin.service
    
    echo -e "${GREEN}✓ Systemd services created${NC}"
}

# Start services
start_services() {
    echo -e "${GREEN}[8/8] Starting Maestro services...${NC}"
    
    # Start web UI
    if [ -f "$INSTALL_DIR/web/app.py" ]; then
        sudo systemctl start maestro-web.service
        sleep 2
        if systemctl is-active --quiet maestro-web.service; then
            echo -e "${GREEN}✓ Web UI started on port $WEB_PORT${NC}"
        else
            echo -e "${YELLOW}⚠ Web UI failed to start. Check logs: journalctl -u maestro-web${NC}"
        fi
    fi
    
    # Start admin API
    if [ -f "$INSTALL_DIR/admin/admin_api.py" ]; then
        sudo systemctl start maestro-admin.service
        sleep 2
        if systemctl is-active --quiet maestro-admin.service; then
            echo -e "${GREEN}✓ Admin API started on port $ADMIN_PORT${NC}"
        else
            echo -e "${YELLOW}⚠ Admin API failed to start. Check logs: journalctl -u maestro-admin${NC}"
        fi
    fi
}

# Get server IP
get_server_ip() {
    IP=$(ip route get 8.8.8.8 | awk '{print $7; exit}')
    echo "$IP"
}

# Print success message
print_success() {
    IP=$(get_server_ip)
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                            ║${NC}"
    echo -e "${GREEN}║           🎉 MAESTRO INSTALLATION COMPLETE! 🎉            ║${NC}"
    echo -e "${GREEN}║                                                            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📍 Installation Directory:${NC} $INSTALL_DIR"
    echo -e "${BLUE}🎵 Music Directory:${NC} $MUSIC_DIR"
    echo ""
    echo -e "${BLUE}🌐 Access URLs:${NC}"
    echo -e "   Web UI:    ${GREEN}http://$IP:$WEB_PORT${NC}"
    echo -e "   Admin API: ${GREEN}http://$IP:$ADMIN_PORT${NC}"
    echo -e "   MPD:       ${GREEN}$IP:$MPD_PORT${NC}"
    echo ""
    echo -e "${BLUE}📋 Service Management:${NC}"
    echo -e "   Web UI:    ${YELLOW}sudo systemctl {start|stop|restart|status} maestro-web${NC}"
    echo -e "   Admin API: ${YELLOW}sudo systemctl {start|stop|restart|status} maestro-admin${NC}"
    echo -e "   MPD:       ${YELLOW}sudo systemctl {start|stop|restart|status} mpd${NC}"
    echo ""
    echo -e "${BLUE}📁 Add Music:${NC}"
    echo -e "   1. Copy music to: ${GREEN}$MUSIC_DIR${NC}"
    echo -e "   2. Or mount network shares via Admin API"
    echo -e "   3. Update MPD library: ${YELLOW}mpc update${NC}"
    echo ""
    echo -e "${BLUE}🔧 Logs:${NC}"
    echo -e "   Web UI:    ${YELLOW}journalctl -u maestro-web -f${NC}"
    echo -e "   Admin API: ${YELLOW}journalctl -u maestro-admin -f${NC}"
    echo -e "   MPD:       ${YELLOW}journalctl -u mpd -f${NC}"
    echo ""
    echo -e "${GREEN}✨ Next Steps:${NC}"
    echo -e "   1. Open ${GREEN}http://$IP:$ADMIN_PORT${NC} to configure system"
    echo -e "   2. Add network shares in Library Management"
    echo -e "   3. Configure audio settings in Audio Tweaks"
    echo -e "   4. Open ${GREEN}http://$IP:$WEB_PORT${NC} to play music!"
    echo ""
}

# Main installation flow
main() {
    print_banner
    check_root
    detect_os
    
    echo -e "${BLUE}Detected OS:${NC} $OS $VERSION"
    echo -e "${BLUE}Installation Directory:${NC} $INSTALL_DIR"
    echo ""
    
    read -p "Press Enter to begin installation or Ctrl+C to cancel..."
    echo ""
    
    install_dependencies
    configure_mpd
    create_install_dir
    install_web_ui
    install_admin_api
    configure_sudo
    create_systemd_services
    start_services
    
    print_success
}

# Run main installation
main
