#!/bin/bash

#==============================================================================
# Maestro MPD Control - Script di Installazione Completo
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
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_PORT=5003
ADMIN_PORT=5004
MPD_PORT=6600
MUSIC_DIR="/media/music"
RECENT_DIR=""
DEFAULT_THEME="dark"
MPD_INSTALL_TYPE=""
MPD_BINARY_PATH=""

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    else
        echo -e "${RED}Impossibile rilevare il sistema operativo. Sistema non supportato.${NC}"
        exit 1
    fi
}

# Print banner
print_banner() {
    clear
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║          MAESTRO MPD CONTROL - INSTALLATORE v2.0             ║"
    echo "║                                                            ║"
    echo "║  Server Musicale Completo con Interfaccia Web e Pannello Admin    ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

# Check if in esecuzione as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        echo -e "${RED}Per favore NON eseguire questo script come root!${NC}"
        echo "Esegui come utente normale. Sudo verrà utilizzato quando necessario."
        exit 1
    fi
}

# Detect existing MPD installation
detect_mpd() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Verifica Installazione MPD${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    local mpd_locations=("/usr/local/bin/mpd" "/usr/bin/mpd" "/opt/mpd/bin/mpd" "$HOME/.local/bin/mpd" "$HOME/mpd/bin/mpd")
    local found_mpd=""
    
    for loc in "${mpd_locations[@]}"; do
        if [ -x "$loc" ]; then
            found_mpd="$loc"
            break
        fi
    done
    
    if [ -z "$found_mpd" ] && command -v mpd &> /dev/null; then
        found_mpd=$(which mpd)
    fi
    
    if [ -n "$found_mpd" ]; then
        echo -e "${GREEN}✓ MPD esistente trovato: ${YELLOW}$found_mpd${NC}"
        if $found_mpd --version &> /dev/null; then
            echo -e "  Versione: ${YELLOW}$($found_mpd --version 2>&1 | head -1)${NC}"
        fi
        
        local is_package=false
        case "$OS" in
            ubuntu|debian)
                dpkg -l mpd 2>/dev/null | grep -q "^ii" && is_package=true
                ;;
            arch|manjaro)
                pacman -Q mpd 2>/dev/null && is_package=true
                ;;
        esac
        
        [ "$is_package" = true ] && echo -e "  Tipo: ${YELLOW}Pacchetto di sistema${NC}" || echo -e "  Tipo: ${YELLOW}Build personalizzata/locale${NC}"
        
        echo ""
        echo "1) Usa MPD esistente"
        echo "2) Installa nuovo MPD dal package manager"
        echo "3) Salta installazione MPD"
        read -p "Scelta (1-3): " mpd_choice
        
        case $mpd_choice in
            1) MPD_INSTALL_TYPE="existing"; MPD_BINARY_PATH="$found_mpd"; echo -e "${GREEN}✓ Uso MPD esistente${NC}" ;;
            2) MPD_INSTALL_TYPE="package"; echo -e "${YELLOW}⚠ Verrà installato il pacchetto MPD${NC}" ;;
            3) MPD_INSTALL_TYPE="skip"; echo -e "${YELLOW}⚠ Installazione MPD saltata${NC}" ;;
            *) MPD_INSTALL_TYPE="existing"; MPD_BINARY_PATH="$found_mpd"; echo -e "${GREEN}✓ Uso MPD esistente${NC}" ;;
        esac
    else
        echo -e "${YELLOW}Nessun MPD esistente trovato${NC}"
        read -p "Installare MPD dal package manager? (Y/n): "
        [[ ! $REPLY =~ ^[Nn]$ ]] && MPD_INSTALL_TYPE="package" || MPD_INSTALL_TYPE="skip"
    fi
    echo ""
}

