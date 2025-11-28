#!/usr/bin/env bash
###############################################################################
# MPD Web Control - Release Cleanup Script
# 
# Removes all personal data and development artifacts to prepare for
# Docker/GitHub public release.
#
# Usage:
#   ./cleanup_for_release.sh [target_directory]
#
# If no target_directory is provided, creates a new clean directory:
#   mpd_web_control_release_YYYYMMDD_HHMMSS/
#
# This script:
# - Removes personal config files (config.env, settings.json, radio_stations.json)
# - Removes development artifacts (__pycache__, venv, backups)
# - Creates sanitized example files
# - Preserves all source code and templates
# - Leaves you with a clean, release-ready directory
###############################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# Determine target directory
if [ $# -eq 1 ]; then
    TARGET_DIR="$1"
    echo "[INFO] Using provided target directory: ${TARGET_DIR}"
else
    TARGET_DIR="${SCRIPT_DIR}/../mpd_web_control_release_${TIMESTAMP}"
    echo "[INFO] Creating new release directory: ${TARGET_DIR}"
fi

# Create target if it doesn't exist
mkdir -p "${TARGET_DIR}"

echo "=========================================="
echo "MPD Web Control - Release Cleanup"
echo "=========================================="
echo ""
echo "Source: ${SCRIPT_DIR}"
echo "Target: ${TARGET_DIR}"
echo ""

# Copy all files except excluded directories
echo "[STEP 1/5] Copying source files..."

# Use cp with find instead of rsync (more portable)
(
    cd "${SCRIPT_DIR}"
    find . -type f \
        ! -path './venv/*' \
        ! -path './__pycache__/*' \
        ! -path './backups/*' \
        ! -path './.pytest_cache/*' \
        ! -path './.git/*' \
        ! -path './mpd_web_control_release_*/*' \
        ! -name '*.pyc' \
        ! -name '*.pyo' \
        ! -name '*.pyd' \
        ! -name '.coverage' \
        -exec sh -c 'mkdir -p "'"${TARGET_DIR}"'/$(dirname {})" && cp -v "{}" "'"${TARGET_DIR}"'/{}"' \;
)

echo "[SUCCESS] Source files copied"
echo ""

# Navigate to target directory for cleanup
cd "${TARGET_DIR}"

echo "[STEP 2/5] Removing personal data files..."

# Remove personal configuration
if [ -f "config.env" ]; then
    echo "  - Removing config.env (contains personal Last.fm keys)"
    rm -f config.env
fi

# Remove personal settings
if [ -f "settings.json" ]; then
    echo "  - Removing settings.json (contains Last.fm session key)"
    rm -f settings.json
fi

# Remove personal radio stations
if [ -f "radio_stations.json" ]; then
    echo "  - Removing radio_stations.json (personal station presets)"
    rm -f radio_stations.json
fi

echo "[SUCCESS] Personal data removed"
echo ""

echo "[STEP 3/5] Removing system-specific features..."

# Remove Maestro Config button from index.html (system-specific feature)
if [ -f "templates/index.html" ]; then
    echo "  - Removing Maestro Config section from index.html"
    # Remove the entire Maestro Config conditional block
    sed -i '/^[[:space:]]*{# Maestro Config Link/,/^[[:space:]]*{% endif %}/d' templates/index.html
fi

echo "[SUCCESS] System-specific features removed"
echo ""

echo "[STEP 4/5] Creating clean example files..."

# Ensure config.env.example exists and is clean
cat > config.env.example << 'EOF'
# MPD Web Control - Configuration
# Copy this file to config.env and customize for your setup

# MPD Connection Settings
MPD_HOST=localhost
MPD_PORT=6600
MPD_TIMEOUT=30

# Music Library
MUSIC_DIRECTORY=/path/to/your/music

# Web Interface
APP_PORT=5003
APP_HOST=0.0.0.0

# Last.fm Integration (Optional)
# Get your API key and shared secret from https://www.last.fm/api
LASTFM_API_KEY=your-api-key-here
LASTFM_SHARED_SECRET=your-shared-secret-here

# Debug Mode (set to False in production)
DEBUG=False

# Flask Secret Key (change this in production)
SECRET_KEY=your-secret-key-change-this-in-production

# Note: MAESTRO_CONFIG_URL removed - system-specific feature not included in release
EOF

echo "  - Created clean config.env.example (Maestro Config URL removed)"

# Create empty settings.json template
cat > settings.json.example << 'EOF'
{
  "theme": "dark",
  "lastfm_api_key": "",
  "lastfm_shared_secret": "",
  "lastfm_session_key": "",
  "scrobbling_enabled": false,
  "show_scrobble_toasts": true
}
EOF

echo "  - Created settings.json.example"

# Create empty radio stations template
cat > radio_stations.json.example << 'EOF'
{
  "stations": []
}
EOF

echo "  - Created radio_stations.json.example"

echo "[SUCCESS] Example files created"
echo ""

echo "[STEP 5/5] Cleaning development artifacts..."

# Remove any remaining __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "  - Removed __pycache__ directories"

# Remove Python bytecode
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true
echo "  - Removed Python bytecode files"

# Remove any .DS_Store (macOS)
find . -type f -name ".DS_Store" -delete 2>/dev/null || true
echo "  - Removed .DS_Store files"

# Remove test artifacts
rm -rf .pytest_cache .coverage 2>/dev/null || true
echo "  - Removed test artifacts"

echo "[SUCCESS] Development artifacts cleaned"
echo ""

echo "[STEP 6/6] Verifying release directory..."

# Check for any remaining personal data patterns
echo "  - Checking for potential personal data..."
FOUND_ISSUES=0

# Check for hardcoded API keys (not in example files)
if grep -r "a598549825d12e1fe784b6641f963a11" --exclude="*.example" --exclude="cleanup_for_release.sh" . 2>/dev/null; then
    echo "    ⚠️  WARNING: Found hardcoded Last.fm API key in non-example files"
    FOUND_ISSUES=1
fi

# Check for hardcoded secrets (not in example files)
if grep -r "5d14ecb180c0bb4ba3018fe4f4734424" --exclude="*.example" --exclude="cleanup_for_release.sh" . 2>/dev/null; then
    echo "    ⚠️  WARNING: Found hardcoded Last.fm secret in non-example files"
    FOUND_ISSUES=1
fi

# Check for personal music paths
if grep -r "/home/fausto" --exclude="*.example" --exclude="cleanup_for_release.sh" --exclude="DOCKER_RELEASE_PLAN.md" --exclude="CHANGELOG.md" . 2>/dev/null; then
    echo "    ⚠️  WARNING: Found personal home directory paths"
    FOUND_ISSUES=1
fi

# Check for Maestro Config URL
if grep -r "192.168.1.142:5000" --exclude="*.example" --exclude="cleanup_for_release.sh" . 2>/dev/null; then
    echo "    ⚠️  WARNING: Found Maestro Config URL (system-specific)"
    FOUND_ISSUES=1
fi

# Check for Maestro Config references in templates
if grep -r "maestro_config_url" --exclude="*.example" --exclude="cleanup_for_release.sh" --exclude="DOCKER_DEPLOYMENT_PLAN.md" templates/ 2>/dev/null; then
    echo "    ⚠️  WARNING: Found Maestro Config references in templates"
    FOUND_ISSUES=1
fi

if [ $FOUND_ISSUES -eq 0 ]; then
    echo "    ✅ No personal data patterns detected"
fi

echo ""
echo "=========================================="
echo "Release Cleanup Complete!"
echo "=========================================="
echo ""
echo "Clean release directory: ${TARGET_DIR}"
echo ""
echo "📋 What was removed:"
echo "  • config.env (personal Last.fm keys)"
echo "  • settings.json (Last.fm session key)"
echo "  • radio_stations.json (personal presets)"
echo "  • Maestro Config button from index.html (system-specific)"
echo "  • __pycache__/ directories"
echo "  • venv/ directory"
echo "  • backups/ directory"
echo "  • Python bytecode files"
echo ""
echo "📝 What was created:"
echo "  • config.env.example (clean template)"
echo "  • settings.json.example (default structure)"
echo "  • radio_stations.json.example (empty template)"
echo ""
echo "✅ Next steps:"
echo "  1. Review the release directory for any remaining personal data"
echo "  2. Test the application with clean config"
echo "  3. Create Docker image or GitHub release"
echo ""

if [ $FOUND_ISSUES -eq 1 ]; then
    echo "⚠️  MANUAL REVIEW NEEDED: Potential personal data found (see warnings above)"
    echo ""
    exit 1
fi

echo "🎉 Release directory is ready for distribution!"
