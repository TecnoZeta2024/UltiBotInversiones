#!/bin/bash
# wait-for-it.sh - Wait for a service to be available
# Adapted from https://github.com/vishnubob/wait-for-it

TIMEOUT=15
QUIET=0
PROTOCOL="http"

usage() {
  echo "Usage: $0 host:port|url [-t timeout] [-- command args]"
  echo "  -t TIMEOUT                  Timeout in seconds, default is 15"
  echo "  -- COMMAND ARGS             Execute command with args after the test completes"
  exit 1
}

wait_for() {
  local url=$1
  local timeout=$2

  # Extract protocol, host, and port from URL
  if [[ $url == http://* ]] || [[ $url == https://* ]]; then
    PROTOCOL=$(echo "$url" | cut -d: -f1)
    HOST=$(echo "$url" | sed -e "s,$PROTOCOL://,,g" | cut -d/ -f1 | cut -d: -f1)
    PORT=$(echo "$url" | sed -e "s,$PROTOCOL://,,g" | cut -d/ -f1 | grep ":" | cut -d: -f2)
    PATH_PART=$(echo "$url" | sed -e "s,$PROTOCOL://$HOST\(:$PORT\)\?,,g")
    
    # Default ports if not specified
    if [ -z "$PORT" ]; then
      if [ "$PROTOCOL" = "https" ]; then
        PORT=443
      else
        PORT=80
      fi
    fi
  else
    # Assuming host:port format
    HOST=$(echo "$url" | cut -d: -f1)
    PORT=$(echo "$url" | cut -d: -f2)
    PATH_PART=""
  fi

  echo "Waiting for $HOST:$PORT..."
  
  start_ts=$(date +%s)
  while :
  do
    nc -z "$HOST" "$PORT" > /dev/null 2>&1
    nc_result=$?
    
    if [ $nc_result -eq 0 ]; then
      # If path part is specified, also check HTTP response
      if [ ! -z "$PATH_PART" ]; then
        if command -v curl &> /dev/null; then
          curl --silent --fail "$PROTOCOL://$HOST:$PORT$PATH_PART" > /dev/null 2>&1
          curl_result=$?
          if [ $curl_result -eq 0 ]; then
            break
          fi
          echo "Service at $url not fully ready yet, retrying..."
        else
          # Can't check HTTP response without curl, assume it's ready
          break
        fi
      else
        break
      fi
    fi
    
    end_ts=$(date +%s)
    if [ $((end_ts - start_ts)) -gt $timeout ]; then
      echo "Timeout reached after $timeout seconds"
      return 1
    fi
    sleep 1
  done
  
  return 0
}

while getopts ":t:" opt; do
  case $opt in
    t) TIMEOUT=$OPTARG ;;
    *) usage ;;
  esac
done

shift $((OPTIND-1))

if [ "$#" -eq 0 ]; then
  usage
fi

URL="$1"
shift

wait_for "$URL" "$TIMEOUT" || exit 1

if [ $# -gt 0 ]; then
  exec "$@"
fi

exit 0