# Prompt for directories
prompt_directories() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Configurazione Directory${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ -d "/media/music" ]; then
        echo -e "Trovato: ${GREEN}/media/music${NC}"
        read -p "Usare questa directory? (Y/n): "
        [[ ! $REPLY =~ ^[Nn]$ ]] && MUSIC_DIR="/media/music" || read -p "Inserisci directory musica: " MUSIC_DIR
    else
        read -p "Directory musica (predefinito /media/music): " MUSIC_DIR
        MUSIC_DIR=${MUSIC_DIR:-/media/music}
    fi
    
    # Store user's actual music location
    USER_MUSIC_DIR="$MUSIC_DIR"
    
    echo ""
    echo -e "${YELLOW}Directory Album Recenti (Opzionale)${NC}"
    echo -e "${CYAN}Inserisci il PERCORSO COMPLETO dove si trovano gli album recenti.${NC}"
    echo -e "${CYAN}Esempio: /media/music/down or /media/music/recent${NC}"
    echo -e "${CYAN}(Questo dovrebbe essere il percorso completo, non relativo alla directory musicale)${NC}"
    echo -e "${CYAN}Nota: /media/music/ripped sarà sempre incluso per i rip dei CD${NC}"
    read -p "Enter full path (or press Enter to skip): " USER_RECENT_DIR
    
    # Always include ripped directory, plus user's directory if specified
    if [ -n "$USER_RECENT_DIR" ]; then
        RECENT_DIR="$USER_RECENT_DIR,/media/music/ripped"
    else
        RECENT_DIR="/media/music/ripped"
    fi
    
    echo ""
    echo -e "${YELLOW}Default Theme${NC}"
    echo -e "${CYAN}Choose the predefinito theme for the web interface:${NC}"
    echo -e "  ${GREEN}1)${NC} Dark (predefinito)"
    echo -e "  ${GREEN}2)${NC} Chiaro"
    echo -e "  ${GREEN}3)${NC} High Contrast"
    echo -e "  ${GREEN}4)${NC} Desert"
    read -p "Select theme (1-4) [1]: " theme_choice
    theme_choice=${theme_choice:-1}
    
    case "$theme_choice" in
        1) DEFAULT_THEME="dark" ;;
        2) DEFAULT_THEME="light" ;;
        3) DEFAULT_THEME="high-contrast" ;;
        4) DEFAULT_THEME="desert" ;;
        *) DEFAULT_THEME="dark" ;;
    esac
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "Music: ${YELLOW}$MUSIC_DIR${NC}"
    [ -n "$RECENT_DIR" ] && echo -e "Recent: ${YELLOW}$RECENT_DIR${NC}" || echo -e "Recent: ${YELLOW}Not configured${NC}"
    echo -e "Tema: ${YELLOW}$DEFAULT_THEME${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Install system dependencies
install_dependencies() {
    echo -e "${GREEN}[1/8] Installazione dipendenze di sistema...${NC}"
    
    local mpd_packages=""
    [ "$MPD_INSTALL_TYPE" = "package" ] && mpd_packages="mpd mpc" && echo -e "  ${YELLOW}Including MPD${NC}" || echo -e "  ${YELLOW}Skipping MPD ($MPD_INSTALL_TYPE)${NC}"
    
    case "$OS" in
        ubuntu|debian)
            # Set noninteractive to avoid prompts
            export DEBIAN_FRONTEND=noninteractive
            sudo apt update
            sudo apt install -y \
                $mpd_packages \
                python3 python3-pip python3-venv \
                alsa-utils \
                nfs-common cifs-utils \
                curl wget git \
                build-essential \
                cdparanoia cd-discid abcde flac lame vorbis-tools eject imagemagick \
                vsftpd
            ;;
        arch|manjaro)
            sudo pacman -Syu --noconfirm \
                $mpd_packages \
                python python-pip \
                alsa-utils \
                nfs-utils cifs-utils \
                curl wget git \
                base-devel \
                vsftpd
            
            # On Arch, add user to audio group for device detection
            if ! groups $USER | grep -q audio; then
                echo -e "${YELLOW}⚠️  Adding $USER to audio group for device detection...${NC}"
                sudo usermod -a -G audio $USER
                echo -e "${GREEN}✓ Added to audio group (logout/login required for full effect)${NC}"
            fi
            ;;
        *)
            echo -e "${RED}Unsupported OS: $OS${NC}"
            exit 1
            ;;
    esac
    
    mkdir -p "$INSTALL_DIR"
    echo "MPD_INSTALL_TYPE=$MPD_INSTALL_TYPE" > "$INSTALL_DIR/.maestro_install_info"
    echo "MPD_BINARY_PATH=$MPD_BINARY_PATH" >> "$INSTALL_DIR/.maestro_install_info"
    echo "INSTALL_DATE=$(date +%Y-%m-%d)" >> "$INSTALL_DIR/.maestro_install_info"
    
    echo -e "${GREEN}✓ Dependencies installed${NC}"
}

