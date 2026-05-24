#!/bin/bash

#==============================================================================
# Maestro Update Bootstrap Script
# Minimal wrapper that pulls latest, then runs the actual update script
# This ensures script changes are picked up immediately without double-run
#==============================================================================

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPDATE_SCRIPT="$REPO_DIR/update-maestro.sh"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         MAESTRO - UPDATE BOOTSTRAP                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Pull latest from git first
echo -e "${GREEN}[1/2] Pulling latest changes from git...${NC}"
cd "$REPO_DIR"

# Stash any local changes
if ! git diff-index --quiet HEAD --; then
    echo "Stashing local changes..."
    git stash
fi

# Explicit fetch first to ensure remote refs are up to date
echo "Fetching remote changes..."
if ! git fetch origin main; then
    echo -e "${RED}Failed to fetch from git${NC}"
    exit 1
fi

# Now check what changed
echo "Checking for new commits..."
BEHIND=$(git rev-list --count HEAD..origin/main)
if [ "$BEHIND" -gt 0 ]; then
    echo "Found $BEHIND new commits. Pulling..."
    if ! git pull --ff-only origin main; then
        echo -e "${RED}Failed to merge changes. Try manual git pull.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Latest changes pulled ($BEHIND commits)${NC}"
else
    echo -e "${GREEN}✓ Already up to date${NC}"
fi
echo ""

# Step 2: Run the actual update script (now with latest changes)
echo -e "${GREEN}[2/2] Running update script...${NC}"
if [ ! -f "$UPDATE_SCRIPT" ]; then
    echo -e "${RED}Error: $UPDATE_SCRIPT not found${NC}"
    exit 1
fi

# Execute the update script with all remaining arguments
exec "$UPDATE_SCRIPT" "$@"
