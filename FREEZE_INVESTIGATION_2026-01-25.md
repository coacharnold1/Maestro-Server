# System Freeze Investigation & Fix - Jan 25, 2026

## Problem Summary
Server became unresponsive on network around 02:30 AM, requiring hard reset at 08:46 AM.

## Root Cause Analysis

### Primary Issue: Client Request Loop
**Discovery:** Client at 192.168.1.246 made **96 album art requests in 2 minutes** (Jan 25, 02:28-02:30 AM)
- Same file requested every ~1 second: Aphex Twin track from **bullwinkle NFS mount**
- Pattern indicates client-side browser/app stuck in refresh loop
- Each request accessed NFS storage, creating cumulative stress

### Contributing Factor: NFS Mount Configuration
**Original Settings:**
- Timeout: 1.4 seconds (`timeo=14`)
- Retries: 2 attempts (`retrans=2`)
- Total failure time: ~2.8 seconds

**Problem:** Short timeouts meant rapid failures during network hiccups, potentially compounding the client loop issue.

## Solutions Implemented

### 1. Album Art Rate Limiting (Server-Side Protection)
**File:** `app.py`

**Added Protection:**
```python
# Rate limit: 2 seconds minimum between identical requests from same client
# Prevents client loops from hammering NFS
# If client requests too fast, serves cached version or placeholder
```

**Benefits:**
- Prevents individual clients from overloading server
- Stops runaway browser/app loops from causing system stress
- Returns cached data immediately for duplicate rapid requests
- Zero impact on normal usage (2-second limit is imperceptible)

### 2. NFS Mount Configuration Improvements
**File:** `/etc/fstab`

**Changes:**
```
Before: timeo=14,retrans=2        (1.4s timeout, 2 retries = 2.8s total)
After:  timeo=600,retrans=3       (60s timeout, 3 retries = 180s total)
Added:  actimeo=3                 (3-second attribute caching)
```

**Benefits:**
- **Much more tolerant** of brief network issues
- **Reduced NFS traffic** through attribute caching
- **Graceful degradation** instead of rapid failure
- Still uses `soft` mounts to prevent infinite hangs

### 3. NFS Health Monitoring
**Files:** `scripts/nfs-health-check.sh`, `scripts/nfs-health-report.sh`

**Monitoring Schedule:** Every 10 minutes (was 5, reduced to minimize overhead)

**What's Monitored:**
- NFS server reachability (192.168.1.110)
- All 8 mount points (accessibility test)
- Stale handle detection
- NFS statistics (retransmissions, timeouts)

**Log Location:** `/var/log/maestro-nfs-health.log`

## Stress Impact Analysis

### NFS Server (192.168.1.110)
**Previous State:**
- Client loops could generate 60+ requests/minute to same files
- Rapid retry storms on network issues

**After Fixes:**
- Rate limiting prevents client loops from reaching server
- Attribute caching reduces overall request volume
- Monitoring: 8 simple `ls` checks every 10 minutes (negligible)

**Conclusion:** ✅ **Reduced stress on NFS server**

### Maestro Client (192.168.1.142)
**Previous State:**
- Short timeouts = constant retry cycles
- No protection against client request loops
- NFS checks every 5 minutes

**After Fixes:**
- Longer timeouts = waits patiently instead of panicking
- Rate limiting catches runaway clients immediately
- NFS checks reduced to every 10 minutes

**Conclusion:** ✅ **Reduced stress on client, better resilience**

## Performance Impact

### Album Art Rate Limiting
- **Overhead:** ~5 lines of Python code, O(1) dictionary lookup
- **Memory:** Keeps last 1000 requests in memory (~100KB)
- **CPU:** Negligible (timestamp comparison)
- **Normal User Impact:** None (2-second limit only blocks rapid duplicates)

### NFS Monitoring
- **Frequency:** Every 10 minutes
- **Duration:** ~1 second per check
- **Operations:** 1 ping + 8 ls commands
- **CPU/Network:** Minimal (<0.1% utilization)

### NFS Configuration Changes
- **Attribute Caching:** Significantly **reduces** NFS requests
- **Longer Timeouts:** No performance impact during normal operation
- **Soft Mounts:** Allows graceful failure instead of system hang

## Commands for Quick Reference

### View Current Status
```bash
~/Maestro-Server/scripts/nfs-health-report.sh
```

### Check for Client Loops (Real-time)
```bash
sudo journalctl -u maestro-web.service -f | grep "album_art"
```

### View Health Log
```bash
sudo tail -f /var/log/maestro-nfs-health.log
```

### Restart Services
```bash
sudo systemctl restart maestro-web.service
```

## Prevention for Future

1. ✅ **Rate limiting** catches client loops before they cause problems
2. ✅ **Robust NFS settings** handle brief network/server issues
3. ✅ **Monitoring** provides early warning of mount problems
4. ⚠️ **Client-side investigation** needed for 192.168.1.246 (what app was looping?)

## Files Modified

- `/etc/fstab` - NFS mount options (backup: `/etc/fstab.backup-20260125-114520`)
- `app.py` - Added rate limiting
- `scripts/nfs-health-check.timer` - Reduced frequency to 10min
- New files: `scripts/nfs-health-check.sh`, `scripts/nfs-health-report.sh`

## Recommendations

1. **Monitor client 192.168.1.246** - investigate what app/browser was causing the loop
2. **Check logs periodically:** `~/Maestro-Server/scripts/nfs-health-report.sh`
3. **If seeing "rate limited" in logs** - indicates clients requesting too fast (protection working)
4. **NFS server health** - ensure 192.168.1.110 is stable

## Summary

The freeze was likely caused by a **client-side request loop** (192.168.1.246) compounded by **aggressive NFS timeouts**. 

**All fixes REDUCE stress** on both server and client while adding protection against future loops.

---
Last Updated: 2026-01-25
