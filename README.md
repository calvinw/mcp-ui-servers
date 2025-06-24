# MCP UI Servers

Collection of MCP (Model Context Protocol) servers with user interface components.

## Projects

### mcp-strudel
MCP server for Strudel live coding environment with web-based interface.

### mcp-button-state  
MCP server for button state management with interactive UI controls.

## Common Commands

### Development Setup
- Install dependencies: `uv sync` (run in individual project directories)
- Run local MCP server: `uv run python server.py`
- Run remote MCP server: `uv run python sse_server.py`
- Run Chainlit web interface: `./run_chainlit.sh` or `uv run chainlit run -w app.py --host 0.0.0.0 --port 8080`

### Deployment
- Deploy to Heroku: `./deploy_heroku.sh` (in project directories)

## Repository Architecture

Each subdirectory contains a complete MCP server implementation with UI components.

### MCP Server Patterns

**Core Server (server.py)**
- Uses FastMCP framework for MCP protocol handling
- Tools defined with `@mcp.tool()` decorator
- Runs in STDIO mode: `mcp.run()`

**SSE Server (sse_server.py)**
- FastAPI wrapper around core MCP server
- Provides `/sse` endpoint for HTTP/SSE transport
- Enables remote MCP client connections

**Web Interface (app.py)**
- Chainlit-based web UI for interactive testing
- Integrates with OpenRouter for LLM functionality
- Provides tool buttons for quick testing

### Key Dependencies
- **fastmcp** - MCP server framework
- **fastapi** - HTTP server for SSE transport
- **chainlit-mcp-client** - Web interface for MCP tools
- **uvicorn** - ASGI server