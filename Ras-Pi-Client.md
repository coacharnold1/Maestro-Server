# Raspberry Pi MPV Client for Multi-Room Playback

I use the following simple client for multi-room playback.  
I use a bare Raspberry Pi running Raspbian with a nice USB DAC attached and configured.

## Setup Instructions

1. Install MPV player on the client device
2. Install the below script as a systemd service file
3. Configure HTTP streaming on the Maestro server (see below)

**Note:** If using on a Windows machine it might get more complicated, ask Claude.

## Enable HTTP Streaming on Maestro Server

You can enable HTTP streaming two ways:

### Option 1: Admin UI (Recommended)

1. Open the Maestro Admin interface at `http://your-server-ip:5004`
2. Navigate to **Audio Tweaks** page
3. In the **HTTP Streaming Configuration** section:
   - Toggle the switch to **Enable HTTP streaming**
   - Use default settings (port 8000, LAME encoder, 192kbps)
   - Or click **Show Advanced Settings** to customize
4. MPD will automatically restart with the new configuration

### Option 2: Manual Configuration

Edit `/etc/mpd.conf` and add:

```conf
audio_output {
    type        "httpd"
    name        "Maestro HTTP Stream"
    encoder     "lame"
    port        "8000"
    bitrate     "192"
    format      "44100:16:2"
    max_clients "0"
    bind_to_address "0.0.0.0"
}
```

Then restart MPD: `sudo systemctl restart mpd`

## Systemd Service File

Create `/etc/systemd/system/maestro-mpv-client.service`:

```ini
[Unit]
Description=Maestro-MPD MPV Client
After=network.target

[Service]
User=Your-Root-User
# Experiment with the commented versions for audio quality.
ExecStart=/usr/bin/mpv --no-video --audio-device=alsa/hw:1,0 http://Your-MPD-address:8000
#ExecStart=/usr/bin/mpv --no-video --no-audio-display --audio-device=alsa/hw:1,0 --demuxer-max-bytes=1MiB --demuxer-readahead-sec=5 http://Your-MPD-address:8000
#ExecStart=/usr/bin/mpv --no-video --audio-device=alsa/hw:1,0 http://Your-MPD-address:8000

Restart=always

[Install]
WantedBy=multi-user.target
```

## Installation Steps

```bash
# Copy service file to systemd directory
sudo cp maestro-mpv-client.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable maestro-mpv-client.service

# Start the service
sudo systemctl start maestro-mpv-client.service

# Check status
sudo systemctl status maestro-mpv-client.service
```

## Configuration Notes

- Replace `Your-Root-User` with your actual username
- Replace `Your-MPD-address` with the IP address or hostname of your MPD server
- Adjust `audio-device=alsa/hw:1,0` to match your DAC's ALSA device
- The default port for MPD HTTP streaming is 8000
- Experiment with the commented ExecStart lines for different audio quality/buffering options
