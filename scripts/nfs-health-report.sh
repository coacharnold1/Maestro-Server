#!/bin/bash
#
# NFS Health Report - Display current status
# Shows mount status, recent errors, and statistics
#

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

LOG_FILE="/var/log/maestro-nfs-health.log"
[ ! -f "$LOG_FILE" ] && LOG_FILE="$HOME/maestro-nfs-health.log"

CONFIG_FILE="/etc/maestro/nfs-config.conf"

# Get NFS server IP from config file or extract from fstab
get_nfs_server() {
    # First try config file if it exists
    if [ -f "$CONFIG_FILE" ] && grep -q "NFS_SERVER=" "$CONFIG_FILE"; then
        source "$CONFIG_FILE"
        echo "$NFS_SERVER"
        return
    fi
    
    # Fall back to extracting first NFS mount from fstab
    local nfs_ip=$(grep -o '^[^/]*:[^ ]*' /etc/fstab | grep -oP '^\d+\.\d+\.\d+\.\d+' | head -1)
    if [ -n "$nfs_ip" ]; then
        echo "$nfs_ip"
        return
    fi
    
    # Last resort fallback
    echo "192.168.1.130"
}

NFS_SERVER=$(get_nfs_server)

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    NFS Mount Health Report - $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"

# Check NFS server connectivity
echo -e "${YELLOW}▸ NFS Server Status:${NC}"
if ping -c 1 -W 2 "$NFS_SERVER" >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Server $NFS_SERVER is reachable"
else
    echo -e "  ${RED}✗${NC} Server $NFS_SERVER is NOT reachable!"
fi
echo
echo -e "${YELLOW}▸ Mount Point Status:${NC}"
mount_points=(
    "/media/music/mrbig"
    "/media/music/borris"
    "/media/music/natasha"
    "/media/music/gidney"
    "/media/music/cloyd"
    "/media/music/bullwinkle"
    "/media/music/rocky"
    "/media/music/down"
)

for mount_point in "${mount_points[@]}"; do
    mount_name=$(basename "$mount_point")
    printf "  %-15s " "$mount_name:"
    
    if mountpoint -q "$mount_point" 2>/dev/null; then
        if timeout 3 ls "$mount_point" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Mounted & Accessible${NC}"
        else
            echo -e "${RED}✗ Mounted but STALE/TIMEOUT${NC}"
        fi
    else
        echo -e "${RED}✗ NOT Mounted${NC}"
    fi
done
echo

# Show NFS mount options for one mount as example
echo -e "${YELLOW}▸ Current Mount Options (bullwinkle example):${NC}"
mount | grep bullwinkle | sed 's/^/  /'
echo

# Show recent errors from log
if [ -f "$LOG_FILE" ]; then
    echo -e "${YELLOW}▸ Recent Log Entries (last 10):${NC}"
    sudo tail -n 10 "$LOG_FILE" 2>/dev/null | sed 's/^/  /' || tail -n 10 "$LOG_FILE" | sed 's/^/  /'
    echo
    
    # Count errors in last 24 hours
    error_count=$(grep "ERROR" "$LOG_FILE" 2>/dev/null | grep "$(date '+%Y-%m-%d')" | wc -l)
    if [ "$error_count" -gt 0 ]; then
        echo -e "${YELLOW}▸ Errors Today:${NC} ${RED}$error_count${NC}"
    else
        echo -e "${YELLOW}▸ Errors Today:${NC} ${GREEN}0${NC}"
    fi
else
    echo -e "${YELLOW}▸ Log File:${NC} Not found (monitoring not yet run)"
fi
echo

# Show NFS client statistics
echo -e "${YELLOW}▸ NFS Client Statistics:${NC}"
if command -v nfsstat >/dev/null 2>&1; then
    nfsstat -c 2>/dev/null | grep -A 5 "Client rpc" | sed 's/^/  /'
else
    echo "  nfsstat command not available"
fi

echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
