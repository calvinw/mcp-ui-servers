"""
Company Selector SSE Server - Now using shared ui_app.py
Combines MCP server and UI app without duplication
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from company_selector_server import mcp, set_websocket_manager

# Add parent directory to path for shared modules
sys.path.append(str(Path(__file__).parent.parent))
from shared_websocket import ConnectionManager

# Import the UI app
from ui_app import ui_app, manager as ui_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set the UI manager as the MCP server's WebSocket manager
set_websocket_manager(ui_manager)

# Create the ASGI app for MCP (following BusMgmtDoltDatabase pattern)
http_app = mcp.http_app(transport="sse", path='/sse')

# Minimal OAuth endpoint (just enough for Claude.ai)
async def oauth_metadata(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return JSONResponse({
        "issuer": base_url
    })

# Create main FastAPI app
app = FastAPI(title="Company Selector MCP Server with UI")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add the OAuth metadata route
app.add_api_route("/.well-known/oauth-authorization-server", oauth_metadata, methods=["GET"])

# Mount the UI app at /company path FIRST (specific routes before catch-all)
app.mount("/company", ui_app)

# Mount the MCP server at root (following BusMgmtDoltDatabase pattern)
# This makes /sse available directly
app.mount("/", http_app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"""
🏢 Company Selector MCP Server Starting on port {port}!

🌐 Web Interface: http://localhost:{port}/company
🤖 MCP Endpoint: http://localhost:{port}/sse
⚡ WebSocket: http://localhost:{port}/company/ws
📊 Status: http://localhost:{port}/api/status

Ready for both web browsers and Claude integration! 🎯
    """)
    uvicorn.run(app, host="0.0.0.0", port=port)