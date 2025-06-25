#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎵 Starting Unified MCP Server locally..."

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

start_server "Unified MCP Server" 8002 "." "unified_sse_server.py"

echo "🚀 Server started!"
echo "- MCP Endpoints:"
echo "  - Strudel: http://localhost:8002/mcp-strudel/sse"
echo "  - Button State: http://localhost:8002/mcp-button-state/sse"
echo "- UI Endpoints:"
echo "  - Strudel: http://localhost:8002/strudel"
echo "  - Button State: http://localhost:8002/button"

wait