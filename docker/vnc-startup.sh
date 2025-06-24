#!/bin/bash
# Start the TightVNC server

# Clean up any existing sessions
/usr/bin/vncserver -kill :1 >/dev/null 2>&1 || true
rm -rf /tmp/.X1* >/dev/null 2>&1 || true

# Configure VNC session
mkdir -p $HOME/.vnc

# Create Xauthority
touch $HOME/.Xauthority

# Start VNC server
echo "Starting VNC server with resolution $VNC_RESOLUTION and color depth $VNC_DEPTH"
/usr/bin/vncserver :1 -geometry ${VNC_RESOLUTION:-1280x800} -depth ${VNC_DEPTH:-24} -localhost no -SecurityTypes VncAuth -PasswordFile $HOME/.vnc/passwd

# Log VNC startup
echo "VNC server started on port 5900"

# Keep the script running to prevent supervisor from restarting VNC repeatedly
tail -f $HOME/.vnc/*log
