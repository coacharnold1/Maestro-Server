#!/bin/bash

# MPD Web Control - Setup Script
# This script helps set up the MPD Web Control application

set -e  # Exit on any error

echo "=== MPD Web Control Setup ==="
echo

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root. Please run as a regular user."
   exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.7"

if python3 -c "import sys; exit(0 if sys.version_info >= (3,7) else 1)"; then
    echo "✅ Python $PYTHON_VERSION detected (>= $REQUIRED_VERSION required)"
else
    echo "❌ Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "📁 Working directory: $SCRIPT_DIR"
echo

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔨 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Dependencies installed successfully"
echo

# Check if config.env exists
if [ ! -f "config.env" ]; then
    echo "⚙️ Creating configuration file..."
    cp config.env.example config.env
    echo "✅ Configuration file created: config.env"
    echo "📝 Please edit config.env with your settings before running the application"
else
    echo "✅ Configuration file already exists: config.env"
fi

echo

# Check MPD connection
echo "🎵 Checking MPD connection..."
MPD_HOST=$(grep "^MPD_HOST=" config.env | cut -d'=' -f2 | tr -d '"' || echo "localhost")
MPD_PORT=$(grep "^MPD_PORT=" config.env | cut -d'=' -f2 | tr -d '"' || echo "6600")

if command -v nc >/dev/null 2>&1; then
    if nc -z "$MPD_HOST" "$MPD_PORT" 2>/dev/null; then
        echo "✅ MPD is accessible at $MPD_HOST:$MPD_PORT"
    else
        echo "⚠️ Cannot connect to MPD at $MPD_HOST:$MPD_PORT"
        echo "   Please ensure MPD is running and accessible"
    fi
else
    echo "ℹ️ netcat not available, skipping MPD connection test"
fi

echo

# Display next steps
echo "🎉 Setup completed successfully!"
echo
echo "Next steps:"
echo "1. Edit config.env with your specific settings:"
echo "   - Update MPD_HOST and MPD_PORT if needed"
echo "   - Set MUSIC_DIRECTORY to your music folder"
echo "   - Add Last.fm API credentials (optional)"
echo
echo "2. Run the application:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo
echo "3. Open your browser to: http://localhost:5000"
echo

# Check if systemd is available for service installation
if command -v systemctl >/dev/null 2>&1; then
    echo "💡 To install as a system service, run:"
    echo "   sudo ./install_service.sh"
    echo
fi

echo "📚 For more information, see README.md"