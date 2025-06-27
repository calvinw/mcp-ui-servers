"""
Clean Unified SSE Server
Mounts 3 FastMCP servers (for MCP protocol) and 3 FastAPI apps (for web UI) separately
Button State, Company Selector, and Company-to-Company - Strudel moved to separate repo
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import importlib.util

# Add subdirectories to Python path
sys.path.append(str(Path(__file__).parent / "mcp-button-state"))
sys.path.append(str(Path(__file__).parent / "mcp-company-selector"))
sys.path.append(str(Path(__file__).parent / "mcp-company-to-company"))

# Function to load a module from a specific path
def load_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Change to each directory and load both MCP servers and UI apps
original_cwd = os.getcwd()

# Load Button components
button_dir = Path(__file__).parent / "mcp-button-state"
os.chdir(str(button_dir))
button_server_module = load_module_from_path("button_server", str(button_dir / "button_state_server.py"))
button_ui_module = load_module_from_path("button_ui", str(button_dir / "ui_app.py"))
button_mcp_app = button_server_module.mcp.http_app(transport="sse", path='/sse')
button_ui_app = button_ui_module.ui_app
os.chdir(original_cwd)

# Load Company components
company_dir = Path(__file__).parent / "mcp-company-selector"
os.chdir(str(company_dir))
company_server_module = load_module_from_path("company_server", str(company_dir / "company_selector_server.py"))
company_ui_module = load_module_from_path("company_ui", str(company_dir / "ui_app.py"))
company_mcp_app = company_server_module.mcp.http_app(transport="sse", path='/sse')
company_ui_app = company_ui_module.ui_app
os.chdir(original_cwd)

# Load Company-to-Company components
company_to_company_dir = Path(__file__).parent / "mcp-company-to-company"
os.chdir(str(company_to_company_dir))
company_to_company_server_module = load_module_from_path("company_to_company_server", str(company_to_company_dir / "company_to_company_server.py"))
company_to_company_ui_module = load_module_from_path("company_to_company_ui", str(company_to_company_dir / "ui_app.py"))
company_to_company_mcp_app = company_to_company_server_module.mcp.http_app(transport="sse", path='/sse')
company_to_company_ui_app = company_to_company_ui_module.ui_app
os.chdir(original_cwd)

# Connect UI WebSocket managers to MCP servers
button_server_module.set_websocket_manager(button_ui_module.manager) 
company_server_module.set_websocket_manager(company_ui_module.manager)
company_to_company_server_module.set_websocket_manager(company_to_company_ui_module.manager)

# Share pending request dictionaries between UI and MCP modules
# This ensures browser responses reach the MCP server's waiting requests

# The UI modules import the server modules directly, so we need to patch the 
# imported functions to use the unified server's module instances

# For button state: patch the handle_state_response function that was imported
original_button_handle = button_ui_module.handle_state_response
def patched_button_handle(request_id: str, state):
    return button_server_module.handle_state_response(request_id, state)
button_ui_module.handle_state_response = patched_button_handle

# For company selector: patch the handle_state_response function that was imported  
original_company_handle = company_ui_module.handle_state_response
def patched_company_handle(request_id: str, state):
    return company_server_module.handle_state_response(request_id, state)
company_ui_module.handle_state_response = patched_company_handle

# For company-to-company: patch the handle_state_response function that was imported
original_company_to_company_handle = company_to_company_ui_module.handle_state_response
def patched_company_to_company_handle(request_id: str, state):
    return company_to_company_server_module.handle_state_response(request_id, state)
company_to_company_ui_module.handle_state_response = patched_company_to_company_handle

# Minimal OAuth endpoint (just enough for Claude.ai)
async def oauth_metadata(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return JSONResponse({
        "issuer": base_url
    })

# Create main FastAPI app
app = FastAPI(
    title="MCP UI Servers - Button, Company & Company-to-Company",
    description="Unified server for Button State, Company Selector, and Company-to-Company apps",
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

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "MCP UI Servers - Button, Company & Company-to-Company",
        "architecture": "Separate MCP servers and UI apps",
        "endpoints": {
            "mcp_endpoints": [
                "https://mcp-ui-servers.mcp.mathplosion.com/mcp-button-state/sse",
                "https://mcp-ui-servers.mcp.mathplosion.com/mcp-company-selector/sse",
                "https://mcp-ui-servers.mcp.mathplosion.com/mcp-company-to-company/sse"
            ],
            "ui_endpoints": [
                "https://mcp-ui-servers.mcp.mathplosion.com/button",
                "https://mcp-ui-servers.mcp.mathplosion.com/company",
                "https://mcp-ui-servers.mcp.mathplosion.com/company_to_company"
            ]
        }
    }

# Mount MCP servers (for Claude integration)
app.mount("/mcp-button-state", button_mcp_app)
app.mount("/mcp-company-selector", company_mcp_app)
app.mount("/mcp-company-to-company", company_to_company_mcp_app)

# Mount UI apps (for web interfaces)
app.mount("/button", button_ui_app)
app.mount("/company", company_ui_app)
app.mount("/company_to_company", company_to_company_ui_app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"""
🔘 MCP UI Servers Starting on port {port}! (Button, Company & Company-to-Company)

📱 Web UI endpoints:
- Button State UI: https://mcp-ui-servers.mcp.mathplosion.com/button
- Company Selector UI: https://mcp-ui-servers.mcp.mathplosion.com/company
- Company-to-Company UI: https://mcp-ui-servers.mcp.mathplosion.com/company_to_company

🤖 MCP endpoints (for Claude):
- Button State MCP: https://mcp-ui-servers.mcp.mathplosion.com/mcp-button-state/sse  
- Company Selector MCP: https://mcp-ui-servers.mcp.mathplosion.com/mcp-company-selector/sse
- Company-to-Company MCP: https://mcp-ui-servers.mcp.mathplosion.com/mcp-company-to-company/sse

✨ Architecture: 3 MCP servers + 3 UI apps mounted separately
Ready for both web browsers and Claude integration! 🌐🤖
    """)
    uvicorn.run(app, host="0.0.0.0", port=port)