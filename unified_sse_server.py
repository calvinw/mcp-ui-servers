import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import string
import random
import json
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import uvicorn
import importlib.util

# Add subdirectories to Python path
sys.path.append(str(Path(__file__).parent / "mcp-button-state"))
sys.path.append(str(Path(__file__).parent / "mcp-strudel"))

# Import button state server
button_path = Path(__file__).parent / "mcp-button-state" / "button_state_server.py"
spec = importlib.util.spec_from_file_location("button_state_server", button_path)
button_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(button_module)
button_mcp = button_module.mcp

# Import strudel server
strudel_path = Path(__file__).parent / "mcp-strudel" / "strudel_server.py"
spec = importlib.util.spec_from_file_location("strudel_server", strudel_path)
strudel_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(strudel_module)
strudel_mcp = strudel_module.mcp

# WebSocket connection manager with session support
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.session_connections: Dict[str, WebSocket] = {}  # session_id -> websocket

    async def connect(self, websocket: WebSocket, session_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if session_id:
            self.session_connections[session_id] = websocket
            logger.info(f"New WebSocket connection with session {session_id}. Total: {len(self.active_connections)}")
        else:
            logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        # Remove from session connections
        session_to_remove = None
        for session_id, ws in self.session_connections.items():
            if ws == websocket:
                session_to_remove = session_id
                break
        if session_to_remove:
            del self.session_connections[session_to_remove]
            logger.info(f"WebSocket disconnected (session {session_to_remove}). Total: {len(self.active_connections)}")
        else:
            logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def send_to_session(self, session_id: str, message: str) -> bool:
        """Send message to specific session. Returns True if successful."""
        if session_id in self.session_connections:
            try:
                await self.session_connections[session_id].send_text(message)
                return True
            except Exception as e:
                logger.error(f"Error sending to session {session_id}: {e}")
                self.disconnect(self.session_connections[session_id])
                return False
        else:
            return False
    
    def has_connections(self) -> bool:
        """Check if there are any active connections"""
        return len(self.active_connections) > 0
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    async def broadcast(self, message: str):
        """Send message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    def generate_session_id(self) -> str:
        """Generate a memorable 4-character session ID (3 letters + 1 digit)"""
        while True:
            letters = ''.join(random.choices(string.ascii_lowercase, k=3))
            digit = random.choice(string.digits)
            session_id = letters + digit
            # Ensure it's not already in use
            if session_id not in self.session_connections:
                return session_id

# Create WebSocket managers and make them available to servers
strudel_manager = ConnectionManager()
button_manager = ConnectionManager()
strudel_module.set_websocket_manager(strudel_manager)
button_module.set_websocket_manager(button_manager)

# Create SSE apps for each MCP server
button_http_app = button_mcp.http_app(transport="sse", path='/sse')
strudel_http_app = strudel_mcp.http_app(transport="sse", path='/sse')

# Minimal OAuth endpoint (just enough for Claude.ai)
async def oauth_metadata(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return JSONResponse({
        "issuer": base_url
    })

# Create main FastAPI app
app = FastAPI(
    title="MCP UI Servers",
    description="Unified server for Strudel and Button State MCP servers with UI interfaces",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "x-api-key", "Upgrade", "Connection", "Sec-WebSocket-Key", "Sec-WebSocket-Version", "Sec-WebSocket-Protocol"],
    expose_headers=["Content-Type", "Authorization", "x-api-key"],
    max_age=86400
)

# Add the OAuth metadata route
app.add_api_route("/.well-known/oauth-authorization-server", oauth_metadata, methods=["GET"])


# UI Routes
@app.get("/strudel")
async def strudel_ui():
    """Serve Strudel live coding interface"""
    session_id = strudel_manager.generate_session_id()
    template_path = Path(__file__).parent / "mcp-strudel" / "static" / "index.html"
    
    with open(template_path, 'r') as f:
        html_content = f.read()
    
    # Inject session ID and update WebSocket URL
    html_content = html_content.replace(
        '<!-- SESSION_ID_PLACEHOLDER -->', 
        f'<script>window.sessionId = "{session_id}";</script>'
    )
    # Update WebSocket URL to use the unified server path
    old_content = html_content
    html_content = html_content.replace('/ws?session_id=', '/strudel/ws?session_id=')
    # Also try alternative patterns just in case
    html_content = html_content.replace('}/ws?session_id=', '}/strudel/ws?session_id=')
    if old_content != html_content:
        logger.info(f"Strudel: Successfully replaced WebSocket URL")
    else:
        logger.warning(f"Strudel: No WebSocket URL replacement occurred")
        logger.info(f"Searching for '/ws?session_id=' in HTML: {'/ws?session_id=' in html_content}")
        # Log the relevant line to debug
        lines = html_content.split('\\n')
        for i, line in enumerate(lines):
            if '/ws' in line:
                logger.info(f"Line {i+1}: {line.strip()}")
    
    return HTMLResponse(content=html_content)

@app.get("/button")
async def button_ui():
    """Serve Button State interface"""
    session_id = button_manager.generate_session_id()
    template_path = Path(__file__).parent / "mcp-button-state" / "static" / "index.html"
    
    with open(template_path, 'r') as f:
        html_content = f.read()
    
    # Inject session ID and update WebSocket URL
    html_content = html_content.replace(
        'SESSION_ID_PLACEHOLDER', 
        session_id
    )
    # Update WebSocket URL to use the unified server path
    old_content = html_content
    html_content = html_content.replace('/ws?session_id=', '/button/ws?session_id=')
    # Also try alternative patterns just in case
    html_content = html_content.replace('}/ws?session_id=', '}/button/ws?session_id=')
    if old_content != html_content:
        logger.info(f"Button: Successfully replaced WebSocket URL")
    else:
        logger.warning(f"Button: No WebSocket URL replacement occurred")
        logger.info(f"Searching for '/ws?session_id=' in HTML: {'/ws?session_id=' in html_content}")
        # Log the relevant line to debug
        lines = html_content.split('\\n')
        for i, line in enumerate(lines):
            if '/ws' in line:
                logger.info(f"Line {i+1}: {line.strip()}")
    
    return HTMLResponse(content=html_content)

# WebSocket endpoints
@app.websocket("/strudel/ws")
async def strudel_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Strudel interface"""
    session_id = websocket.query_params.get('session_id')
    logger.info(f"Strudel WebSocket connection attempt with session_id='{session_id}'")
    
    await strudel_manager.connect(websocket, session_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "current-code-response":
                    request_id = message.get("request_id", "")
                    current_code = message.get("code", "")
                    if request_id:
                        strudel_module.handle_code_response(request_id, current_code)
                elif message.get("type") == "evaluation-error":
                    error_msg = message.get("error", "Unknown error")
                    code_snippet = message.get("code", "Unknown code")
                    logger.error(f"Strudel evaluation error: {error_msg} | Code: {code_snippet}")
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
    except WebSocketDisconnect:
        strudel_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Strudel WebSocket error: {e}")
        strudel_manager.disconnect(websocket)

@app.websocket("/button/ws")
async def button_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Button State interface"""
    session_id = websocket.query_params.get('session_id')
    logger.info(f"Button WebSocket connection attempt with session_id='{session_id}'")
    
    await button_manager.connect(websocket, session_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get('type') == 'button-state-response':
                    request_id = message.get('request_id')
                    state = message.get('state', {})
                    if request_id:
                        button_module.handle_state_response(request_id, state)
                elif message.get('type') == 'ping':
                    await websocket.send_text(json.dumps({'type': 'pong'}))
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
    except WebSocketDisconnect:
        button_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Button WebSocket error: {e}")
        button_manager.disconnect(websocket)

# Mount static file directories
app.mount("/strudel/static", StaticFiles(directory=str(Path(__file__).parent / "mcp-strudel" / "static")), name="strudel_static")
app.mount("/button/static", StaticFiles(directory=str(Path(__file__).parent / "mcp-button-state" / "static")), name="button_static")

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "MCP UI Servers",
        "endpoints": {
            "mcp_endpoints": [
                "https://mcp-ui-servers.mcp.mathplosion.com/mcp-strudel/sse",
                "https://mcp-ui-servers.mcp.mathplosion.com/mcp-button-state/sse"
            ],
            "ui_endpoints": [
                "https://mcp-ui-servers.mcp.mathplosion.com/strudel",
                "https://mcp-ui-servers.mcp.mathplosion.com/button"
            ]
        }
    }

# Mount each MCP server at its respective path
app.mount("/mcp-strudel", strudel_http_app)
app.mount("/mcp-button-state", button_http_app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8002))
    print(f"""
🎵 MCP UI Servers Starting on port {port}!

MCP endpoints available at:
- Strudel MCP: http://localhost:{port}/mcp-strudel/sse
- Button State MCP: http://localhost:{port}/mcp-button-state/sse

Ready for Claude integration! 🤖
    """)
    uvicorn.run(app, host="0.0.0.0", port=port)