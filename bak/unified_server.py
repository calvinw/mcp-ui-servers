import os
import sys
import importlib.util
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to load a module from a specific path
def load_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Change to each directory and load the servers as if they were running independently
original_cwd = os.getcwd()

# Load Strudel server
strudel_dir = Path(__file__).parent / "mcp-strudel"
os.chdir(str(strudel_dir))
sys.path.insert(0, str(strudel_dir))
strudel_sse_server = load_module_from_path("sse_strudel_server", str(strudel_dir / "sse_strudel_server.py"))
strudel_app = strudel_sse_server.app
sys.path.remove(str(strudel_dir))
os.chdir(original_cwd)

# Load Button server  
button_dir = Path(__file__).parent / "mcp-button-state"
os.chdir(str(button_dir))
sys.path.insert(0, str(button_dir))
button_sse_server = load_module_from_path("sse_button_state_server", str(button_dir / "sse_button_state_server.py"))
button_app = button_sse_server.app
sys.path.remove(str(button_dir))
os.chdir(original_cwd)

# OAuth metadata endpoint
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

# Add OAuth metadata route
app.add_api_route("/.well-known/oauth-authorization-server", oauth_metadata, methods=["GET"])

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "MCP UI Servers",
        "endpoints": {
            "mcp_endpoints": [
                "/strudel/sse",
                "/button/sse"
            ],
            "ui_endpoints": [
                "/strudel",
                "/button"
            ]
        }
    }

# Mount the sub-applications with their own static files and WebSocket endpoints
app.mount("/strudel", strudel_app)
app.mount("/button", button_app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"""
🎵 MCP UI Servers Starting on port {port}!

Available endpoints:
- Strudel MCP: http://localhost:{port}/strudel/sse
- Button State MCP: http://localhost:{port}/button/sse
- Strudel UI: http://localhost:{port}/strudel
- Button UI: http://localhost:{port}/button

Ready for Claude integration! 🤖
    """)
    uvicorn.run(app, host="0.0.0.0", port=port)