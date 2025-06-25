#!/bin/bash
#
# This script orchestrates the startup of a headless GUI environment and ensures
# all logs are piped to standard output for Docker logging.

# --- Configuration ---
export DISPLAY=:1
VNC_PASSWORD_FILE="$HOME/.vnc/passwd"

# --- VNC Password Setup ---
# Unconditionally set the VNC password from the VNC_PASSWORD environment variable.
# This prevents state-related issues from previous container runs.
if [ -z "$VNC_PASSWORD" ]; then
    echo "FATAL: VNC_PASSWORD environment variable is not set. Exiting."
    exit 1
fi
echo "Setting VNC password..."
mkdir -p "$HOME/.vnc"
# Use x11vnc to store the password securely.
x11vnc -storepasswd "$VNC_PASSWORD" "$VNC_PASSWORD_FILE"
chmod 600 "$VNC_PASSWORD_FILE" # Ensure correct permissions
echo "VNC password has been set."

# --- XFCE Autostart Configuration ---
# This section has been disabled. The UI application is now launched directly by supervisord
# to ensure proper process management and logging.

# --- Service Startup ---
# 1. Start Xvfb (Virtual Framebuffer) in the background.
#    All logs are piped to stdout/stderr.
echo "Starting Xvfb on display ${DISPLAY}..."
Xvfb ${DISPLAY} -screen 0 ${VNC_RESOLUTION:-1280x800}x${VNC_DEPTH:-24} -ac -nolisten tcp &
XVFB_PID=$!

# Wait for Xvfb to be ready by polling for the X11 socket
echo "Waiting for Xvfb to be ready..."
for i in $(seq 30); do
    if [ -e "/tmp/.X11-unix/X${DISPLAY:1}" ]; then
        echo "Xvfb is ready."
        break
    fi
    sleep 1
done
if ! [ -e "/tmp/.X11-unix/X${DISPLAY:1}" ]; then
    echo "FATAL: Xvfb failed to start. Exiting."
    exit 1
fi

# 2. Start the XFCE Desktop Environment in the background.
echo "Starting XFCE desktop environment..."
startxfce4 &

# 3. Start x11vnc in the foreground. This keeps the container running.
#    It uses the password file and pipes all output to stdout for docker logs.
echo "Starting x11vnc server on port 5900. Use VNC client to connect."
x11vnc -display ${DISPLAY} -forever -usepw -create -rfbport 5900

# This part will not be reached as x11vnc runs in the foreground,
# but it's good practice for script clarity.
wait $XVFB_PID
