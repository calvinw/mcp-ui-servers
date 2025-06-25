import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
import logging
from typing import Any
from company_selector_server import mcp, set_websocket_manager, handle_state_response

# Add parent directory to path for shared modules
sys.path.append(str(Path(__file__).parent.parent))
from shared_websocket import ConnectionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create WebSocket manager and make it available to server.py
manager = ConnectionManager()
set_websocket_manager(manager)

# Create the ASGI app for MCP
http_app = mcp.http_app(transport="sse", path='/sse')

# Wrap with FastAPI
app = FastAPI(title="Company Selector MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/")
async def root():
    """Root endpoint that redirects to the button interface"""
    return JSONResponse({
        "message": "Company Selector MCP Server",
        "interfaces": {
            "mcp": "/sse",
            "company": "/company",
            "websocket": "/ws"
        }
    })

@app.get("/debug/connections")
async def debug_connections():
    """Debug endpoint to see active connections"""
    return JSONResponse({
        "total_connections": len(manager.active_connections),
        "session_connections": list(manager.session_connections.keys()),
        "has_connections": manager.has_connections()
    })

@app.get("/company")
async def company_interface():
    """Serve the company selector interface HTML page"""
    session_id = manager.generate_session_id()
    
    # Read the HTML template
    html_path = Path(__file__).parent / "static" / "index.html"
    if not html_path.exists():
        return HTMLResponse("""
        <html>
            <head><title>Company Selector Interface Not Found</title></head>
            <body>
                <h1>Company Selector Interface Not Found</h1>
                <p>The static/index.html file is missing.</p>
            </body>
        </html>
        """)
    
    with open(html_path, 'r') as f:
        html_content = f.read()
    
    # Replace placeholder with actual session ID
    html_content = html_content.replace('SESSION_ID_PLACEHOLDER', session_id)
    
    return HTMLResponse(html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str = None):
    """WebSocket endpoint for real-time communication with company selector interface"""
    # Get session_id from query parameters
    session_id = websocket.query_params.get('session_id')
    logger.info(f"WebSocket connection attempt with session_id='{session_id}'")
    
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                logger.info(f"Received WebSocket message: {message}")
                
                # Handle different message types
                if message.get('type') == 'company-state-response':
                    # Handle company state response from client
                    request_id = message.get('request_id')
                    state = message.get('state', {})
                    
                    if request_id:
                        handle_state_response(request_id, state)
                    
                elif message.get('type') == 'ping':
                    # Respond to ping
                    await websocket.send_text(json.dumps({'type': 'pong'}))
                    
                else:
                    logger.warning(f"Unknown message type: {message.get('type')}")
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/oauth/metadata")
async def oauth_metadata():
    """OAuth metadata endpoint for MCP client discovery"""
    return JSONResponse({
        "authorization_endpoint": "https://example.com/oauth/authorize",
        "token_endpoint": "https://example.com/oauth/token"
    })

# Mount the MCP server to handle SSE - must be AFTER all other routes
app.mount("/", http_app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
