#!/bin/bash

# MPD Web Control - Service Installation Script
# This script installs the application as a systemd service

set -e

echo "=== MPD Web Control Service Installation ==="
echo

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Get the user who owns the script directory
APP_USER=$(stat -c '%U' "$SCRIPT_DIR")
APP_GROUP=$(stat -c '%G' "$SCRIPT_DIR")

echo "📁 Application directory: $SCRIPT_DIR"
echo "👤 Running as user: $APP_USER"
echo

# Verify the application files exist
if [ ! -f "$SCRIPT_DIR/app.py" ]; then
    echo "❌ app.py not found in $SCRIPT_DIR"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/venv/bin/python" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Create startup script for proper venv activation
STARTUP_SCRIPT="$SCRIPT_DIR/start_app.sh"

echo "📝 Creating startup script: $STARTUP_SCRIPT"

cat > "$STARTUP_SCRIPT" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
exec python app.py
EOF

chmod +x "$STARTUP_SCRIPT"
echo "✅ Startup script created"

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/mpd-web-control.service"

echo "📝 Creating systemd service file: $SERVICE_FILE"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=MPD Web Control Panel - Combined Edition
After=network.target mpd.service
Wants=mpd.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/start_app.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file created"

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Enable the service
echo "🔧 Enabling service..."
systemctl enable mpd-web-control.service

# Check if the service should be started now
read -p "🚀 Start the service now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "▶️ Starting service..."
    systemctl start mpd-web-control.service
    
    # Give it a moment to start
    sleep 2
    
    # Check status
    if systemctl is-active --quiet mpd-web-control.service; then
        echo "✅ Service started successfully!"
        
        # Get the port from config
        if [ -f "$SCRIPT_DIR/config.env" ]; then
            APP_PORT=$(grep "^APP_PORT=" "$SCRIPT_DIR/config.env" | cut -d'=' -f2 | tr -d '"' || echo "5000")
        else
            APP_PORT="5000"
        fi
        
        echo "🌐 Web interface should be available at: http://localhost:$APP_PORT"
    else
        echo "❌ Service failed to start. Check logs with:"
        echo "   journalctl -u mpd-web-control.service -f"
    fi
else
    echo "ℹ️ Service enabled but not started. Start it manually with:"
    echo "   sudo systemctl start mpd-web-control.service"
fi

echo
echo "📋 Useful commands:"
echo "   sudo systemctl status mpd-web-control    # Check service status"
echo "   sudo systemctl stop mpd-web-control      # Stop service"
echo "   sudo systemctl restart mpd-web-control   # Restart service"
echo "   journalctl -u mpd-web-control -f         # View logs"
echo "   sudo systemctl disable mpd-web-control   # Disable auto-start"

echo
echo "🎉 Service installation completed!"