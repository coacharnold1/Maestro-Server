#!/bin/bash
#==============================================================================
# Maestro CD Auto-Rip Handler
# Called by udev when a CD is inserted
#==============================================================================

SETTINGS_FILE="$HOME/maestro/web/settings.json"
LOG_FILE="$HOME/maestro/logs/cd-autorip.log"
LOCK_FILE="/tmp/maestro-cd-autorip.lock"
ADMIN_API="http://localhost:5004"

# Create log directory if needed
mkdir -p "$(dirname "$LOG_FILE")"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "CD insertion detected"

# Check for lock file to prevent multiple simultaneous runs
if [ -f "$LOCK_FILE" ]; then
    LOCK_AGE=$(($(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0)))
    if [ $LOCK_AGE -lt 300 ]; then
        log "Lock file exists (age: ${LOCK_AGE}s), another instance is running. Exiting."
        exit 0
    else
        log "Stale lock file detected (age: ${LOCK_AGE}s), removing and continuing"
        rm -f "$LOCK_FILE"
    fi
fi

# Create lock file
touch "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

# Wait a moment for CD to settle
sleep 3

# Check if settings file exists
if [ ! -f "$SETTINGS_FILE" ]; then
    log "Settings file not found: $SETTINGS_FILE"
    exit 0
fi

# Check if auto-rip is enabled (using Python to parse JSON)
AUTO_RIP=$(python3 -c "
import json
import sys
try:
    with open('$SETTINGS_FILE', 'r') as f:
        settings = json.load(f)
    enabled = settings.get('cd_ripper', {}).get('auto_rip', {}).get('enabled', False)
    print('true' if enabled else 'false')
except Exception as e:
    print('false', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)

if [ "$AUTO_RIP" != "true" ]; then
    log "Auto-rip disabled, skipping"
    exit 0
fi

log "Auto-rip enabled, checking for disc..."

# Verify disc is present and get metadata
DISC_CHECK=$(curl -s "$ADMIN_API/api/cd/detect")
HAS_DISC=$(echo "$DISC_CHECK" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('true' if data.get('has_disc', False) else 'false')
except:
    print('false')
")

if [ "$HAS_DISC" != "true" ]; then
    log "No disc detected, skipping"
    exit 0
fi

log "Disc detected, fetching metadata..."

# Get metadata
METADATA=$(curl -s "$ADMIN_API/api/cd/metadata")
log "Metadata: $METADATA"

# Start ripping with default settings from settings.json
log "Starting auto-rip..."

RIP_RESPONSE=$(curl -s -X POST "$ADMIN_API/api/cd/rip" \
    -H "Content-Type: application/json" \
    -d '{
        "auto_rip": true,
        "album_art_embedded": true,
        "album_art_file": true
    }')

log "Rip response: $RIP_RESPONSE"

# Check if rip started successfully
SUCCESS=$(echo "$RIP_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('true' if data.get('status') == 'success' else 'false')
except:
    print('false')
")

if [ "$SUCCESS" = "true" ]; then
    log "Auto-rip started successfully"
else
    log "Auto-rip failed to start"
fi
