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
        return {'success': False, 'error': 'Command timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

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
    """Mount a configured network share"""
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
        
        # Build mount command
        if mount['type'] == 'nfs':
            cmd = f"mount -t nfs {mount['server']}:{mount['share_path']} {mount_point}"
        elif mount['type'] == 'smb':
            creds = ""
            if mount['username']:
                creds = f"username={mount['username']},password={mount['password']}"
            cmd = f"mount -t cifs //{mount['server']}/{mount['share_path']} {mount_point}"
            if creds:
                cmd += f" -o {creds}"
        else:
            return jsonify({'status': 'error', 'message': 'Unknown mount type'}), 400
        
        # Execute mount
        result = run_command(cmd, require_sudo=True)
        
        if result['success']:
            return jsonify({'status': 'success', 'message': f"Mounted {mount['name']}"})
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
