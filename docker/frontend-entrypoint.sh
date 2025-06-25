#!/bin/bash
# Frontend container entrypoint - waits for dependencies and then executes the main container command.

set -e

echo "Starting UltiBot Frontend container..."

# Wait for backend to be ready
# The URL is taken from the environment variable BACKEND_URL, defaulting to http://backend:8000
echo "Waiting for backend service to be available at ${BACKEND_URL:-http://backend:8000}/health..."
/app/wait-for-it.sh -t 60 ${BACKEND_URL:-http://backend:8000}/health
BACKEND_STATUS=$?

if [ $BACKEND_STATUS -ne 0 ]; then
    echo "Fatal: Backend service did not become available. Exiting."
    exit 1
else
    echo "Backend service is available."
fi

# Print the API_BASE_URL for debugging
echo "API_BASE_URL is set to: $API_BASE_URL"
echo "VNC_PASSWORD is set (from entrypoint): $VNC_PASSWORD"

# Execute the command passed to this script (which is CMD from Dockerfile)
echo "Handing over to supervisord..."
exec "$@"
