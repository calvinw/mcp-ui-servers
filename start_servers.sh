#!/bin/bash

set -euo pipefail

APP_DIR="${APP_DIR:-/app}"
cd "$APP_DIR"

echo "🎵 Starting Unified MCP Server..."

cleanup() {
    echo "Shutting down servers..."
    jobs -p | xargs -r kill 2>/dev/null || true
    exit 0
}

trap cleanup SIGTERM SIGINT EXIT

start_server() {
    local name="$1"
    local port="$2"
    local dir="$3"
    local script="$4"
    
    echo "Starting $name on port $port..."
    
    if [[ ! -d "$dir" ]]; then
        echo "Error: Directory $dir not found"
        return 1
    fi
    
    if [[ ! -f "$dir/$script" ]]; then
        echo "Error: Script $dir/$script not found"
        return 1
    fi
    
    (cd "$dir" && PORT="$port" python "$script") &
    local pid=$!
    echo "$name PID: $pid"
    
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "Error: Failed to start $name"
        return 1
    fi
}

start_server "Unified MCP Server" 8080 "." "unified_sse_server.py"
echo "🚀 Server started!"

wait
