#!/bin/bash
# Quick test of the integrated system

echo "🎵 Maestro MPD Control - Quick Test"
echo "===================================="
echo ""

# Check if files exist
echo "📁 Checking files..."
[ -f ~/Maestro-MPD-Control/install-maestro.sh ] && echo "✓ Installer present" || echo "✗ Installer missing"
[ -f ~/Maestro-MPD-Control/admin/admin_api.py ] && echo "✓ Admin API present" || echo "✗ Admin API missing"
[ -f ~/Maestro-MPD-Control/app.py ] && echo "✓ Web UI present" || echo "✗ Web UI missing"
echo ""

# Check current services
echo "🔍 Checking running services..."
if pgrep -f "admin_api.py" > /dev/null; then
    PID=$(pgrep -f "admin_api.py")
    echo "✓ Admin API running (PID: $PID)"
else
    echo "✗ Admin API not running"
fi

if systemctl is-active --quiet mpd 2>/dev/null; then
    echo "✓ MPD running"
else
    echo "✗ MPD not running"
fi
echo ""

# Check ports
echo "🌐 Checking ports..."
if nc -z localhost 5004 2>/dev/null; then
    echo "✓ Port 5004 (Admin API) open"
else
    echo "✗ Port 5004 not accessible"
fi

if nc -z localhost 6600 2>/dev/null; then
    echo "✓ Port 6600 (MPD) open"
else
    echo "✗ Port 6600 not accessible"
fi
echo ""

# Get IP
IP=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}')
echo "📡 Access URLs:"
echo "   Admin API: http://$IP:5004"
echo "   Web UI:    http://$IP:5003"
echo ""

# Check music library
if [ -d /media/music ]; then
    COUNT=$(find /media/music -type d -maxdepth 1 2>/dev/null | wc -l)
    echo "🎵 Music library: $((COUNT-1)) folders in /media/music"
fi
echo ""

echo "📋 Next steps:"
echo "   1. Review integration: cat ~/Maestro-MPD-Control/INTEGRATION_SUMMARY.md"
echo "   2. Test installer: cd ~/Maestro-MPD-Control && ./install-maestro.sh"
echo "   3. Commit to git: git add . && git commit -m 'Add admin API v2.0'"
echo ""
