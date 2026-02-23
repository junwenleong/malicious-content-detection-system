#!/bin/bash

set -e

echo -e "\033[36mStarting Malicious Content Detection System...\033[0m"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "\033[31mError: Docker is not installed or not in PATH.\033[0m"
    exit 1
fi

# Function to check if a port is in use
is_port_in_use() {
    lsof -i :"$1" &> /dev/null || nc -z localhost "$1" &> /dev/null 2>&1
}

# Find an available backend port starting from 8000
BACKEND_PORT=8000
while is_port_in_use $BACKEND_PORT; do
    echo -e "\033[33mPort $BACKEND_PORT is in use, trying next port...\033[0m"
    BACKEND_PORT=$((BACKEND_PORT + 1))
    if [ $BACKEND_PORT -gt 8100 ]; then
        echo -e "\033[31mError: Could not find available port in range 8000-8100\033[0m"
        exit 1
    fi
done

FRONTEND_PORT=5175

# Check if frontend port is available
if is_port_in_use $FRONTEND_PORT; then
    echo -e "\033[31mError: Frontend port $FRONTEND_PORT is already in use.\033[0m"
    exit 1
fi

# Export ports for docker-compose
export BACKEND_PORT
export FRONTEND_PORT

# Update ALLOWED_ORIGINS to include the new frontend port
export ALLOWED_ORIGINS="[\"http://localhost:$FRONTEND_PORT\", \"http://127.0.0.1:$FRONTEND_PORT\"]"

echo -e "\033[33mBuilding and starting containers...\033[0m"
echo -e "\033[33mBackend will run on port: $BACKEND_PORT\033[0m"
echo -e "\033[33mFrontend will run on port: $FRONTEND_PORT\033[0m"

# Clean up any existing containers first
echo -e "\033[33mCleaning up existing containers...\033[0m"
docker compose down 2>/dev/null || true

# Create a temporary docker-compose override
cat > docker-compose.override.yml <<EOF
services:
  backend:
    ports:
      - "$BACKEND_PORT:8000"
    environment:
      ALLOWED_ORIGINS: '$ALLOWED_ORIGINS'
  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: http://localhost:$BACKEND_PORT
    ports:
      - "$FRONTEND_PORT:80"
EOF

# Run Docker Compose
docker compose up --build -d

if [ $? -eq 0 ]; then
    echo -e "\n\033[32mSystem is running!\033[0m"
    echo -e "\033[36mBackend API: http://localhost:$BACKEND_PORT\033[0m"
    echo -e "\033[36mFrontend UI: http://localhost:$FRONTEND_PORT\033[0m"
    echo -e "\n\033[33mTo stop: docker compose down\033[0m"
else
    echo -e "\033[31mFailed to start containers.\033[0m"
    exit 1
fi
