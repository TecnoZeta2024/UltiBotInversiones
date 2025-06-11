#!/bin/bash
# Frontend container entrypoint - configures and starts all services

# Log startup
echo "Starting UltiBot Frontend container..."

# Set VNC password from environment or use default
if [ -n "$VNC_PASSWORD" ]; then
    echo "Setting VNC password from environment variable"
    mkdir -p /root/.vnc
    echo "$VNC_PASSWORD" | vncpasswd -f > /root/.vnc/passwd
    chmod 600 /root/.vnc/passwd
else
    echo "Using default VNC password"
    mkdir -p /root/.vnc
    echo "1234" | vncpasswd -f > /root/.vnc/passwd
    chmod 600 /root/.vnc/passwd
fi

# Wait for backend to be ready
echo "Waiting for backend service to be available..."
/app/wait-for-it.sh ${BACKEND_URL:-http://backend:8000}/health --timeout=60
BACKEND_STATUS=$?

if [ $BACKEND_STATUS -ne 0 ]; then
    echo "Warning: Backend may not be fully ready, but continuing startup anyway"
else
    echo "Backend service is available"
fi

# Start supervisord to manage all processes
echo "Starting supervisord to manage all processes..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
