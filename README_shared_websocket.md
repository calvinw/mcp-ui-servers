# Shared WebSocket Connection Manager

This module provides a reusable `ConnectionManager` class for handling WebSocket connections with session support across MCP UI servers.

## Usage

### Basic Import

```python
from shared_websocket import ConnectionManager

# Create a manager instance
manager = ConnectionManager()
```

### Integration with MCP Servers

```python
# In your MCP server module (e.g., button_state_server.py)
from shared_websocket import ConnectionManager

# Create and set the manager
websocket_manager = None

def set_websocket_manager(manager: ConnectionManager):
    global websocket_manager
    websocket_manager = manager
```

### WebSocket Endpoint Setup

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = websocket.query_params.get('session_id')
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle messages...
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

## Key Features

- **Session Management**: Associate WebSocket connections with session IDs
- **Automatic Session ID Generation**: Creates memorable 4-character IDs (e.g., "abc7")
- **Broadcasting**: Send messages to all connected clients
- **Targeted Messaging**: Send messages to specific sessions
- **Connection Tracking**: Monitor active connections and session counts
- **Error Handling**: Automatic cleanup of disconnected clients

## Methods

### Connection Management
- `connect(websocket, session_id=None)` - Accept new WebSocket connection
- `disconnect(websocket)` - Remove connection and cleanup sessions
- `has_connections()` - Check if any clients are connected
- `get_connection_count()` - Get total number of connections

### Messaging
- `send_to_session(session_id, message)` - Send to specific session
- `broadcast(message)` - Send to all connected clients

### Session Management
- `generate_session_id()` - Create unique session ID
- `get_session_ids()` - List all active session IDs
- `get_session_connection(session_id)` - Get WebSocket for session

## File Structure

```
mcp-ui-servers/
├── shared_websocket.py          # Shared ConnectionManager
├── unified_sse_server.py        # Uses shared module
├── mcp-button-state/
│   └── sse_button_state_server.py  # Uses shared module
└── mcp-strudel/
    └── sse_strudel_server.py    # Uses shared module
```

## Benefits

1. **Code Reusability**: Single implementation used across all servers
2. **Consistency**: Same behavior and API across different MCP servers
3. **Maintainability**: Bug fixes and improvements apply to all servers
4. **Extensibility**: Easy to add new features to all servers at once