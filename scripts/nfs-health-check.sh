#!/bin/bash
#
# NFS Mount Health Check Script
# Monitors all NFS mounts and logs issues
# Created: 2026-01-25
#

LOG_FILE="/var/log/maestro-nfs-health.log"
ALERT_FILE="/tmp/nfs-alert-needed"
NFS_SERVER="192.168.1.110"

# Ensure log file exists and is writable
sudo touch "$LOG_FILE" 2>/dev/null || LOG_FILE="$HOME/maestro-nfs-health.log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | sudo tee -a "$LOG_FILE" >/dev/null
}

# Check if NFS server is reachable
check_server() {
    if ! ping -c 1 -W 2 "$NFS_SERVER" >/dev/null 2>&1; then
        log_message "ERROR: NFS server $NFS_SERVER is not reachable!"
        return 1
    fi
    return 0
}

# Check each NFS mount point
check_mounts() {
    local all_ok=true
    local mount_points=(
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
        # Check if mounted
        if ! mountpoint -q "$mount_point" 2>/dev/null; then
            log_message "ERROR: $mount_point is NOT mounted!"
            all_ok=false
            continue
        fi
        
        # Test actual access with timeout
        if ! timeout 5 ls "$mount_point" >/dev/null 2>&1; then
            log_message "ERROR: $mount_point is mounted but NOT accessible (timeout/stale)!"
            all_ok=false
            continue
        fi
        
        # Check for stale NFS handle
        if dmesg | tail -n 50 | grep -i "stale.*$mount_point" >/dev/null 2>&1; then
            log_message "WARNING: Stale NFS handle detected for $mount_point"
            all_ok=false
        fi
    done
    
    if [ "$all_ok" = true ]; then
        log_message "INFO: All NFS mounts are healthy"
        # Remove alert flag if exists
        rm -f "$ALERT_FILE"
        return 0
    else
        # Create alert flag
        touch "$ALERT_FILE"
        return 1
    fi
}

# Check NFS statistics for errors
check_nfs_stats() {
    local errors=$(nfsstat -c 2>/dev/null | grep -E "retrans|timeout" | head -n 2)
    if [ -n "$errors" ]; then
        log_message "NFS Stats: $errors"
    fi
}

# Main execution
main() {
    log_message "=== Starting NFS Health Check ==="
    
    if ! check_server; then
        log_message "=== Health Check FAILED - Server Unreachable ==="
        touch "$ALERT_FILE"
        exit 1
    fi
    
    if ! check_mounts; then
        log_message "=== Health Check FAILED - Mount Issues ==="
        check_nfs_stats
        exit 1
    fi
    
    check_nfs_stats
    log_message "=== Health Check PASSED ==="
    exit 0
}

main