# Configure MPD
configure_mpd() {
    echo -e "${GREEN}[2/8] Configurazione MPD...${NC}"
    
    # Standardize music location to /media/music
    if [ "$USER_MUSIC_DIR" != "/media/music" ]; then
        echo -e "${YELLOW}Setting up standard music location...${NC}"
        
        # Create the user's actual music directory
        sudo mkdir -p "$USER_MUSIC_DIR"
        
        # Create symlink: /media/music -> user's location
        if [ -e "/media/music" ] && [ ! -L "/media/music" ]; then
            echo -e "${YELLOW}⚠️  /media/music exists and is not a symlink${NC}"
            read -p "Remove/backup existing /media/music? (y/N): "
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo mv /media/music "/media/music.backup.$(date +%Y%m%d_%H%M%S)"
                echo -e "${GREEN}✓ Backed up to /media/music.backup.*${NC}"
            else
                echo -e "${RED}✗ Cannot proceed without modifying /media/music${NC}"
                exit 1
            fi
        fi
        
        # Remove existing symlink if present
        [ -L "/media/music" ] && sudo rm /media/music
        
        # Create the symlink
        sudo mkdir -p /media
        sudo ln -s "$USER_MUSIC_DIR" /media/music
        echo -e "${GREEN}✓ Creato symlink: /media/music -> $USER_MUSIC_DIR${NC}"
        
        # Set MUSIC_DIR to standard location for MPD config
        MUSIC_DIR="/media/music"
    else
        # Create music directory (but don't change ownership - may be network mount)
        sudo mkdir -p "$MUSIC_DIR"
    fi
    
    # Create CD ripping output directory
    if [ "$MUSIC_DIR" == "/media/music" ]; then
        sudo mkdir -p "$USER_MUSIC_DIR/ripped"
        sudo chown -R mpd:audio "$USER_MUSIC_DIR/ripped"
        echo -e "${GREEN}✓ Creato CD ripping directory: $USER_MUSIC_DIR/ripped${NC}"
    else
        sudo mkdir -p "$MUSIC_DIR/ripped"
        echo -e "${GREEN}✓ Creato CD ripping directory: $MUSIC_DIR/ripped${NC}"
    fi
    
    # CRITICAL: Backup MPD database BEFORE any changes
    if [ -f /var/lib/mpd/database ]; then
        echo -e "${YELLOW}⚠️  Backing up MPD database...${NC}"
        sudo cp /var/lib/mpd/database /var/lib/mpd/database.backup.$(date +%Y%m%d_%H%M%S)
        echo -e "${GREEN}✓ MPD database backed up${NC}"
    fi
    
    # Check if MPD config exists and is configured
    if [ -f /etc/mpd.conf ] && grep -q "music_directory" /etc/mpd.conf 2>/dev/null; then
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}⚠️  EXISTING MPD CONFIGURATION DETECTED${NC}"
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo "Found existing MPD configuration at: /etc/mpd.conf"
        echo ""
        echo -e "${RED}WARNING: Overwriting this will:"
        echo "  - Reset your audio device configuration"
        echo "  - Reset custom buffer settings"
        echo "  - Potentially rebuild your MPD database${NC}"
        echo ""
        echo "Recommendation: Keep existing config and use Admin Panel"
        echo "                (Audio Tweaks page) to adjust settings."
        echo ""
        read -p "Overwrite existing MPD config? (y/N): " OVERWRITE_MPD
        
        if [[ ! $OVERWRITE_MPD =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}✓ Preserving existing MPD configuration${NC}"
            echo -e "${BLUE}  Use the Admin Panel (port $ADMIN_PORT) to adjust MPD settings${NC}"
            MPD_INSTALL_TYPE="preserve_existing"
            return
        else
            echo -e "${YELLOW}⚠️  Backing up existing config...${NC}"
            sudo cp /etc/mpd.conf /etc/mpd.conf.backup.$(date +%Y%m%d_%H%M%S)
            echo -e "${GREEN}✓ Backup created: /etc/mpd.conf.backup.*${NC}"
        fi
    fi
    
    # Only create new config if we're allowed to
    echo -e "${BLUE}Creazione new MPD configuration...${NC}"
    sudo tee /etc/mpd.conf > /dev/null <<EOF
# Maestro MPD Configuration
# Directory musica
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
log_level           "predefinito"

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
    
    echo -e "${GREEN}✓ MPD configured and in esecuzione${NC}"
}

