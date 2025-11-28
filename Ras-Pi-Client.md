#I use the following simple client for multi room playback.  
#I use a bare rasberry pi running rasbian with a nice USB DAC attached and configured. 
#Install MPV player, then install the below # script as a systemd service file. 
#HTTP streaming is already enaled in MPD.conf.   
#If using on a windows machine it might get more complicated,  ask Claude.

[Unit]
Description=Maestro-MPD MPV Client
After=network.target

[Service]
User=Your=Root-User
# Experiment with the commented versions for audio quality.
ExecStart=/usr/bin/mpv --no-video --audio-device=alsa/hw:1,0 http://Your-MPD-address:8000
#ExecStart=/usr/bin/mpv --no-video --no-audio-display --audio-device=alsa/hw:1,0 --demuxer-max-bytes=1MiB --demuxer-readahead-sec=5 http://Your-MPD-address:8000
#ExecStart=/usr/bin/mpv --no-video --audio-device=alsa/hw:1,0 http://Your-MPD-address:8000

Restart=always

[Install]
WantedBy=multi-user.target



