#!/bin/bash
# Start XFCE desktop environment for VNC session

# Wait for VNC server to be ready
while [ ! -e /tmp/.X11-unix/X1 ]; do
  sleep 1
done

# Launch XFCE
/usr/bin/startxfce4 &

# Launch the UltiBot UI application
# We assume the working directory is /app where the project is located
poetry run python src/ultibot_ui/main.py

# Keep the script running
wait
