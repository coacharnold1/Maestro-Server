# Raspberry Pi MPV Client for Multi-Room Playback

I use the following simple client for multi-room playback.  
I use a bare Raspberry Pi running Raspbian with a nice USB DAC attached and configured. I'm pretty certain you could do this with any version raspberry pi. I'm currently on a version 3 but it should be fine with a V2 or even a zero.  as long as it can run MPV.

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
   - For **24-bit audio support**: Use FLAC encoder with 96000:24:2 format
   - Or use default settings for compatibility
   - Click **Show Advanced Settings** to customize encoder, bitrate, and format
4. MPD will automatically restart with the new configuration

### Option 2: Manual Configuration (with 24-bit support)

For **24-bit FLAC/WAV files**, edit `/etc/mpd.conf` and add:

```conf
audio_output {
    type        "httpd"
    name        "Maestro HTTP Stream"
    encoder     "flac"
    port        "8000"
    bitrate     "0"
    format      "96000:24:2"
    max_clients "0"
    bind_to_address "0.0.0.0"
    always_on   "yes"
}

# Increase buffer to handle high-bitrate 24-bit streaming
max_output_buffer_size "32768"
```

For **standard 16-bit/44.1kHz** (backward compatible):

```conf
audio_output {
    type        "httpd"
    name        "Maestro HTTP Stream"
    encoder     "lame"
    port        "8000"
    bitrate     "320"
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
ExecStart=/usr/bin/mpv --no-video --audio-device=alsa/hw:1,0 --network-timeout=60 --demuxer-max-bytes=128M http://Your-MPD-address:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Key Flags Explained:**
- `--network-timeout=60`: Waits up to 60 seconds for network responses; prevents immediate dropout on brief network hiccups
- `--demuxer-max-bytes=128M`: Maintains a 128MB buffer to handle stream discontinuities and underruns gracefully

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

## Troubleshooting

### Audio Device Underruns

**Symptom:** Logs show repeated `Audio device underrun detected` or `Device underrun detected` messages; audio stuttering or glitching.

**Cause:** The ALSA audio buffer is emptying faster than `mpv` can feed it, usually due to insufficient buffering or network delays.

**Solution:** The flags in the recommended `ExecStart` line (`--network-timeout=60 --demuxer-max-bytes=128M`) handle this. If underruns persist:
- Check your network connection stability
- Verify the ALSA device is correctly configured: `aplay -l`
- Try increasing the demuxer buffer: `--demuxer-max-bytes=256M`

### Stream Drops or Premature Termination

**Symptom:** `systemctl status` shows the service crashed, or logs show `Stream ends prematurely`.

**Cause:** The HTTP stream connection dropped due to network hiccups, timeout, or server reset.

**Solution:** The `--network-timeout=60` and `--demuxer-max-bytes=128M` flags provide resilience. Ensure:
- `Restart=always` is set in the service file (auto-recovery on crashes)
- Your network is stable
- The MPD server's HTTP stream is configured correctly (see "Enable HTTP Streaming on Maestro Server" section above)

### Monitor Service Status

Check the live journal to diagnose ongoing issues:

```bash
sudo journalctl -u maestro-mpv-client.service -f
```

This shows real-time logs as the service runs, helping you spot network, audio device, or stream issues.
