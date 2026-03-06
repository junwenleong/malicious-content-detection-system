#!/bin/bash

set -e

echo -e "\033[36mStarting Malicious Content Detection System (hot reload enabled)...\033[0m"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "\033[31mError: Docker is not installed or not in PATH.\033[0m"
    exit 1
fi

BACKEND_PORT=8002
FRONTEND_PORT=5175

# --- Colima-safe Docker socket detection ---
COLIMA_SOCK="$HOME/.colima/default/docker.sock"
if [ -S "$COLIMA_SOCK" ]; then
    export DOCKER_HOST="unix://$COLIMA_SOCK"
    echo -e "\033[32m✓ Using Colima Docker socket\033[0m"
elif [ -S "$HOME/.colima/docker.sock" ]; then
    COLIMA_SOCK="$HOME/.colima/docker.sock"
    export DOCKER_HOST="unix://$COLIMA_SOCK"
    echo -e "\033[32m✓ Using Colima Docker socket (legacy path)\033[0m"
elif [ -S "$HOME/.docker/run/docker.sock" ]; then
    export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"
    echo -e "\033[32m✓ Using Docker Desktop socket\033[0m"
fi

# --- Verify Docker daemon is reachable; recover if Colima forwarder is dead ---
if ! docker info &>/dev/null; then
    echo -e "\033[33mDocker daemon unreachable. Checking Colima...\033[0m"
    if command -v colima &>/dev/null && colima status 2>/dev/null | grep -q "Running"; then
        echo -e "\033[33mColima VM is running but socket is dead. Restarting Colima...\033[0m"
        colima stop 2>/dev/null || true
        colima start 2>/dev/null
        sleep 2
        if ! docker info &>/dev/null; then
            echo -e "\033[31mError: Docker daemon still unreachable after Colima restart.\033[0m"
            exit 1
        fi
        echo -e "\033[32m✓ Colima recovered\033[0m"
    else
        echo -e "\033[31mError: Cannot connect to Docker daemon.\033[0m"
        exit 1
    fi
fi

# --- Release ports safely (docker compose down first, then kill only stray non-Docker processes) ---
echo -e "\033[33mCleaning up existing containers...\033[0m"
# Don't use -v here — it destroys the node_modules anonymous volume
docker compose down --remove-orphans 2>/dev/null || true
sleep 1

# Find the Colima SSH forwarder PID so we never kill it
COLIMA_FORWARDER_PID=""
if [ -S "$COLIMA_SOCK" ]; then
    COLIMA_FORWARDER_PID=$(lsof -t "$COLIMA_SOCK" 2>/dev/null || true)
fi

clear_port() {
    local port=$1
    local pids
    pids=$(lsof -ti :"$port" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        local safe_pids=""
        for pid in $pids; do
            if [ -n "$COLIMA_FORWARDER_PID" ]; then
                local is_forwarder=false
                for fpid in $COLIMA_FORWARDER_PID; do
                    if [ "$pid" = "$fpid" ]; then
                        is_forwarder=true
                        break
                    fi
                done
                if $is_forwarder; then
                    echo -e "\033[90mSkipping Colima forwarder (PID $pid) on port $port\033[0m"
                    continue
                fi
            fi
            safe_pids="$safe_pids $pid"
        done

        safe_pids=$(echo "$safe_pids" | xargs)
        if [ -n "$safe_pids" ]; then
            echo -e "\033[33mClearing stray processes on port $port (PIDs: $safe_pids)...\033[0m"
            echo "$safe_pids" | xargs kill -15 2>/dev/null || true
            sleep 1
            local remaining=""
            for pid in $safe_pids; do
                if kill -0 "$pid" 2>/dev/null; then
                    remaining="$remaining $pid"
                fi
            done
            remaining=$(echo "$remaining" | xargs)
            if [ -n "$remaining" ]; then
                echo "$remaining" | xargs kill -9 2>/dev/null || true
                sleep 0.5
            fi
        fi
    fi
}

clear_port $BACKEND_PORT
clear_port $FRONTEND_PORT

# Export ports for docker compose
export BACKEND_PORT
export FRONTEND_PORT
export VITE_API_URL="http://localhost:$BACKEND_PORT"
export ALLOWED_ORIGINS="[\"http://localhost:$FRONTEND_PORT\", \"http://127.0.0.1:$FRONTEND_PORT\"]"

# --- Smart build: skip --build if nothing changed ---
HASH_DIR=".run_hashes"
mkdir -p "$HASH_DIR"

compute_build_hash() {
    # Hash the files that affect whether we need to rebuild
    cat \
        requirements-api.txt \
        Dockerfile \
        docker-compose.yml \
        docker-compose.dev.yml \
        frontend/Dockerfile.dev \
        frontend/package-lock.json \
        2>/dev/null | shasum -a 256 | cut -d' ' -f1
}

CURRENT_HASH=$(compute_build_hash)
STORED_HASH=""
if [ -f "$HASH_DIR/build.sha256" ]; then
    STORED_HASH=$(cat "$HASH_DIR/build.sha256")
fi

BUILD_FLAGS=""
if [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
    echo -e "\033[33mBuild inputs changed — rebuilding images...\033[0m"
    BUILD_FLAGS="--build"
else
    echo -e "\033[32m✓ Build inputs unchanged — skipping rebuild\033[0m"
fi

# Force rebuild with: ./run.sh --rebuild
if [ "${1:-}" = "--rebuild" ]; then
    echo -e "\033[33mForced rebuild requested\033[0m"
    BUILD_FLAGS="--build"
fi

echo -e "\033[33mBackend will run on port: $BACKEND_PORT\033[0m"
echo -e "\033[33mFrontend will run on port: $FRONTEND_PORT\033[0m"

echo -e "\n\033[32mStarting services...\033[0m"
echo -e "\033[36mBackend API: http://localhost:$BACKEND_PORT\033[0m"
echo -e "\033[36mFrontend UI: http://localhost:$FRONTEND_PORT\033[0m"
echo -e "\n\033[33mPress Ctrl+C to stop all services\033[0m\n"

# Trap Ctrl+C to clean up
trap 'echo -e "\n\033[33mStopping services...\033[0m"; docker compose -f docker-compose.yml -f docker-compose.dev.yml down; exit 0' INT TERM

# If we're building, do the build step first so we can save the hash on success
if [ -n "$BUILD_FLAGS" ]; then
    echo -e "\033[33mBuilding images...\033[0m"
    command docker compose -f docker-compose.yml -f docker-compose.dev.yml build
    echo "$CURRENT_HASH" > "$HASH_DIR/build.sha256"
    echo -e "\033[32m✓ Build complete — hash saved\033[0m"
fi

echo -e "\033[32m✓ Hot reload active — backend restarts on Python changes, frontend uses Vite HMR\033[0m\n"
command docker compose -f docker-compose.yml -f docker-compose.dev.yml up --force-recreate
