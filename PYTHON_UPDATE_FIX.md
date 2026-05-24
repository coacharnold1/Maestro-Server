# Python System Update Recovery Guide

## Problem

After a system Python update (e.g., from Python 3.13 to Python 3.14), Maestro services may fail to start with errors like:

```
ModuleNotFoundError: No module named 'flask'
```

This happens because Python virtual environments (venvs) contain symlinks to the system Python, and when Python is updated, the old packages become incompatible with the new version.

## Quick Fix

Run the provided fix script:

```bash
cd ~/Maestro-Server
./fix-python-venv.sh
```

This script will:
1. Stop Maestro services
2. Recreate both web and admin virtual environments
3. Reinstall all Python dependencies
4. Restart the services

## Manual Fix

If you prefer to fix it manually:

```bash
# Stop services
sudo systemctl stop maestro-web.service maestro-admin.service

# Recreate web venv
cd ~/maestro/web
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r ~/maestro/requirements.txt
deactivate

# Recreate admin venv
cd ~/maestro/admin
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Restart services
sudo systemctl restart maestro-web.service maestro-admin.service
```

## Using Update Script

The update script has been enhanced to automatically detect and fix broken venvs:

```bash
cd ~/Maestro-Server
./update-maestro.sh
```

The update script will now:
- Check if venvs are functional
- Automatically recreate them if broken (e.g., after Python update)
- Install all dependencies fresh

## Prevention

### For Arch Linux Users

After system updates that include Python, always run:

```bash
cd ~/Maestro-Server
./fix-python-venv.sh
```

Or simply run the update script which includes the fix:

```bash
cd ~/Maestro-Server
./update-maestro.sh
```

### System Update Best Practices

1. **Before major system updates**: Note your current Python version
   ```bash
   python3 --version
   ```

2. **After system updates**: Check if Python was updated
   ```bash
   python3 --version
   ```

3. **If Python version changed**: Run the fix script
   ```bash
   ./fix-python-venv.sh
   ```

## Checking Service Status

After the fix, verify services are running:

```bash
sudo systemctl status maestro-web.service maestro-admin.service
```

If services are still failing, check logs:

```bash
# Web service logs
sudo journalctl -u maestro-web.service -n 50

# Admin service logs
sudo journalctl -u maestro-admin.service -n 50
```

## Why This Happens

Python virtual environments use symlinks to the system Python interpreter. When you create a venv with Python 3.13, it creates:

```
venv/bin/python3 -> /usr/bin/python3
```

And installs packages for Python 3.13 in:

```
venv/lib/python3.13/site-packages/
```

When the system updates to Python 3.14:
- The symlink now points to Python 3.14
- But packages are still in the 3.13 directory
- Python 3.14 can't find the packages → ModuleNotFoundError

## Future Updates

The installer and update scripts have been updated to automatically detect and fix this issue. If you encounter it again:

1. Try the update script first: `./update-maestro.sh`
2. If that doesn't work, use the fix script: `./fix-python-venv.sh`
3. As a last resort, use the manual fix steps above

## Related Commands

```bash
# Check Python version in venv
~/maestro/web/venv/bin/python3 --version

# Check pip health
~/maestro/web/venv/bin/pip --version

# List installed packages
~/maestro/web/venv/bin/pip list

# Force package reinstall
cd ~/maestro/web
source venv/bin/activate
pip install --force-reinstall -r ~/maestro/requirements.txt
deactivate
```

## Support

If the fix script doesn't resolve the issue:

1. Check service logs for specific errors
2. Verify Python version compatibility
3. Ensure all dependencies are available in system repositories
4. Check for disk space issues
5. Review systemd service files for path mismatches

For Arch Linux specifically, Python updates are common and you may want to create a pacman hook to automatically run the fix script after Python updates.