# Create installation directory
create_install_dir() {
    echo -e "${GREEN}[3/8] Creazione installation directory...${NC}"
    
    mkdir -p "$INSTALL_DIR"/{web,admin,config,logs}
    
    echo -e "${GREEN}✓ Directory structure created${NC}"
}

# Install Web UI
install_web_ui() {
    echo -e "${GREEN}[4/8] Installazione Web UI...${NC}"
    
    # Copy web UI files
    if [ -f "$HOME/Maestro-Server/app.py" ]; then
        cp -r "$HOME/Maestro-Server"/{app.py,templates,static,requirements.txt} "$INSTALL_DIR/web/" 2>/dev/null || true
        cp -r "$HOME/Maestro-Server"/data "$INSTALL_DIR/web/" 2>/dev/null || true
        # Copy LMS client library if it exists
        [ -f "$HOME/Maestro-Server/lms_client.py" ] && cp "$HOME/Maestro-Server/lms_client.py" "$INSTALL_DIR/web/"
        # Copy Bandcamp client library if it exists
        [ -f "$HOME/Maestro-Server/bandcamp_client.py" ] && cp "$HOME/Maestro-Server/bandcamp_client.py" "$INSTALL_DIR/web/"
    elif [ -f "app.py" ]; then
        # In Esecuzione from Maestro-Server directory
        cp -r {app.py,templates,static,requirements.txt} "$INSTALL_DIR/web/" 2>/dev/null || true
        cp -r data "$INSTALL_DIR/web/" 2>/dev/null || true
        # Copy LMS client library if it exists
        [ -f "lms_client.py" ] && cp lms_client.py "$INSTALL_DIR/web/"
        # Copy Bandcamp client library if it exists
        [ -f "bandcamp_client.py" ] && cp bandcamp_client.py "$INSTALL_DIR/web/"
    elif [ -f "$HOME/Maestro-MPD-Control/app.py" ]; then
        cp -r "$HOME/Maestro-MPD-Control"/{app.py,templates,static,requirements.txt} "$INSTALL_DIR/web/" 2>/dev/null || true
        # Copy LMS client library if it exists
        [ -f "$HOME/Maestro-MPD-Control/lms_client.py" ] && cp "$HOME/Maestro-MPD-Control/lms_client.py" "$INSTALL_DIR/web/"
        # Copy Bandcamp client library if it exists
        [ -f "$HOME/Maestro-MPD-Control/bandcamp_client.py" ] && cp "$HOME/Maestro-MPD-Control/bandcamp_client.py" "$INSTALL_DIR/web/"
    else
        echo -e "${YELLOW}Avviso: Web UI source not found in ~/Maestro-Server, current directory, or ~/Maestro-MPD-Control${NC}"
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

# Create initial settings
create_settings() {
    echo -e "${GREEN}[4.5/8] Creazione initial settings...${NC}"
    
    local settings_file="$INSTALL_DIR/settings.json"
    
    # Build settings JSON
    cat > "$settings_file" <<EOF
{
    "theme": "$DEFAULT_THEME",
    "enable_scrobbling": false,
    "show_scrobble_toasts": true,
    "lastfm_api_key": "",
    "lastfm_shared_secret": "",
    "lastfm_session_key": "",
    "bandcamp_enabled": false,
    "bandcamp_username": "",
    "bandcamp_identity_token": ""
EOF
    
    # Add recent_albums_dir if configured
    if [ -n "$RECENT_DIR" ]; then
        cat >> "$settings_file" <<EOF
,
    "recent_albums_dir": "$RECENT_DIR"
EOF
    fi
    
    # Close JSON
    cat >> "$settings_file" <<EOF

}
EOF
    
    # Copy to web directory as well (web is source of truth)
    cp "$settings_file" "$INSTALL_DIR/web/settings.json"
    
    echo -e "${GREEN}✓ Initial settings created (root and web)${NC}"
}

# Install Admin API
install_admin_api() {
    echo -e "${GREEN}[5/8] Installazione Admin API...${NC}"
    
    # Check if admin API exists
    if [ -d "$HOME/Maestro-Server/admin" ]; then
        cp -r "$HOME/Maestro-Server/admin"/* "$INSTALL_DIR/admin/"
    elif [ -d "admin" ]; then
        # In Esecuzione from Maestro-Server directory
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
        
        echo -e "${YELLOW}Avviso: Admin API source not found. Creazione placeholder...${NC}"
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
    echo -e "${GREEN}[6/8] Configurazione permessi sudo...${NC}"
    
    # Add user to audio group for device access
    if ! groups $USER | grep -q audio; then
        sudo usermod -aG audio $USER
        echo -e "  ${YELLOW}Added $USER to audio group${NC}"
    fi
    
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
    
    echo -e "${GREEN}✓ Permessi sudo configurati${NC}"
}

# Configure FTP access
configure_ftp() {
    echo -e "${GREEN}[7/9] Configurazione FTP access...${NC}"
    
    # Backup original vsftpd.conf if it exists
    if [ -f /etc/vsftpd.conf ]; then
        sudo cp /etc/vsftpd.conf /etc/vsftpd.conf.backup
        echo -e "  ${YELLOW}Backed up original vsftpd.conf${NC}"
    fi
    
    # Create vsftpd configuration
    sudo tee /etc/vsftpd.conf > /dev/null <<EOF
# Maestro FTP Configuration
# Allow local users to log in
local_enable=YES

# Enable write permissions
write_enable=YES

# Set local umask to 022 (files: 644, dirs: 755)
local_umask=022

# Disable anonymous access
anonymous_enable=NO

# Restrict users to their home directory and /media/music
chroot_local_user=NO

# Allow users to access /media/music
# Users can navigate to /media/music to manage ripped CDs
user_sub_token=\$USER
local_root=/home/\$USER

# Enable passive mode for better firewall compatibility
pasv_enable=YES
pasv_min_port=40000
pasv_max_port=40100

# Logging
xferlog_enable=YES
xferlog_file=/var/log/vsftpd.log

# Security settings
ssl_enable=NO
allow_writeable_chroot=YES

# Performance
use_localtime=YES
EOF
    
    # Ensure music directory exists and has proper permissions
    sudo mkdir -p /media/music/ripped
    sudo chown -R $USER:$USER /media/music
    sudo chmod -R 755 /media/music
    
    # Enable and start vsftpd
    sudo systemctl enable vsftpd
    sudo systemctl restart vsftpd
    
    if systemctl is-active --quiet vsftpd; then
        echo -e "${GREEN}✓ FTP server configured and in esecuzione${NC}"
        echo -e "  ${YELLOW}Users can FTP to organize music in /media/music/${NC}"
    else
        echo -e "${YELLOW}⚠ FTP server failed to start. Check logs: journalctl -u vsftpd${NC}"
    fi
}

# Configure CD auto-rip
configure_cd_autorip() {
    echo -e "${GREEN}Configurazione CD auto-rip...${NC}"
    
    # Create scripts directory
    mkdir -p "$INSTALL_DIR/scripts"
    mkdir -p "$INSTALL_DIR/logs"
    
    # Copy CD insert handler script
    if [ -f "$REPO_DIR/scripts/cd-inserted.sh" ]; then
        cp "$REPO_DIR/scripts/cd-inserted.sh" "$INSTALL_DIR/scripts/"
        chmod +x "$INSTALL_DIR/scripts/cd-inserted.sh"
        echo -e "  ${GREEN}✓ Installato CD insert handler${NC}"
    fi
    
    # Install udev rule
    if [ -f "$REPO_DIR/udev/99-maestro-cd.rules" ]; then
        # Replace %u with actual username in udev rule
        sed "s/%u/$USER/g" "$REPO_DIR/udev/99-maestro-cd.rules" | sudo tee /etc/udev/rules.d/99-maestro-cd.rules > /dev/null
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        echo -e "  ${GREEN}✓ Installato udev rule for CD detection${NC}"
    fi
    
    echo -e "${GREEN}✓ CD auto-rip configured (disabled by predefinito, enable in CD Settings)${NC}"
}

# Create systemd services
create_systemd_services() {
    echo -e "${GREEN}[8/9] Creazione servizi systemd...${NC}"
    
    # Configure MPD to wait for NFS mounts (fixes database loss issue)
    echo -e "${YELLOW}Configurazione MPD to wait for NFS mounts...${NC}"
    sudo mkdir -p /etc/systemd/system/mpd.service.d
    sudo tee /etc/systemd/system/mpd.service.d/nfs-wait.conf > /dev/null <<'MPDEOF'
[Unit]
# Wait for NFS mounts before starting MPD
After=network-online.target remote-fs.target
Wants=network-online.target
Requires=remote-fs.target

[Service]
# Restart MPD if it crashes due to NFS issues
Restart=on-failure
RestartSec=10
MPDEOF
    echo -e "${GREEN}✓ Configured MPD to wait for remote filesystems${NC}"
    
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
    echo -e "${GREEN}[9/9] Avvio Maestro services...${NC}"
    
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
    echo -e "${GREEN}║           🎉 INSTALLAZIONE MAESTRO COMPLETATA! 🎉            ║${NC}"
    echo -e "${GREEN}║                                                            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📍 Directory Installazione:${NC} $INSTALL_DIR"
    echo -e "${BLUE}🎵 Directory Musica:${NC} $MUSIC_DIR"
    if [ "$USER_MUSIC_DIR" != "/media/music" ] && [ -L "/media/music" ]; then
        echo -e "${BLUE}   (Link simbolico a: ${YELLOW}$USER_MUSIC_DIR${BLUE})${NC}"
    fi
    echo ""
    echo -e "${BLUE}🌐 URL di Accesso:${NC}"
    echo -e "   Interfaccia Web:    ${GREEN}http://$IP:$WEB_PORT${NC}"
    echo -e "   Admin API: ${GREEN}http://$IP:$ADMIN_PORT${NC}"
    echo -e "   MPD:       ${GREEN}$IP:$MPD_PORT${NC}"
    echo -e "   FTP:       ${GREEN}ftp://$IP${NC} (username: ${YELLOW}$USER${NC})"
    echo ""
    echo -e "${BLUE}📋 Gestione Servizi:${NC}"
    echo -e "   Interfaccia Web:    ${YELLOW}sudo systemctl {start|stop|restart|status} maestro-web${NC}"
    echo -e "   Admin API: ${YELLOW}sudo systemctl {start|stop|restart|status} maestro-admin${NC}"
    echo -e "   MPD:       ${YELLOW}sudo systemctl {start|stop|restart|status} mpd${NC}"
    echo -e "   FTP:       ${YELLOW}sudo systemctl {start|stop|restart|status} vsftpd${NC}"
    echo ""
    echo -e "${BLUE}📁 Aggiungi Musica:${NC}"
    echo -e "   1. Copia musica in: ${GREEN}/media/music${NC}"
    echo -e "      (Le sottodirectory dentro /media/music appariranno in Album Recenti)"
    echo -e "   2. Oppure monta condivisioni di rete dentro ${GREEN}/media/music/${NC}"
    echo -e "   3. Usa FTP per organizzare i CD rippati: ${GREEN}ftp://$IP/media/music/ripped${NC}"
    echo -e "   4. Aggiorna libreria MPD: ${YELLOW}mpc update${NC}"
    echo ""
    echo -e "${BLUE}🔧 Log:${NC}"
    echo -e "   Interfaccia Web:    ${YELLOW}journalctl -u maestro-web -f${NC}"
    echo -e "   Admin API: ${YELLOW}journalctl -u maestro-admin -f${NC}"
    echo -e "   MPD:       ${YELLOW}journalctl -u mpd -f${NC}"
    echo ""
    echo -e "${GREEN}✨ Prossimi Passi:${NC}"
    echo -e "   1. Apri ${GREEN}http://$IP:$ADMIN_PORT${NC} per configurare il sistema"
    echo -e "   2. Aggiungi condivisioni di rete in Gestione Libreria"
    echo -e "   3. Configura impostazioni audio in Regolazioni Audio"
    echo -e "   4. Apri ${GREEN}http://$IP:$WEB_PORT${NC} per riprodurre musica!"
    echo ""
}

# Main installation flow
main() {
    print_banner
    check_root
    detect_os
    
    echo -e "${BLUE}Sistema Operativo rilevato:${NC} $OS $VERSION"
    echo -e "${BLUE}Directory Installazione:${NC} $INSTALL_DIR"
    echo ""
    
    detect_mpd
    prompt_directories
    
    read -p "Press Enter to begin installation or Ctrl+C to cancel..."
    echo ""
    
    install_dependencies
    configure_mpd
    create_install_dir
    install_web_ui
    create_settings
    install_admin_api
    configure_sudo
    configure_ftp
    configure_cd_autorip
    create_systemd_services
    start_services
    
    print_success
}

# Run main installation
main
