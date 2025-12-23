#!/usr/bin/env python3
"""
Maestro Admin API
System administration interface for MPD server configuration
Runs on port 5004, separate from main web UI (port 5003)
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import subprocess
import psutil
import socket
import os
import json
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'maestro-admin-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration file paths
CONFIG_DIR = Path.home() / '.config' / 'maestro'
MOUNTS_CONFIG = CONFIG_DIR / 'mounts.json'
AUDIO_CONFIG = CONFIG_DIR / 'audio.json'

# Ensure config directory exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def run_command(command, require_sudo=False):
    """Execute shell command and return output"""
    try:
        if require_sudo:
            # Use full path to sudo for systemd services
            command = ['/usr/bin/sudo'] + command if isinstance(command, list) else f'/usr/bin/sudo {command}'
        
        # Use longer timeout for system updates and other long operations
        timeout = 300 if 'apt upgrade' in str(command) or 'pacman' in str(command) else 30
        
        result = subprocess.run(
            command,
            shell=isinstance(command, str),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Command timeout', 'stdout': '', 'stderr': ''}
    except Exception as e:
        return {'success': False, 'error': str(e), 'stdout': '', 'stderr': ''}

def get_system_info():
    """Get current system information"""
    try:
        # Get IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
    except:
        ip_address = "Unknown"
    
    # Get memory info
    memory = psutil.virtual_memory()
    
    # Get disk info
    disk = psutil.disk_usage('/')
    
    # Get uptime
    boot_time = psutil.boot_time()
    uptime_seconds = psutil.time.time() - boot_time
    uptime_hours = uptime_seconds / 3600
    
    return {
        'ip_address': ip_address,
        'hostname': socket.gethostname(),
        'memory': {
            'total': memory.total,
            'used': memory.used,
            'free': memory.available,
            'percent': memory.percent
        },
        'disk': {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        },
        'uptime_hours': round(uptime_hours, 1),
        'cpu_percent': psutil.cpu_percent(interval=1)
    }

# ============================================================================
# ROUTES - MAIN PAGES
# ============================================================================

@app.route('/')
def index():
    """Admin dashboard home"""
    return render_template('admin_home.html')

@app.route('/library')
def library_page():
    """Library management page"""
    return render_template('library_management.html')

@app.route('/audio')
def audio_page():
    """Audio tweaks page"""
    return render_template('audio_tweaks.html')

@app.route('/system')
def system_page():
    """System administration page"""
    return render_template('system_admin.html')

@app.route('/cd-ripper')
def cd_ripper_page():
    """CD ripper page"""
    return render_template('cd_ripper.html')

@app.route('/cd-settings')
def cd_settings_page():
    """CD settings page"""
    return render_template('cd_settings.html')

@app.route('/files')
def file_browser_page():
    """File browser page"""
    return render_template('file_browser.html')

# ============================================================================
# API ENDPOINTS - SYSTEM INFO
# ============================================================================

@app.route('/api/system/info', methods=['GET'])
def api_system_info():
    """Get current system information"""
    try:
        info = get_system_info()
        return jsonify({'status': 'success', 'info': info})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/system/reboot', methods=['POST'])
def api_system_reboot():
    """Reboot the system"""
    try:
        # Schedule reboot in 5 seconds to allow response to be sent
        result = run_command('shutdown -r +1 "Rebooting via Maestro Admin"', require_sudo=True)
        if result['success']:
            return jsonify({'status': 'success', 'message': 'System will reboot in 1 minute'})
        else:
            return jsonify({'status': 'error', 'message': result.get('stderr', 'Unknown error')}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/system/update', methods=['POST'])
def api_system_update():
    """Update the operating system"""
    try:
        # Detect package manager
        if os.path.exists('/usr/bin/apt'):
            # Debian/Ubuntu - run update first, then upgrade
            update_result = run_command('apt update', require_sudo=True)
            
            if not update_result['success']:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to update package list',
                    'output': update_result.get('stderr', 'Unknown error')
                }), 500
            
            # Now run upgrade
            upgrade_result = run_command('apt upgrade -y', require_sudo=True)
            
            # Check if sudo failed due to password requirement
            stderr = upgrade_result.get('stderr', '')
            if 'sudo: a password is required' in stderr or 'sudo: no tty present' in stderr:
                return jsonify({
                    'status': 'error',
                    'message': 'Sudo password required. Configure NOPASSWD in sudoers for: apt',
                    'output': 'To fix: sudo visudo -f /etc/sudoers.d/maestro\nAdd: ' + os.environ.get('USER', 'fausto') + ' ALL=(ALL) NOPASSWD: /usr/bin/apt'
                }), 500
            
            # Parse output to see what was upgraded
            output = upgrade_result.get('stdout', '')
            lines = output.split('\n')
            
            # Count upgraded packages
            upgraded_count = 0
            for line in lines:
                if ' upgraded,' in line:
                    parts = line.split()
                    if len(parts) > 0 and parts[0].isdigit():
                        upgraded_count = int(parts[0])
                    break
            
            if upgrade_result['success']:
                return jsonify({
                    'status': 'success',
                    'message': f'System update completed! {upgraded_count} package(s) upgraded.',
                    'output': output,
                    'packages_upgraded': upgraded_count,
                    'update_output': update_result.get('stdout', '')
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Upgrade failed',
                    'output': upgrade_result.get('stderr', 'Unknown error')
                }), 500
                
        elif os.path.exists('/usr/bin/pacman'):
            # Arch Linux
            result = run_command('pacman -Syu --noconfirm', require_sudo=True)
            
            if result['success']:
                return jsonify({
                    'status': 'success',
                    'message': 'System updated successfully (Arch Linux)',
                    'output': result['stdout']
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': result.get('stderr', 'Update failed')
                }), 500
        else:
            return jsonify({'status': 'error', 'message': 'Unsupported package manager'}), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# API ENDPOINTS - LIBRARY MANAGEMENT
# ============================================================================

@app.route('/api/library/mounts', methods=['GET'])
def api_get_mounts():
    """Get configured network mounts"""
    try:
        # Load mounts from config file
        if MOUNTS_CONFIG.exists():
            with open(MOUNTS_CONFIG, 'r') as f:
                mounts = json.load(f)
        else:
            mounts = []
        
        # Also read existing mounts from /etc/fstab
        fstab_mounts = []
        try:
            with open('/etc/fstab', 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 3:
                        device, mount_point, fs_type = parts[0], parts[1], parts[2]
                        
                        # Only include NFS and CIFS/SMB mounts
                        if fs_type in ['nfs', 'nfs4', 'cifs']:
                            mount_type = 'nfs' if fs_type in ['nfs', 'nfs4'] else 'smb'
                            
                            # Parse NFS share (e.g., 192.168.1.110:/media/MrBig/music)
                            if ':' in device and mount_type == 'nfs':
                                server, share_path = device.split(':', 1)
                            elif mount_type == 'smb':
                                # SMB format: //server/share
                                server = device.replace('//', '').split('/')[0] if '//' in device else device
                                share_path = '/' + '/'.join(device.replace('//', '').split('/')[1:]) if '//' in device else device
                            else:
                                server = device
                                share_path = device
                            
                            # Generate a friendly name from the mount point
                            # e.g., /media/music/mrbig -> "mrbig"
                            mount_name = mount_point.rstrip('/').split('/')[-1].title()
                            
                            fstab_mount = {
                                'id': f"fstab-{len(fstab_mounts)}",
                                'name': mount_name,
                                'type': mount_type,
                                'server': server,
                                'share_path': share_path,
                                'mount_point': mount_point,
                                'options': parts[3] if len(parts) > 3 else 'defaults',
                                'status': 'mounted' if os.path.ismount(mount_point) else 'unmounted',
                                'source': 'fstab'  # Mark as fstab entry (read-only)
                            }
                            fstab_mounts.append(fstab_mount)
        except Exception as e:
            print(f"Warning: Could not read /etc/fstab: {e}")
        
        # Check mount status for config-managed mounts
        for mount in mounts:
            mount_point = mount.get('mount_point')
            if mount_point and os.path.ismount(mount_point):
                mount['status'] = 'mounted'
            else:
                mount['status'] = 'unmounted'
            mount['source'] = 'config'  # Mark as config-managed
        
        # Combine both lists (fstab first, then config)
        all_mounts = fstab_mounts + mounts
        
        return jsonify({'status': 'success', 'mounts': all_mounts})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/library/mounts', methods=['POST'])
def api_add_mount():
    """Add a new network mount configuration"""
    try:
        data = request.json
        mount_type = data.get('type')  # 'nfs' or 'smb'
        name = data.get('name')
        server = data.get('server')
        share_path = data.get('share_path')
        mount_point = data.get('mount_point')
        username = data.get('username', '')
        password = data.get('password', '')
        
        # Validate required fields
        if not all([mount_type, name, server, share_path, mount_point]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Enforce standard music directory structure
        # All mounts should be inside /media/music/
        if not mount_point.startswith('/media/music/'):
            # Extract the subdirectory name from the mount point
            subdirectory = os.path.basename(mount_point.rstrip('/'))
            mount_point = f'/media/music/{subdirectory}'
            print(f"[INFO] Standardized mount point to: {mount_point}")
        
        # Create the mount point directory
        try:
            os.makedirs(mount_point, exist_ok=True)
            print(f"[INFO] Created mount point directory: {mount_point}")
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Failed to create mount point: {str(e)}'}), 500
        
        # Load existing mounts
        if MOUNTS_CONFIG.exists():
            with open(MOUNTS_CONFIG, 'r') as f:
                mounts = json.load(f)
        else:
            mounts = []
        
        # Add new mount
        new_mount = {
            'id': len(mounts) + 1,
            'type': mount_type,
            'name': name,
            'server': server,
            'share_path': share_path,
            'mount_point': mount_point,
            'username': username,
            'password': password,  # In production, encrypt this!
            'status': 'unmounted'
        }
        mounts.append(new_mount)
        
        # Save configuration
        with open(MOUNTS_CONFIG, 'w') as f:
            json.dump(mounts, f, indent=2)
        
        return jsonify({'status': 'success', 'message': 'Mount configuration added', 'mount': new_mount})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/library/mounts/<int:mount_id>/mount', methods=['POST'])
def api_mount_share(mount_id):
    """Mount a configured network share with optimized NFS options"""
    try:
        # Load mounts
        if not MOUNTS_CONFIG.exists():
            return jsonify({'status': 'error', 'message': 'No mounts configured'}), 404
        
        with open(MOUNTS_CONFIG, 'r') as f:
            mounts = json.load(f)
        
        # Find mount
        mount = next((m for m in mounts if m['id'] == mount_id), None)
        if not mount:
            return jsonify({'status': 'error', 'message': 'Mount not found'}), 404
        
        mount_point = mount['mount_point']
        
        # Create mount point if it doesn't exist
        os.makedirs(mount_point, exist_ok=True)
        
        # Build mount command with optimized options for MPD stability
        if mount['type'] == 'nfs':
            # NFS options optimized for reliability with MPD:
            # - auto: mount at boot
            # - x-systemd.automount: auto-remount on access
            # - x-systemd.requires: wait for network
            # - _netdev: network filesystem
            # - ro: read-only (adjust if you need write access)
            # - timeo=30: 3 second timeout (30 deciseconds)
            # - retrans=2: retry twice
            # - soft: fail after timeout (vs hard which hangs)
            # - nofail: don't fail boot if unavailable
            # - intr: allow interruption of hung operations
            nfs_opts = "auto,x-systemd.automount,x-systemd.requires=network-online.target,_netdev,ro,timeo=30,retrans=2,soft,nofail,intr"
            cmd = f"mount -t nfs -o {nfs_opts} {mount['server']}:{mount['share_path']} {mount_point}"
        elif mount['type'] == 'smb':
            creds = ""
            if mount['username']:
                creds = f"username={mount['username']},password={mount['password']}"
            smb_opts = "auto,x-systemd.automount,x-systemd.requires=network-online.target,_netdev,nofail"
            cmd = f"mount -t cifs //{mount['server']}/{mount['share_path']} {mount_point}"
            if creds:
                cmd += f" -o {smb_opts},{creds}"
            else:
                cmd += f" -o {smb_opts}"
        else:
            return jsonify({'status': 'error', 'message': 'Unknown mount type'}), 400
        
        # Execute mount
        result = run_command(cmd, require_sudo=True)
        
        if result['success']:
            return jsonify({'status': 'success', 'message': f"Mounted {mount['name']} with optimized options"})
        else:
            return jsonify({'status': 'error', 'message': result.get('stderr', 'Mount failed')}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/library/mounts/<int:mount_id>/unmount', methods=['POST'])
def api_unmount_share(mount_id):
    """Unmount a network share"""
    try:
        # Load mounts
        if not MOUNTS_CONFIG.exists():
            return jsonify({'status': 'error', 'message': 'No mounts configured'}), 404
        
        with open(MOUNTS_CONFIG, 'r') as f:
            mounts = json.load(f)
        
        # Find mount
        mount = next((m for m in mounts if m['id'] == mount_id), None)
        if not mount:
            return jsonify({'status': 'error', 'message': 'Mount not found'}), 404
        
        # Execute unmount
        result = run_command(f"umount {mount['mount_point']}", require_sudo=True)
        
        if result['success']:
            return jsonify({'status': 'success', 'message': f"Unmounted {mount['name']}"})
        else:
            return jsonify({'status': 'error', 'message': result.get('stderr', 'Unmount failed')}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/library/mounts/<int:mount_id>', methods=['DELETE'])
def api_delete_mount(mount_id):
    """Delete a mount configuration"""
    try:
        if not MOUNTS_CONFIG.exists():
            return jsonify({'status': 'error', 'message': 'No mounts configured'}), 404
        
        with open(MOUNTS_CONFIG, 'r') as f:
            mounts = json.load(f)
        
        # Remove mount
        mounts = [m for m in mounts if m['id'] != mount_id]
        
        # Save
        with open(MOUNTS_CONFIG, 'w') as f:
            json.dump(mounts, f, indent=2)
        
        return jsonify({'status': 'success', 'message': 'Mount configuration deleted'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/library/mounts/<int:mount_id>/add-to-fstab', methods=['POST'])
def api_add_mount_to_fstab(mount_id):
    """Add a mount configuration to /etc/fstab for persistence across reboots"""
    try:
        # Load mounts
        if not MOUNTS_CONFIG.exists():
            return jsonify({'status': 'error', 'message': 'No mounts configured'}), 404
        
        with open(MOUNTS_CONFIG, 'r') as f:
            mounts = json.load(f)
        
        # Find mount
        mount = next((m for m in mounts if m['id'] == mount_id), None)
        if not mount:
            return jsonify({'status': 'error', 'message': 'Mount not found'}), 404
        
        # Check if already in fstab
        try:
            with open('/etc/fstab', 'r') as f:
                fstab_content = f.read()
                if mount['mount_point'] in fstab_content:
                    return jsonify({'status': 'warning', 'message': 'Mount point already exists in fstab'}), 400
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Cannot read fstab: {str(e)}'}), 500
        
        # Build fstab entry with optimized options
        if mount['type'] == 'nfs':
            device = f"{mount['server']}:{mount['share_path']}"
            fs_type = "nfs"
            # Optimized NFS options for MPD stability
            options = "auto,x-systemd.automount,x-systemd.requires=network-online.target,_netdev,ro,timeo=30,retrans=2,soft,nofail,intr"
        elif mount['type'] == 'smb':
            device = f"//{mount['server']}/{mount['share_path']}"
            fs_type = "cifs"
            options = "auto,x-systemd.automount,x-systemd.requires=network-online.target,_netdev,nofail"
            if mount.get('username'):
                # Note: In production, use credentials file instead of password in fstab
                options += f",username={mount['username']},password={mount['password']}"
        else:
            return jsonify({'status': 'error', 'message': 'Unknown mount type'}), 400
        
        # Create fstab entry
        fstab_entry = f"\n# Maestro-managed mount: {mount['name']}\n"
        fstab_entry += f"{device} {mount['mount_point']} {fs_type} {options} 0 0\n"
        
        # Append to fstab
        try:
            # Use tee to write with sudo
            cmd = f"echo '{fstab_entry}' | sudo tee -a /etc/fstab"
            result = run_command(cmd, require_sudo=False)  # sudo already in command
            
            if not result['success']:
                return jsonify({'status': 'error', 'message': f"Failed to update fstab: {result.get('stderr', 'Unknown error')}"}), 500
            
            # Reload systemd
            run_command("systemctl daemon-reload", require_sudo=True)
            
            return jsonify({
                'status': 'success',
                'message': f"Added {mount['name']} to /etc/fstab. Mount will persist across reboots.",
                'fstab_entry': fstab_entry.strip()
            })
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Failed to update fstab: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Save
        with open(MOUNTS_CONFIG, 'w') as f:
            json.dump(mounts, f, indent=2)
        
        return jsonify({'status': 'success', 'message': 'Mount configuration deleted'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/library/update', methods=['POST'])
def api_update_library():
    """Trigger MPD library update"""
    try:
        import mpd
        
        # Connect to MPD
        client = mpd.MPDClient()
        client.timeout = 10
        client.idletimeout = None
        
        try:
            client.connect('localhost', 6600)
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Cannot connect to MPD: {str(e)}',
                'mpd_host': 'localhost:6600'
            }), 500
        
        # Get stats before update
        try:
            stats_before = client.stats()
            songs_before = int(stats_before.get('songs', 0))
            albums_before = int(stats_before.get('albums', 0))
            artists_before = int(stats_before.get('artists', 0))
        except:
            songs_before = albums_before = artists_before = 0
        
        # Trigger update
        try:
            update_job = client.update()  # Returns job ID
        except Exception as e:
            client.close()
            return jsonify({
                'status': 'error',
                'message': f'Failed to trigger update: {str(e)}'
            }), 500
        
        # Wait a moment for update to process
        import time
        time.sleep(2)
        
        # Get stats after update
        try:
            stats_after = client.stats()
            songs_after = int(stats_after.get('songs', 0))
            albums_after = int(stats_after.get('albums', 0))
            artists_after = int(stats_after.get('artists', 0))
            db_update = stats_after.get('db_update', 0)
        except:
            songs_after = albums_after = artists_after = 0
            db_update = 0
        
        client.close()
        
        # Calculate changes
        songs_added = songs_after - songs_before
        albums_added = albums_after - albums_before
        artists_added = artists_after - artists_before
        
        return jsonify({
            'status': 'success',
            'message': 'MPD library update completed!',
            'update_job_id': update_job,
            'stats': {
                'songs': songs_after,
                'albums': albums_after,
                'artists': artists_after,
                'songs_added': songs_added,
                'albums_added': albums_added,
                'artists_added': artists_added
            },
            'db_update_time': db_update
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/library/mpd-info', methods=['GET'])
def api_get_mpd_info():
    """Get MPD music directory and existing folder structure"""
    try:
        # Read MPD config for music_directory
        mpd_config_paths = ['/etc/mpd.conf', os.path.expanduser('~/.mpdconf')]
        music_dir = '/media/music'  # default
        
        for config_path in mpd_config_paths:
            if os.path.exists(config_path):
                with open(config_path) as f:
                    for line in f:
                        if line.strip().startswith('music_directory') and not line.strip().startswith('#'):
                            # Extract path from quotes
                            music_dir = line.split('"')[1]
                            break
                break
        
        # List directories under music_dir
        directories = []
        if os.path.exists(music_dir):
            for item in sorted(os.listdir(music_dir)):
                path = os.path.join(music_dir, item)
                if os.path.isdir(path):
                    # Check if it's a mount point
                    is_mount = os.path.ismount(path)
                    
                    # Get basic info
                    stat_info = os.stat(path)
                    
                    # Count files - skip for network mounts (too slow)
                    if is_mount:
                        # For network mounts, just show that it's a network share
                        file_count = 'network'
                    else:
                        # Count files for local directories only
                        file_count = '?'
                        try:
                            if os.access(path, os.R_OK):
                                count_result = subprocess.run(
                                    ['find', path, '-type', 'f', '-readable'],
                                    capture_output=True,
                                    text=True,
                                    timeout=5  # Quick timeout for local dirs
                                )
                                if count_result.returncode == 0:
                                    lines = count_result.stdout.strip().split('\n') if count_result.stdout.strip() else []
                                    file_count = len([l for l in lines if l])
                                else:
                                    file_count = '?'
                            else:
                                file_count = 'no access'
                        except subprocess.TimeoutExpired:
                            file_count = '10000+'
                        except Exception as e:
                            file_count = '?'
                    
                    directories.append({
                        'name': item,
                        'path': path,
                        'is_mount': is_mount,
                        'owner': stat_info.st_uid,
                        'file_count': file_count
                    })
        
        return jsonify({
            'status': 'success',
            'music_directory': music_dir,
            'directories': directories,
            'total_folders': len(directories)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# API ENDPOINTS - AUDIO CONFIGURATION
# ============================================================================

@app.route('/api/audio/devices', methods=['GET'])
def api_get_audio_devices():
    """Get available audio devices"""
    try:
        # Use explicit path and sudo
        result = run_command(['/usr/bin/aplay', '-l'], require_sudo=True)
        devices = []
        parsed_devices = []
        raw_output = result.get('stdout', result.get('output', ''))
        
        if result['success']:
            # Parse aplay output - look for card lines
            # Format: card 0: PCH [HDA Intel PCH], device 0: ALC887-VD Analog [ALC887-VD Analog]
            for line in raw_output.split('\n'):
                if line.startswith('card'):
                    devices.append(line.strip())
                    # Extract card and device numbers
                    try:
                        parts = line.split(':')
                        card_info = parts[0].strip()
                        card_num = card_info.split()[1]
                        
                        # Look for device number
                        if 'device' in line:
                            device_part = line.split('device')[1].split(':')[0].strip()
                            device_num = device_part.split()[0]
                            
                            # Extract device name
                            name_start = line.find('[', line.find('[') + 1) + 1
                            name_end = line.rfind(']')
                            device_name = line[name_start:name_end] if name_start > 0 else f"Card {card_num} Device {device_num}"
                            
                            parsed_devices.append({
                                'card': card_num,
                                'device': device_num,
                                'hw_string': f"hw:{card_num},{device_num}",
                                'name': device_name
                            })
                    except:
                        pass
        
        return jsonify({
            'status': 'success',
            'devices': devices,
            'parsed_devices': parsed_devices,
            'raw_output': raw_output,
            'device_count': len(devices)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/audio/config', methods=['GET'])
def api_get_audio_config():
    """Get current audio configuration"""
    try:
        if AUDIO_CONFIG.exists():
            with open(AUDIO_CONFIG, 'r') as f:
                config = json.load(f)
        else:
            # Audiophile defaults - bit-perfect playback
            config = {
                'buffer_size': 4096,
                'output_format': 'native',  # Let DAC handle native format
                'resample_quality': 'disabled',  # Bit-perfect
                'mixer_type': 'none',  # Use DAC volume
                'dsd_mode': 'auto'  # Native DSD if supported
            }
        
        # Read current device from MPD config
        current_device = 'default'
        try:
            with open('/etc/mpd.conf', 'r') as f:
                mpd_config = f.read()
            import re
            # Look for device line in ALSA audio_output block
            match = re.search(r'audio_output\s*\{[^}]*type\s*"alsa"[^}]*device\s*"([^"]+)"', mpd_config, re.DOTALL)
            if match:
                current_device = match.group(1)
        except:
            pass
        
        config['current_device'] = current_device
        
        return jsonify({'status': 'success', 'config': config})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/audio/config', methods=['POST'])
def api_save_audio_config():
    """Save audio configuration and update MPD config"""
    try:
        config = request.json
        
        # Ensure config directory exists
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(AUDIO_CONFIG, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Update MPD configuration file
        mpd_updated = False
        try:
            audio_device = config.get('audio_device', 'default')
            mixer_type = config.get('mixer_type', 'none')
            
            # Read current MPD config
            mpd_config_path = '/etc/mpd.conf'
            with open(mpd_config_path, 'r') as f:
                mpd_config = f.read()
            
            # Find and update the audio_output section
            import re
            # Pattern to match the ALSA audio output block
            pattern = r'(audio_output\s*\{[^}]*type\s*"alsa"[^}]*)\}'
            
            def update_alsa_config(match):
                block = match.group(1)
                # Remove old device line if exists
                block = re.sub(r'\s*device\s*"[^"]*"\n', '', block)
                # Remove old mixer_type line if exists
                block = re.sub(r'\s*mixer_type\s*"[^"]*"\n', '', block)
                
                # Add device line if not default
                if audio_device != 'default':
                    block += f'\n    device          "{audio_device}"'
                
                # Add mixer_type
                block += f'\n    mixer_type      "{mixer_type}"'
                
                return block + '\n}'
            
            new_config = re.sub(pattern, update_alsa_config, mpd_config, flags=re.DOTALL)
            
            # Write updated config using sudo tee
            import subprocess
            proc = subprocess.run(
                ['/usr/bin/sudo', 'tee', mpd_config_path], 
                input=new_config.encode(), 
                capture_output=True,
                timeout=10
            )
            if proc.returncode == 0:
                mpd_updated = True
        except Exception as e:
            print(f"Error updating MPD config: {e}")
        
        return jsonify({
            'status': 'success',
            'message': 'Audio configuration saved. Restart MPD to apply changes.',
            'saved_config': config,
            'config_file': str(AUDIO_CONFIG),
            'mpd_updated': mpd_updated
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/audio/system-tweaks', methods=['POST'])
def api_apply_system_tweaks():
    """Apply system-level audio optimizations"""
    try:
        config = request.json
        cpu_governor = config.get('cpu_governor', 'ondemand')
        mpd_priority = config.get('mpd_priority', 'high')
        swappiness = config.get('swappiness', 10)
        
        results = []
        
        # Set CPU governor
        if cpu_governor:
            result = run_command(
                f"echo {cpu_governor} | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor",
                require_sudo=True
            )
            if result['success']:
                results.append(f"CPU governor set to {cpu_governor}")
            else:
                results.append(f"CPU governor failed: {result.get('stderr', 'Unknown error')}")
        
        # Set swappiness
        result = run_command(f"sysctl -w vm.swappiness={swappiness}", require_sudo=True)
        if result['success']:
            results.append(f"Swappiness set to {swappiness}")
            # Make it persistent
            run_command(
                f"echo 'vm.swappiness={swappiness}' | tee -a /etc/sysctl.conf",
                require_sudo=True
            )
        
        # Set MPD priority (would need to restart MPD with nice/renice)
        # This is a placeholder - actual implementation would modify systemd service
        results.append(f"MPD priority: {mpd_priority} (requires service restart)")
        
        return jsonify({
            'status': 'success',
            'message': 'System tweaks applied',
            'details': results
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# LOGS API
# ============================================================================

@app.route('/logs')
def logs_page():
    """Render the logs viewer page"""
    return render_template('system_logs.html')

@app.route('/api/logs/<log_type>', methods=['GET'])
def api_get_logs(log_type):
    """
    Get system logs for different services
    Query params: lines (default 500)
    """
    try:
        lines = int(request.args.get('lines', 500))
        
        if log_type == 'mpd':
            # MPD logs from systemd journal
            result = run_command(['journalctl', '-u', 'mpd.service', '-n', str(lines), '--no-pager'], require_sudo=True)
        elif log_type == 'maestro-web':
            # Maestro Web UI logs
            result = run_command(['journalctl', '-u', 'maestro-web.service', '-n', str(lines), '--no-pager'], require_sudo=True)
        elif log_type == 'maestro-admin':
            # Maestro Admin API logs
            result = run_command(['journalctl', '-u', 'maestro-admin.service', '-n', str(lines), '--no-pager'], require_sudo=True)
        elif log_type == 'system':
            # General system logs (filtered for relevant entries)
            result = run_command(['journalctl', '-n', str(lines), '--no-pager', '-p', 'warning'], require_sudo=True)
        else:
            return jsonify({'success': False, 'error': 'Invalid log type'}), 400
        
        if result['success']:
            # Split into lines and filter out empty lines
            logs = [line for line in result['stdout'].split('\n') if line.strip()]
            return jsonify({
                'success': True,
                'logs': logs,
                'log_type': log_type,
                'line_count': len(logs)
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('stderr', 'Failed to fetch logs')
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mpd/backup', methods=['POST'])
def backup_mpd_database():
    """Create a timestamped backup of the MPD database"""
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'/var/lib/mpd/database.backup.{timestamp}'
        
        # Copy database file
        result = run_command(
            ['cp', '/var/lib/mpd/database', backup_path],
            require_sudo=True
        )
        
        if result['success']:
            # Get backup file size
            size_result = run_command(['du', '-h', backup_path], require_sudo=True)
            size = size_result['stdout'].split()[0] if size_result['success'] else 'unknown'
            
            return jsonify({
                'success': True,
                'message': f'Database backed up to {backup_path} ({size})',
                'backup_path': backup_path,
                'timestamp': timestamp
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('stderr', 'Failed to create backup')
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mpd/backups', methods=['GET'])
def list_mpd_backups():
    """List available MPD database backups"""
    try:
        from datetime import datetime
        
        # Find all backup files
        result = run_command(
            ['find', '/var/lib/mpd/', '-name', 'database.backup.*', '-type', 'f'],
            require_sudo=True
        )
        
        if not result['success']:
            return jsonify({'success': False, 'error': 'Failed to list backups'}), 500
        
        backups = []
        for line in result['stdout'].strip().split('\n'):
            if not line:
                continue
                
            # Get file info
            basename = os.path.basename(line)
            size_result = run_command(['du', '-h', line], require_sudo=True)
            size = size_result['stdout'].split()[0] if size_result['success'] else 'unknown'
            
            # Get modification time in local timezone
            stat_result = run_command(['stat', '-c', '%y', line], require_sudo=True)
            if stat_result['success']:
                from datetime import datetime
                # Parse the timestamp - stat already returns local time
                timestamp_str = stat_result['stdout'].strip()
                # Format: 2025-12-18 19:22:17.123456789 -0500
                try:
                    # Extract just the date and time part
                    dt_str = timestamp_str.split('.')[0]
                    dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                    date_str = dt.strftime('%b %d, %I:%M:%S %p')
                except:
                    date_str = timestamp_str.split('.')[0]
            else:
                date_str = 'unknown'
            
            backups.append({
                'name': basename,
                'path': line,
                'size': size,
                'date': date_str
            })
        
        # Sort by name (timestamp) descending and limit to 3 most recent
        backups.sort(key=lambda x: x['name'], reverse=True)
        backups = backups[:3]
        
        return jsonify({
            'success': True,
            'backups': backups,
            'count': len(backups)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mpd/restore', methods=['POST'])
def restore_mpd_database():
    """Restore MPD database from a backup"""
    try:
        data = request.get_json()
        backup_file = data.get('backup_file')
        
        if not backup_file:
            return jsonify({'success': False, 'error': 'No backup file specified'}), 400
        
        # Validate backup file exists
        backup_path = f'/var/lib/mpd/{backup_file}'
        check_result = run_command(['test', '-f', backup_path], require_sudo=True)
        
        if not check_result['success']:
            return jsonify({'success': False, 'error': 'Backup file not found'}), 404
        
        # Stop MPD
        stop_result = run_command(['systemctl', 'stop', 'mpd'], require_sudo=True)
        if not stop_result['success']:
            return jsonify({'success': False, 'error': 'Failed to stop MPD'}), 500
        
        # Copy backup to database
        restore_result = run_command(
            ['cp', backup_path, '/var/lib/mpd/database'],
            require_sudo=True
        )
        
        if not restore_result['success']:
            # Try to restart MPD even if restore failed
            run_command(['systemctl', 'start', 'mpd'], require_sudo=True)
            return jsonify({'success': False, 'error': 'Failed to restore database'}), 500
        
        # Start MPD
        start_result = run_command(['systemctl', 'start', 'mpd'], require_sudo=True)
        
        if start_result['success']:
            return jsonify({
                'success': True,
                'message': f'Database restored from {backup_file} and MPD restarted'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Database restored but MPD failed to start'
            }), 500
            
    except Exception as e:
        # Try to restart MPD on error
        run_command(['systemctl', 'start', 'mpd'], require_sudo=True)
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# CD RIPPER API
# ============================================================================

# Cache for CD metadata to avoid repeatedly querying the disc
cd_metadata_cache = {
    'disc_id': None,
    'mb_disc_id': None,
    'metadata': None,
    'timestamp': 0
}

# Storage for edited metadata
cd_edited_metadata = {}

# Global rip status
rip_status = {
    'active': False,
    'progress': 0,
    'current_track': 0,
    'total_tracks': 0,
    'status': 'idle',
    'error': None
}

def load_cd_settings():
    """Helper function to load CD settings"""
    settings_file = Path.home() / 'maestro' / 'settings.json'
    try:
        with open(settings_file, 'r') as f:
            settings = json.load(f)
    except:
        settings = {}
    
    cd_settings = settings.get('cd_ripper', {})
    auto_rip = cd_settings.get('auto_rip', {})
    album_art = cd_settings.get('album_art', {})
    
    # Provide defaults
    return {
        'enabled': cd_settings.get('enabled', True),
        'output_dir': cd_settings.get('output_dir', '/media/music/ripped'),
        'format': cd_settings.get('format', 'flac'),
        'quality': cd_settings.get('quality', 'high'),
        'metadata_provider': cd_settings.get('metadata_provider', 'musicbrainz'),
        'auto_eject': cd_settings.get('auto_eject', True),
        'parallel_encode': cd_settings.get('parallel_encode', True),
        'max_processes': cd_settings.get('max_processes', 4),
        'auto_rip_enabled': auto_rip.get('enabled', False),
        'skip_confirmation': auto_rip.get('skip_confirmation', True),
        'auto_eject_when_done': auto_rip.get('auto_eject_when_done', True),
        'album_art_embed': album_art.get('embed', True),
        'album_art_file': album_art.get('save_file', True)
    }

@app.route('/api/cd/settings')
def get_cd_settings():
    """Get CD ripper configuration"""
    try:
        cd_settings = load_cd_settings()
        return jsonify({'status': 'success', 'settings': cd_settings})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/cd/settings', methods=['POST'])
def update_cd_settings():
    """Update CD ripper configuration"""
    try:
        data = request.json
        settings = load_settings()
        
        # Validate output directory
        output_dir = data.get('output_dir')
        if output_dir and not os.path.isdir(output_dir):
            return jsonify({'status': 'error', 'error': 'Invalid output directory'}), 400
        
        # Ensure cd_ripper section exists
        if 'cd_ripper' not in settings:
            settings['cd_ripper'] = {}
        
        # Update basic settings
        settings['cd_ripper']['enabled'] = data.get('enabled', True)
        settings['cd_ripper']['output_dir'] = output_dir or '/media/music/ripped'
        settings['cd_ripper']['format'] = data.get('format', 'flac')
        settings['cd_ripper']['quality'] = data.get('quality', 'high')
        settings['cd_ripper']['metadata_provider'] = data.get('metadata_provider', 'musicbrainz')
        settings['cd_ripper']['auto_eject'] = data.get('auto_eject', True)
        settings['cd_ripper']['parallel_encode'] = data.get('parallel_encode', True)
        settings['cd_ripper']['max_processes'] = data.get('max_processes', 4)
        
        # Update auto_rip settings
        if 'auto_rip' not in settings['cd_ripper']:
            settings['cd_ripper']['auto_rip'] = {}
        if 'auto_rip_enabled' in data:
            settings['cd_ripper']['auto_rip']['enabled'] = data['auto_rip_enabled']
        if 'skip_confirmation' in data:
            settings['cd_ripper']['auto_rip']['skip_confirmation'] = data['skip_confirmation']
        if 'auto_eject_when_done' in data:
            settings['cd_ripper']['auto_rip']['auto_eject_when_done'] = data['auto_eject_when_done']
        
        # Update album art settings
        if 'album_art' not in settings['cd_ripper']:
            settings['cd_ripper']['album_art'] = {}
        if 'album_art_embed' in data:
            settings['cd_ripper']['album_art']['embed'] = data['album_art_embed']
        if 'album_art_file' in data:
            settings['cd_ripper']['album_art']['save_file'] = data['album_art_file']
        
        save_settings(settings)
        return jsonify({'status': 'success', 'message': 'Settings updated'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/cd/drives')
def get_cd_drives():
    """List available CD drives (local and USB)"""
    try:
        drives = []
        
        # Check common device paths
        for device in ['/dev/cdrom', '/dev/sr0', '/dev/sr1', '/dev/sr2']:
            if os.path.exists(device):
                real_device = os.path.realpath(device)
                
                # Try to get model info
                try:
                    model_path = f'/sys/block/{os.path.basename(real_device)}/device/model'
                    with open(model_path, 'r') as f:
                        model = f.read().strip()
                except:
                    model = 'Unknown'
                
                drives.append({
                    'device': device,
                    'real_device': real_device,
                    'name': os.path.basename(real_device),
                    'model': model,
                    'type': 'USB' if 'usb' in real_device.lower() else 'Internal'
                })
        
        return jsonify({'success': True, 'drives': drives, 'count': len(drives)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cd/status')
def get_cd_status():
    """Check if CD is inserted and get basic info"""
    try:
        # Use cdparanoia to detect if disc is present
        result = run_command(['/usr/bin/cdparanoia', '-Q'])
        
        # Check if command executed (may have error key if failed)
        if 'error' in result:
            return jsonify({
                'success': True,
                'disc_present': False,
                'track_count': 0,
                'message': f"No disc in drive: {result.get('error', 'unknown')}"
            })
        
        # cdparanoia exits with 0 if disc found, non-zero if no disc
        disc_present = result.get('returncode') == 0
        
        # Get track count if disc is present
        track_count = 0
        if disc_present and result.get('stderr'):
            # Parse cdparanoia output for track count
            for line in result['stderr'].split('\n'):
                if 'tracks:' in line.lower():
                    try:
                        track_count = int(line.split(':')[1].strip().split()[0])
                    except:
                        pass
        
        return jsonify({
            'success': True,
            'disc_present': disc_present,
            'track_count': track_count,
            'message': 'Disc detected' if disc_present else 'No disc in drive'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cd/metadata', methods=['POST'])
def save_cd_metadata():
    """Save edited CD metadata"""
    global cd_edited_metadata
    try:
        data = request.get_json()
        disc_id = data.get('disc_id')
        
        if not disc_id:
            return jsonify({'success': False, 'error': 'disc_id required'}), 400
        
        # Store edited metadata
        cd_edited_metadata[disc_id] = {
            'artist': data.get('artist', ''),
            'album': data.get('album', ''),
            'year': data.get('year', ''),
            'genre': data.get('genre', ''),
            'tracks': data.get('tracks', [])
        }
        
        print(f"DEBUG: Saved edited metadata for disc {disc_id}: {cd_edited_metadata[disc_id]}", flush=True)
        
        return jsonify({'success': True, 'message': 'Metadata saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cd/info')
def get_cd_info():
    """Get CD metadata from configured provider"""
    global cd_metadata_cache
    import time
    
    print(f"DEBUG: get_cd_info() called", flush=True)
    try:
        # Get disc ID using python discid library for proper MusicBrainz disc ID
        import discid
        try:
            disc = discid.read('/dev/cdrom')
            disc_id = disc.id  # MusicBrainz disc ID
            freedb_id = disc.freedb_id  # FreeDB disc ID for cache key
            track_count = len(disc.tracks)
            print(f"DEBUG: Got disc ID: {disc_id}, FreeDB ID: {freedb_id}, Tracks: {track_count}", flush=True)
        except discid.DiscError as e:
            print(f"DEBUG: DiscError: {str(e)}", flush=True)
            # Clear cache if no disc
            cd_metadata_cache = {'disc_id': None, 'mb_disc_id': None, 'metadata': None, 'timestamp': 0}
            return jsonify({
                'success': False,
                'error': f'Could not read disc ID: {str(e)}. Is a CD in the drive?'
            }), 400
        except Exception as e:
            print(f"DEBUG: Unexpected error reading disc: {str(e)}", flush=True)
            # Clear cache if no disc
            cd_metadata_cache = {'disc_id': None, 'mb_disc_id': None, 'metadata': None, 'timestamp': 0}
            return jsonify({
                'success': False,
                'error': f'Error reading disc: {str(e)}'
            }), 400
        
        # Check cache - if same disc and cached within last 60 seconds, return cached data
        current_time = time.time()
        if (cd_metadata_cache['disc_id'] == freedb_id and 
            cd_metadata_cache['metadata'] is not None and 
            (current_time - cd_metadata_cache['timestamp']) < 60):
            print(f"DEBUG: Returning cached metadata for disc {freedb_id}", flush=True)
            cached_data = cd_metadata_cache['metadata'].copy()
            
            # Override with edited metadata if it exists (check both disc IDs)
            mb_disc_id = cd_metadata_cache.get('mb_disc_id', disc_id)
            if mb_disc_id in cd_edited_metadata or freedb_id in cd_edited_metadata:
                edited = cd_edited_metadata.get(mb_disc_id) or cd_edited_metadata.get(freedb_id)
                print(f"DEBUG: Applying edited metadata: {edited}", flush=True)
                cached_data['artist'] = edited.get('artist', cached_data['artist'])
                cached_data['album'] = edited.get('album', cached_data['album'])
                cached_data['year'] = edited.get('year', cached_data['year'])
                cached_data['genre'] = edited.get('genre', cached_data['genre'])
                if edited.get('tracks'):
                    cached_data['tracks'] = edited['tracks']
                print(f"DEBUG: Returning cached data with edits: genre={cached_data['genre']}", flush=True)
            
            return jsonify(cached_data)
        
        # Query MusicBrainz API
        import requests
        mb_url = f'https://musicbrainz.org/ws/2/discid/{disc_id}?inc=artist-credits+recordings'
        headers = {
            'User-Agent': 'Maestro-MPD/1.0 (https://github.com/yourusername/maestro)',
            'Accept': 'application/json'
        }
        
        print(f"DEBUG: Querying MusicBrainz with URL: {mb_url}", flush=True)
        response = requests.get(mb_url, headers=headers, timeout=10)
        print(f"DEBUG: MusicBrainz response status: {response.status_code}", flush=True)
        
        if response.status_code == 200:
            data = response.json()
            if 'releases' in data and len(data['releases']) > 0:
                release = data['releases'][0]
                release_id = release.get('id', '')
                artist = release.get('artist-credit', [{}])[0].get('name', 'Unknown Artist')
                album = release.get('title', 'Unknown Album')
                year = release.get('date', '')[:4] if release.get('date') else ''
                
                # Fetch album art from Cover Art Archive
                album_art_url = None
                if release_id:
                    try:
                        art_url = f'https://coverartarchive.org/release/{release_id}'
                        art_response = requests.get(art_url, headers=headers, timeout=5)
                        if art_response.status_code == 200:
                            art_data = art_response.json()
                            if 'images' in art_data and len(art_data['images']) > 0:
                                # Get the front cover or first image
                                for image in art_data['images']:
                                    if image.get('front', False):
                                        album_art_url = image.get('thumbnails', {}).get('large', image.get('image'))
                                        break
                                if not album_art_url and art_data['images']:
                                    album_art_url = art_data['images'][0].get('thumbnails', {}).get('large', art_data['images'][0].get('image'))
                    except:
                        pass  # Album art is optional
                
                # If no MusicBrainz album art, try Last.fm as fallback
                if not album_art_url:
                    try:
                        from pathlib import Path
                        settings_file = Path.home() / 'maestro' / 'settings.json'
                        if settings_file.exists():
                            with open(settings_file) as f:
                                settings = json.load(f)
                                lastfm_api_key = settings.get('lastfm_api_key', '')
                                
                                if lastfm_api_key:
                                    lastfm_url = 'http://ws.audioscrobbler.com/2.0/'
                                    lastfm_params = {
                                        'method': 'album.getinfo',
                                        'api_key': lastfm_api_key,
                                        'artist': artist,
                                        'album': album,
                                        'format': 'json'
                                    }
                                    lfm_response = requests.get(lastfm_url, params=lastfm_params, timeout=5)
                                    if lfm_response.status_code == 200:
                                        lfm_data = lfm_response.json()
                                        if 'album' in lfm_data and 'image' in lfm_data['album']:
                                            # Get largest image
                                            for img in reversed(lfm_data['album']['image']):
                                                if img.get('#text'):
                                                    album_art_url = img['#text']
                                                    break
                    except Exception as e:
                        print(f"Last.fm fallback failed: {e}", flush=True)
                        pass
                
                # Get track list
                tracks = []
                if 'media' in release and len(release['media']) > 0:
                    for track in release['media'][0].get('tracks', []):
                        tracks.append({
                            'number': track.get('position', 0),
                            'title': track.get('title', f"Track {track.get('position', 0)}")
                        })
                
                metadata = {
                    'success': True,
                    'artist': artist,
                    'album': album,
                    'year': year,
                    'genre': '',  # MusicBrainz doesn't reliably provide genre in discid lookup
                    'tracks': tracks,
                    'disc_id': disc_id,
                    'album_art_url': album_art_url
                }
                
                # Cache the result
                cd_metadata_cache['disc_id'] = freedb_id
                cd_metadata_cache['mb_disc_id'] = disc_id
                cd_metadata_cache['metadata'] = metadata
                cd_metadata_cache['timestamp'] = time.time()
                print(f"DEBUG: Cached metadata for FreeDB: {freedb_id}, MB: {disc_id}", flush=True)
                
                return jsonify(metadata)
        
        print(f"DEBUG: First MusicBrainz query failed, trying fallback. Status: {response.status_code if 'response' in locals() else 'no response'}", flush=True)
        
        # Fallback: Use abcde-musicbrainz-tool to get proper MusicBrainz disc ID format
        try:
            # Get the full MusicBrainz disc ID
            print(f"DEBUG: Trying abcde-musicbrainz-tool fallback", flush=True)
            mb_result = run_command(['/usr/bin/abcde-musicbrainz-tool', '--command', 'id', '--device', '/dev/cdrom'])
            print(f"DEBUG: Tool result: {mb_result}", flush=True)
            if mb_result.get('returncode') == 0 and mb_result.get('stdout'):
                mb_disc_id = mb_result['stdout'].strip().split()[0]  # First field is the disc ID
                print(f"DEBUG: Got MB disc ID: {mb_disc_id}", flush=True)
                if mb_disc_id and mb_disc_id != disc_id:
                    # Try MusicBrainz with the proper disc ID format
                    mb_url2 = f'https://musicbrainz.org/ws/2/discid/{mb_disc_id}?inc=artist-credits+recordings'
                    print(f"DEBUG: Querying {mb_url2}", flush=True)
                    response2 = requests.get(mb_url2, headers=headers, timeout=10)
                    print(f"DEBUG: Response status: {response2.status_code}", flush=True)
                    if response2.status_code == 200:
                        data2 = response2.json()
                        print(f"DEBUG: Got releases: {len(data2.get('releases', []))}", flush=True)
                        if 'releases' in data2 and len(data2['releases']) > 0:
                            release = data2['releases'][0]
                            release_id = release.get('id', '')
                            artist = release.get('artist-credit', [{}])[0].get('name', 'Unknown Artist')
                            album = release.get('title', 'Unknown Album')
                            year = release.get('date', '')[:4] if release.get('date') else ''
                            
                            # Try to get album art
                            album_art_url = None
                            if release_id:
                                try:
                                    art_url = f'https://coverartarchive.org/release/{release_id}'
                                    art_response = requests.get(art_url, headers=headers, timeout=5)
                                    if art_response.status_code == 200:
                                        art_data = art_response.json()
                                        if 'images' in art_data and len(art_data['images']) > 0:
                                            for image in art_data['images']:
                                                if image.get('front', False):
                                                    album_art_url = image.get('thumbnails', {}).get('large', image.get('image'))
                                                    break
                                            if not album_art_url and art_data['images']:
                                                album_art_url = art_data['images'][0].get('thumbnails', {}).get('large', art_data['images'][0].get('image'))
                                except:
                                    pass
                            
                            # If no MusicBrainz album art, try Last.fm
                            if not album_art_url:
                                try:
                                    # Load Last.fm API key from settings
                                    settings_file = Path.home() / 'maestro' / 'web' / 'settings.json'
                                    if settings_file.exists():
                                        with open(settings_file) as f:
                                            settings = json.load(f)
                                            lastfm_api_key = settings.get('lastfm_api_key', '')
                                            
                                            if lastfm_api_key:
                                                print(f"DEBUG: Trying Last.fm for album art", flush=True)
                                                lastfm_params = {
                                                    'method': 'album.getinfo',
                                                    'api_key': lastfm_api_key,
                                                    'artist': artist,
                                                    'album': album,
                                                    'format': 'json'
                                                }
                                                lastfm_response = requests.get('https://ws.audioscrobbler.com/2.0/', 
                                                                              params=lastfm_params, timeout=5)
                                                if lastfm_response.status_code == 200:
                                                    lastfm_data = lastfm_response.json()
                                                    if 'album' in lastfm_data and 'image' in lastfm_data['album']:
                                                        # Get the largest image available
                                                        for size_pref in ['extralarge', 'large', 'medium']:
                                                            for img in lastfm_data['album']['image']:
                                                                if img.get('size') == size_pref and img.get('#text'):
                                                                    album_art_url = img['#text']
                                                                    print(f"DEBUG: Found Last.fm {size_pref} image", flush=True)
                                                                    break
                                                            if album_art_url:
                                                                break
                                except Exception as e:
                                    print(f"DEBUG: Last.fm lookup failed: {e}", flush=True)
                            
                            tracks = []
                            if 'media' in release and len(release['media']) > 0:
                                for track in release['media'][0].get('tracks', []):
                                    tracks.append({
                                        'number': track.get('position', 0),
                                        'title': track.get('title', f"Track {track.get('position', 0)}")
                                    })
                            
                            metadata = {
                                'success': True,
                                'artist': artist,
                                'album': album,
                                'year': year,
                                'genre': '',
                                'tracks': tracks,
                                'disc_id': mb_disc_id,
                                'album_art_url': album_art_url
                            }
                            
                            # Cache the result
                            cd_metadata_cache['disc_id'] = disc_id
                            cd_metadata_cache['mb_disc_id'] = mb_disc_id
                            cd_metadata_cache['metadata'] = metadata
                            cd_metadata_cache['timestamp'] = time.time()
                            
                            # Override with edited metadata if it exists (check both disc IDs)
                            if mb_disc_id in cd_edited_metadata or disc_id in cd_edited_metadata:
                                edited = cd_edited_metadata.get(mb_disc_id) or cd_edited_metadata.get(disc_id)
                                metadata['artist'] = edited.get('artist', metadata['artist'])
                                metadata['album'] = edited.get('album', metadata['album'])
                                metadata['year'] = edited.get('year', metadata['year'])
                                metadata['genre'] = edited.get('genre', metadata['genre'])
                                if edited.get('tracks'):
                                    metadata['tracks'] = edited['tracks']
                            
                            return jsonify(metadata)
        except Exception as ex:
            print(f"DEBUG: Fallback failed with error: {ex}", flush=True)
            import traceback
            traceback.print_exc()
        
        # Final fallback: no metadata found
        print(f"DEBUG: Using final fallback - no metadata found", flush=True)
        return jsonify({
            'success': True,
            'artist': 'Unknown Artist',
            'album': 'Unknown Album',
            'year': '',
            'genre': '',
            'tracks': [{'number': i+1, 'title': f'Track {i+1}'} for i in range(track_count)],
            'disc_id': disc_id,
            'message': 'No metadata found'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cd/rip', methods=['POST'])
def rip_cd():
    """Start CD ripping process"""
    global rip_status
    
    if rip_status['active']:
        return jsonify({'success': False, 'error': 'Ripping already in progress'}), 400
    
    try:
        data = request.get_json() or {}
        output_format = data.get('format', 'flac')
        output_dir = data.get('output_dir', '/media/music/ripped')
        album_art_opts = data.get('album_art', {})
        
        # Validate output directory
        if not output_dir.startswith('/media/music/'):
            return jsonify({'success': False, 'error': 'Output directory must be under /media/music/'}), 400
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Load settings for quality and options
        cd_settings = load_cd_settings()
        
        # Get disc ID to check for edited metadata
        disc_id = None
        try:
            result = run_command(['/usr/bin/cd-discid', '/dev/cdrom'])
            if result['returncode'] == 0:
                disc_info = result['stdout'].strip().split()
                if len(disc_info) >= 1:
                    disc_id = disc_info[0]
        except:
            pass
        
        # Start ripping in background thread
        def rip_thread():
            global rip_status, cd_edited_metadata, cd_metadata_cache
            rip_status['active'] = True
            rip_status['status'] = 'Starting rip...'
            rip_status['progress'] = 0
            rip_status['error'] = None
            
            try:
                # Pre-download album art if enabled
                # (Cache should already be populated by UI calling /api/cd/info before rip)
                save_art_file = album_art_opts.get('save_file', True)
                # Use MusicBrainz disc ID from cache instead of FreeDB ID
                mb_disc_id = cd_metadata_cache.get('mb_disc_id')
                if save_art_file and mb_disc_id and cd_metadata_cache.get('metadata'):
                    try:
                        # Get metadata from cache (prefer edited if available, fallback to cache)
                        cache_metadata = cd_metadata_cache.get('metadata', {})
                        edited_metadata = cd_edited_metadata.get(mb_disc_id, {})
                        
                        artist = edited_metadata.get('artist') or cache_metadata.get('artist', 'Unknown Artist')
                        album = edited_metadata.get('album') or cache_metadata.get('album', 'Unknown Album')
                        year = edited_metadata.get('year') or cache_metadata.get('year', '')
                        
                        # Get album art URL from cache
                        if cache_metadata.get('album_art_url'):
                            album_art_url = cache_metadata['album_art_url']
                            
                            if album_art_url:
                                # Construct album folder path (same format as abcde will use)
                                artist_safe = artist.replace('/', '_').replace(' ', '_')
                                album_safe = album.replace('/', '_').replace(' ', '_')
                                if year:
                                    dir_name = f"{artist_safe} - {album_safe} ({year})"
                                else:
                                    dir_name = f"{artist_safe} - {album_safe}"
                                album_folder = os.path.join(output_dir, dir_name)
                                
                                # Create album folder
                                os.makedirs(album_folder, exist_ok=True)
                                print(f"DEBUG: Created album folder: {album_folder}", flush=True)
                                
                                # Download album art
                                import requests
                                print(f"DEBUG: Pre-downloading album art from {album_art_url}", flush=True)
                                art_response = requests.get(album_art_url, timeout=10)
                                if art_response.status_code == 200:
                                    cover_path = os.path.join(album_folder, 'cover.jpg')
                                    with open(cover_path, 'wb') as f:
                                        f.write(art_response.content)
                                    print(f"DEBUG: Album art saved to {cover_path}", flush=True)
                                else:
                                    print(f"DEBUG: Failed to download album art, status: {art_response.status_code}", flush=True)
                    except Exception as art_error:
                        print(f"DEBUG: Error pre-downloading album art: {art_error}", flush=True)
                
                # Create temporary abcde config
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
                    f.write(f'''# ABCDE configuration for Maestro\n''')
                    f.write(f'''CDROMREADERSYNTAX=cdparanoia\n''')
                    f.write(f'''CDPARANOIA=cdparanoia\n''')
                    f.write(f'''OUTPUTDIR="{output_dir}"\n''')
                    f.write(f'''OUTPUTTYPE="{output_format}"\n''')
                    f.write(f'''OUTPUTFORMAT='${{ARTISTFILE}} - ${{ALBUMFILE}} (${{CDYEAR}})/${{TRACKNUM}} - ${{TRACKFILE}}'\n''')
                    f.write(f'''VAOUTPUTFORMAT='Various Artists - ${{ALBUMFILE}} (${{CDYEAR}})/${{TRACKNUM}} - ${{ARTISTFILE}} - ${{TRACKFILE}}'\n''')
                    f.write(f'''CDDBMETHOD=musicbrainz\n''')
                    f.write(f'''MAXPROCS={cd_settings.get('max_processes', 4)}\n''')
                    
                    # Build ACTIONS based on album art preferences
                    embed_art = album_art_opts.get('embed', True)
                    save_art = album_art_opts.get('save_file', True)
                    
                    actions = 'cddb,read,encode,tag'
                    # Add getalbumart action if either embed or save is enabled
                    if embed_art or save_art:
                        actions += ',getalbumart'
                    if embed_art:
                        actions += ',embedalbumart'
                    actions += ',move,clean'
                    f.write(f'''ACTIONS={actions}\n''')
                    
                    # Album art settings
                    if embed_art or save_art:
                        f.write(f'''# Album art settings\n''')
                        f.write(f'''ALBUMARTFILE="cover.jpg"\n''')
                        f.write(f'''ALBUMARTTYPE="JPEG"\n''')
                        # COVERART tells abcde to keep the cover art file
                        f.write(f'''COVERART={1 if save_art else 0}\n''')
                        f.write(f'''COVERARTWGET=y\n''')
                    
                    # Format-specific settings
                    if output_format == 'flac':
                        quality = cd_settings.get('quality', 'high')
                        compression = '8' if quality == 'high' else '5' if quality == 'medium' else '3'
                        f.write(f'''FLACOPTS='-{compression}'\n''')
                    elif output_format == 'mp3':
                        quality = cd_settings.get('quality', 'high')
                        bitrate = '320' if quality == 'high' else '192' if quality == 'medium' else '128'
                        f.write(f'''LAMEOPTS='-b {bitrate}'\n''')
                    
                    config_file = f.name
                
                # If metadata was edited, create a custom CDDB file
                cddb_file = None
                if disc_id and disc_id in cd_edited_metadata:
                    edited = cd_edited_metadata[disc_id]
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.cddb', delete=False) as cddb:
                        # Write CDDB format file
                        cddb.write(f"# xmcd\n")
                        cddb.write(f"#\n")
                        cddb.write(f"# Track frame offsets:\n")
                        cddb.write(f"#\n")
                        cddb.write(f"# Disc length: 0 seconds\n")
                        cddb.write(f"#\n")
                        cddb.write(f"DISCID={disc_id}\n")
                        cddb.write(f"DTITLE={edited.get('artist', 'Unknown')} / {edited.get('album', 'Unknown')}\n")
                        cddb.write(f"DYEAR={edited.get('year', '')}\n")
                        cddb.write(f"DGENRE={edited.get('genre', '')}\n")
                        
                        # Write track titles
                        for i, track in enumerate(edited.get('tracks', [])):
                            cddb.write(f"TTITLE{i}={track.get('title', f'Track {i+1}')}\n")
                        
                        cddb.write(f"EXTD=\n")
                        cddb.write(f"PLAYORDER=\n")
                        cddb_file = cddb.name
                    
                    # Copy CDDB file to abcde working directory for it to use
                    import shutil
                    cddb_dest = os.path.join(output_dir, f'{disc_id}.cddb')
                    shutil.copy(cddb_file, cddb_dest)
                    print(f"DEBUG: Created custom CDDB file at {cddb_dest}", flush=True)
                
                # Execute abcde
                rip_status['status'] = 'Ripping tracks...'
                
                # Log the config file contents for debugging
                with open(config_file, 'r') as f:
                    print(f"DEBUG: abcde config:\n{f.read()}", flush=True)
                
                # Set up environment with proper PATH
                env = os.environ.copy()
                env['PATH'] = '/usr/local/bin:/usr/bin:/bin'
                env['HOME'] = str(Path.home())
                
                process = subprocess.Popen(
                    ['/usr/bin/abcde', '-c', config_file, '-N'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    cwd=output_dir,
                    env=env
                )
                
                # Capture all output for debugging
                all_output = []
                
                # Monitor output for progress
                for line in iter(process.stdout.readline, ''):
                    all_output.append(line)
                    print(f"ABCDE: {line.rstrip()}", flush=True)
                    
                    if 'track' in line.lower():
                        # Try to extract track number
                        import re
                        match = re.search(r'track[\s:]*?(\d+)', line, re.IGNORECASE)
                        if match:
                            track_num = int(match.group(1))
                            rip_status['current_track'] = track_num
                            rip_status['status'] = f'Ripping track {track_num}...'
                            # Estimate progress (rough)
                            if rip_status['total_tracks'] > 0:
                                rip_status['progress'] = int((track_num / rip_status['total_tracks']) * 100)
                
                process.wait()
                
                # Clean up config file
                os.unlink(config_file)
                
                if process.returncode == 0:
                    rip_status['status'] = 'Rip completed successfully'
                    rip_status['progress'] = 100
                    
                    # Download and save album art if enabled
                    album_art_settings = album_art_opts if 'album_art_opts' in locals() else {}
                    save_art_file = album_art_settings.get('save_file', False)
                    
                    if save_art_file and disc_id:
                        try:
                            # Get metadata to find artist/album and album art URL
                            metadata = cd_edited_metadata.get(disc_id, {})
                            artist = metadata.get('artist', 'Unknown Artist')
                            album = metadata.get('album', 'Unknown Album')
                            
                            # Try to get album art URL from cache
                            if cd_metadata_cache.get('disc_id') == disc_id and cd_metadata_cache.get('metadata'):
                                album_art_url = cd_metadata_cache['metadata'].get('album_art_url')
                                
                                if album_art_url:
                                    import requests
                                    print(f"DEBUG: Downloading album art from {album_art_url}", flush=True)
                                    
                                    # Construct output directory
                                    output_path = os.path.join(output_dir, f"{artist.replace('/', '_')} - {album.replace('/', '_')}")
                                    if os.path.exists(output_path):
                                        cover_path = os.path.join(output_path, 'cover.jpg')
                                        
                                        # Download album art
                                        art_response = requests.get(album_art_url, timeout=10)
                                        if art_response.status_code == 200:
                                            with open(cover_path, 'wb') as f:
                                                f.write(art_response.content)
                                            print(f"DEBUG: Album art saved to {cover_path}", flush=True)
                                        else:
                                            print(f"DEBUG: Failed to download album art, status: {art_response.status_code}", flush=True)
                                    else:
                                        print(f"DEBUG: Output directory not found: {output_path}", flush=True)
                                else:
                                    print(f"DEBUG: No album art URL available", flush=True)
                        except Exception as art_error:
                            print(f"DEBUG: Error downloading album art: {art_error}", flush=True)
                    
                    # Update MPD database
                    run_command(['/usr/bin/mpc', 'update'])
                    
                    # Auto-eject if enabled
                    if cd_settings.get('auto_eject', True):
                        run_command(['/usr/bin/eject', '/dev/cdrom'])
                else:
                    rip_status['status'] = 'Rip failed'
                    error_msg = '\n'.join(all_output[-10:]) if all_output else f'exit code {process.returncode}'
                    rip_status['error'] = f'abcde failed: {error_msg}'
                    print(f"DEBUG: abcde failed with code {process.returncode}", flush=True)
                    print(f"DEBUG: Last output lines:\n{error_msg}", flush=True)
                    
            except Exception as e:
                rip_status['status'] = 'Error'
                rip_status['error'] = str(e)
            finally:
                rip_status['active'] = False
        
        # Get track count for progress tracking
        try:
            result = run_command(['/usr/bin/cd-discid', '/dev/cdrom'])
            if result['returncode'] == 0:
                disc_info = result['stdout'].strip().split()
                rip_status['total_tracks'] = len(disc_info) - 2
        except:
            rip_status['total_tracks'] = 0
        
        # Start thread
        import threading
        thread = threading.Thread(target=rip_thread, daemon=True)
        thread.start()
        
        return jsonify({'success': True, 'message': 'Rip started'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cd/rip-status')
def get_rip_status():
    """Get current ripping progress"""
    return jsonify({
        'success': True,
        'active': rip_status['active'],
        'progress': rip_status['progress'],
        'current_track': rip_status['current_track'],
        'total_tracks': rip_status['total_tracks'],
        'status': rip_status['status'],
        'error': rip_status['error']
    })

@app.route('/api/cd/eject', methods=['POST'])
def eject_cd():
    """Eject the CD"""
    try:
        result = run_command(['eject', '/dev/cdrom'], require_sudo=True)
        if result['success']:
            return jsonify({'success': True, 'message': 'CD ejected'})
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Eject failed')}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cd/config', methods=['GET'])
def get_abcde_config():
    """Get abcde.conf contents"""
    try:
        # Try user config first, then system config
        config_paths = [
            Path.home() / '.abcde.conf',
            Path('/etc/abcde.conf')
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = f.read()
                return jsonify({'success': True, 'config': config, 'path': str(config_path)})
        
        # No config found, return empty/default
        return jsonify({'success': True, 'config': '# No abcde.conf found\n# Settings will use defaults\n', 'path': None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cd/config', methods=['POST'])
def save_abcde_config():
    """Save abcde.conf"""
    try:
        config = request.json.get('config', '')
        
        # Save to user's home directory
        config_path = Path.home() / '.abcde.conf'
        with open(config_path, 'w') as f:
            f.write(config)
        
        return jsonify({'success': True, 'message': 'Configuration saved', 'path': str(config_path)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cd/config/reset', methods=['POST'])
def reset_abcde_config():
    """Reset abcde.conf to defaults"""
    try:
        config_path = Path.home() / '.abcde.conf'
        
        # Remove user config if it exists
        if config_path.exists():
            config_path.unlink()
        
        return jsonify({'success': True, 'message': 'Configuration reset to defaults'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# FILE BROWSER API
# ============================================================================

@app.route('/api/files/browse')
def browse_files():
    """Browse music directory"""
    try:
        path = request.args.get('path', '/media/music/ripped')
        
        # Security: Only allow browsing within music directories
        allowed_paths = ['/var/lib/mpd/music', '/mnt/music', '/media/music']
        if not any(path.startswith(allowed) for allowed in allowed_paths):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        items = []
        for entry in os.scandir(path):
            item = {
                'name': entry.name,
                'path': entry.path,
                'is_dir': entry.is_dir(),
                'size': entry.stat().st_size if entry.is_file() else 0,
                'modified': entry.stat().st_mtime
            }
            items.append(item)
        
        # Sort: directories first, then files alphabetically
        items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        
        return jsonify({
            'success': True,
            'path': path,
            'parent': os.path.dirname(path) if path not in ['/mnt/music', '/var/lib/mpd/music', '/media/music/ripped'] else None,
            'items': items
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/play', methods=['POST'])
def play_file():
    """Add file to MPD playlist and play"""
    try:
        data = request.json
        path = data.get('path')
        
        # Add to MPD playlist
        result = run_command(['/usr/bin/mpc', 'add', path])
        
        if not result['success']:
            return jsonify({'success': False, 'error': f"Failed to add file: {result.get('stderr', 'Unknown error')}"}), 500
        
        # Play the newly added song
        result = run_command(['/usr/bin/mpc', 'play'])
        if result['success']:
            return jsonify({'success': True, 'message': 'Added to playlist and playing'})
        else:
            return jsonify({'success': False, 'error': 'Failed to start playback'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/delete', methods=['POST'])
def delete_file():
    """Delete file or directory"""
    try:
        data = request.json
        path = data.get('path')
        
        # Security: Only allow deleting within music directories
        allowed_paths = ['/var/lib/mpd/music', '/mnt/music', '/media/music']
        if not any(path.startswith(allowed) for allowed in allowed_paths):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        if os.path.isdir(path):
            result = run_command(['rm', '-rf', path], require_sudo=True)
        else:
            result = run_command(['rm', '-f', path], require_sudo=True)
        
        if result['success']:
            return jsonify({'success': True, 'message': 'Deleted successfully'})
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Delete failed')}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/update-mpd', methods=['POST'])
def update_mpd_library():
    """Update MPD library database"""
    try:
        result = run_command(['/usr/bin/mpc', 'update'])
        if result['success']:
            return jsonify({'success': True, 'message': 'MPD library update started'})
        else:
            return jsonify({'success': False, 'error': 'Update failed'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/move', methods=['POST'])
def move_file():
    """Move or rename file/directory"""
    try:
        data = request.json
        source = data.get('source')
        destination = data.get('destination')
        
        # Security checks
        allowed_paths = ['/var/lib/mpd/music', '/mnt/music']
        if not any(source.startswith(allowed) for allowed in allowed_paths) or \
           not any(destination.startswith(allowed) for allowed in allowed_paths):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        result = run_command(['mv', source, destination], require_sudo=True)
        
        if result['success']:
            # Update MPD database
            run_command(['/usr/bin/mpc', 'update'])
            return jsonify({'success': True, 'message': 'File moved successfully'})
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Move failed')}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/mkdir', methods=['POST'])
def make_directory():
    """Create new directory"""
    try:
        data = request.json
        path = data.get('path')
        name = data.get('name')
        
        new_dir = os.path.join(path, name)
        
        # Security check
        allowed_paths = ['/var/lib/mpd/music', '/mnt/music']
        if not any(new_dir.startswith(allowed) for allowed in allowed_paths):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        os.makedirs(new_dir, exist_ok=True)
        return jsonify({'success': True, 'message': 'Directory created'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# ============================================================================
# HTTP STREAMING CONFIGURATION
# ============================================================================

@app.route('/api/streaming/config', methods=['GET'])
def get_streaming_config():
    """Get current HTTP streaming configuration from mpd.conf"""
    try:
        import re
        
        # Read mpd.conf
        result = run_command(['cat', '/etc/mpd.conf'], require_sudo=True)
        if not result['success']:
            return jsonify({'status': 'error', 'message': 'Failed to read mpd.conf'}), 500
        
        config_text = result['stdout']
        
        # Parse httpd audio_output block
        httpd_pattern = r'audio_output\s*\{[^}]*type\s+"httpd"[^}]*\}'
        httpd_match = re.search(httpd_pattern, config_text, re.DOTALL)
        
        if not httpd_match:
            # No HTTP streaming configured
            return jsonify({
                'status': 'success',
                'enabled': False,
                'config': {
                    'name': 'Maestro HTTP Stream',
                    'port': '8000',
                    'encoder': '',  # Empty = lossless WAVE
                    'bitrate': '',
                    'format': '',
                    'max_clients': '0',
                    'bind_to_address': '0.0.0.0'
                }
            })
        
        httpd_block = httpd_match.group(0)
        
        # Extract individual settings
        def extract_value(key, default=''):
            pattern = rf'{key}\s+"([^"]*)"'
            match = re.search(pattern, httpd_block)
            return match.group(1) if match else default
        
        config = {
            'name': extract_value('name', 'Maestro HTTP Stream'),
            'port': extract_value('port', '8000'),
            'encoder': extract_value('encoder', ''),  # Empty = lossless WAVE
            'bitrate': extract_value('bitrate', ''),
            'format': extract_value('format', ''),
            'max_clients': extract_value('max_clients', '0'),
            'bind_to_address': extract_value('bind_to_address', '0.0.0.0')
        }
        
        # Check if the entire block is commented (look for # before the audio_output keyword)
        # Get the text around the match to check for comments
        start_pos = httpd_match.start()
        # Look back up to 50 characters to find the start of the line
        line_start = max(0, start_pos - 50)
        prefix_text = config_text[line_start:start_pos]
        
        # Check if there's a # before audio_output on the same line
        last_newline = prefix_text.rfind('\n')
        if last_newline != -1:
            line_prefix = prefix_text[last_newline+1:].strip()
        else:
            line_prefix = prefix_text.strip()
        
        is_commented = line_prefix.startswith('#')
        
        return jsonify({
            'status': 'success',
            'enabled': not is_commented,
            'config': config
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/streaming/config', methods=['POST'])
def update_streaming_config():
    """Update HTTP streaming configuration in mpd.conf"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        # Config is sent flat in the data, not nested
        config = data
        
        # Read current mpd.conf
        result = run_command(['cat', '/etc/mpd.conf'], require_sudo=True)
        if not result['success']:
            return jsonify({'status': 'error', 'message': 'Failed to read mpd.conf'}), 500
        
        config_text = result['stdout']
        
        # Build HTTP streaming block based on encoder setting
        name = config.get('name', 'Maestro HTTP Stream')
        port = config.get('port', '8000')
        encoder = config.get('encoder', '').strip()
        bitrate = config.get('bitrate', '').strip()
        format_val = config.get('format', '').strip()
        max_clients = config.get('max_clients', '0')
        bind_addr = config.get('bind_to_address', '0.0.0.0')
        
        # Build config lines - only include fields that have values
        config_lines = [
            'audio_output {',
            f'    type        "httpd"',
            f'    name        "{name}"',
            f'    port        "{port}"',
        ]
        
        # Optional fields - only add if they have values
        if encoder:
            config_lines.append(f'    encoder     "{encoder}"')
        if bitrate:
            config_lines.append(f'    bitrate     "{bitrate}"')
        if format_val:
            config_lines.append(f'    format      "{format_val}"')
        
        config_lines.extend([
            f'    max_clients "{max_clients}"',
            f'    bind_to_address "{bind_addr}"',
            f'    mixer_type  "software"',
            '}'
        ])
        
        httpd_block = '\n'.join(config_lines)
        
        # Remove existing httpd audio_output block (commented or not)
        import re
        # Remove commented blocks
        config_text = re.sub(r'#\s*audio_output\s*\{[^}]*type\s+"httpd"[^}]*\}', '', config_text, flags=re.DOTALL)
        # Remove active blocks
        config_text = re.sub(r'audio_output\s*\{[^}]*type\s+"httpd"[^}]*\}', '', config_text, flags=re.DOTALL)
        
        # Add new block at the end if enabled, or commented if disabled
        if enabled:
            config_text += '\n\n# HTTP Streaming Output (Multi-room playback)\n' + httpd_block + '\n'
        else:
            # Add as commented block for reference
            commented_block = '\n'.join(['#' + line if line.strip() else line for line in httpd_block.split('\n')])
            config_text += '\n\n# HTTP Streaming Output (Multi-room playback) - DISABLED\n' + commented_block + '\n'
        
        # Write back to mpd.conf
        write_result = run_command(
            f'echo {repr(config_text)} | sudo tee /etc/mpd.conf > /dev/null',
            require_sudo=False
        )
        
        if not write_result['success']:
            return jsonify({'success': False, 'error': 'Failed to write mpd.conf'}), 500
        
        # Restart MPD
        restart_result = run_command(['systemctl', 'restart', 'mpd'], require_sudo=True)
        
        if restart_result['success']:
            return jsonify({
                'success': True,
                'message': f'HTTP streaming {"enabled" if enabled else "disabled"} and MPD restarted',
                'stream_url': f'http://{socket.gethostname()}:{config.get("port", "8000")}' if enabled else None
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Config updated but MPD restart failed'
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Maestro Admin API Starting")
    print("=" * 60)
    print(f"Running on: http://0.0.0.0:5004")
    print(f"Config directory: {CONFIG_DIR}")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5004, debug=True, allow_unsafe_werkzeug=True)
