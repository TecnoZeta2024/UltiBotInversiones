#!/bin/bash
# Start XFCE desktop environment for VNC session

# Wait for VNC server to start
sleep 2

# Launch XFCE
startxfce4 &

# Keep the script running to prevent supervisor from restarting XFCE repeatedly
wait
