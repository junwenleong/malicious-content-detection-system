#!/bin/bash

set -e

echo -e "\033[36mStarting Malicious Content Detection System...\033[0m"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "\033[31mError: Docker is not installed or not in PATH.\033[0m"
    exit 1
fi

BACKEND_PORT=8002
FRONTEND_PORT=5175

# Kill any process occupying a given port
clear_port() {
    local port=$1
    local pids
    pids=$(lsof -ti :"$port" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo -e "\033[33mClearing port $port (PIDs: $pids)...\033[0m"
        echo "$pids" | xargs kill -15 2>/dev/null || true
        sleep 1
        # Force kill any remaining processes
        pids=$(lsof -ti :"$port" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null || true
            sleep 0.5
        fi
    fi
}

clear_port $BACKEND_PORT
clear_port $FRONTEND_PORT

# Export ports for docker-compose
export BACKEND_PORT
export FRONTEND_PORT
export VITE_API_URL="http://localhost:$BACKEND_PORT"

# Update ALLOWED_ORIGINS to include the new frontend port
export ALLOWED_ORIGINS="[\"http://localhost:$FRONTEND_PORT\", \"http://127.0.0.1:$FRONTEND_PORT\"]"

echo -e "\033[33mBuilding and starting containers...\033[0m"
echo -e "\033[33mBackend will run on port: $BACKEND_PORT\033[0m"
echo -e "\033[33mFrontend will run on port: $FRONTEND_PORT\033[0m"

# Clean up any existing containers
echo -e "\033[33mCleaning up existing containers...\033[0m"
docker compose down -v --remove-orphans 2>/dev/null || true

# Wait a moment for cleanup
sleep 1

echo -e "\n\033[32mStarting services...\033[0m"
echo -e "\033[36mBackend API: http://localhost:$BACKEND_PORT\033[0m"
echo -e "\033[36mFrontend UI: http://localhost:$FRONTEND_PORT\033[0m"
echo -e "\n\033[33mPress Ctrl+C to stop all services\033[0m\n"

# Trap Ctrl+C to clean up
trap 'echo -e "\n\033[33mStopping services...\033[0m"; docker compose down; exit 0' INT TERM

# Run Docker Compose in foreground (no -d flag)
docker compose up --build --force-recreate
