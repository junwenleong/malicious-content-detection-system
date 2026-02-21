#!/bin/bash
set -e

# Default to (2 * cores) + 1 workers if not set, or 1 if detection fails
if [ -z "$WORKERS" ]; then
  if command -v nproc > /dev/null; then
    CORES=$(nproc)
    WORKERS=$((CORES * 2 + 1))
  else
    WORKERS=1
  fi
fi

echo "Starting Gunicorn with $WORKERS workers..."

exec gunicorn -k uvicorn.workers.UvicornWorker \
    -w "$WORKERS" \
    --timeout 120 \
    -b 0.0.0.0:8000 \
    api.app:app
