# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development Setup
- Install dependencies: `uv sync` (runs in root directory)
- Run unified MCP server: `uv run python unified_server.py`
- Run unified SSE server: `uv run python unified_sse_server.py`
- Run Chainlit web interface: `./run_chainlit.sh` or `uv run chainlit run -w app.py --host 0.0.0.0 --port 8080`

### Individual Server Development
Each MCP server can be run independently from its subdirectory:
- Local MCP (STDIO): `uv run python server.py`
- Remote MCP (SSE): `uv run python sse_server.py`

### Code Quality
- Format code: `uv run black .`
- Sort imports: `uv run isort .`
- Type checking: `uv run mypy .`
- Run tests: `uv run pytest` (if tests exist)

## Architecture Overview

This repository contains multiple MCP (Model Context Protocol) servers with web-based user interfaces. The project supports both unified deployment and individual server operation.

### Repository Structure

**Root Level** - Unified deployment and shared components
- `unified_server.py` - Combines all MCP servers in a single FastAPI application
- `unified_sse_server.py` - SSE transport wrapper for unified server
- `app.py` - Chainlit web interface for testing all MCP tools
- `shared_websocket.py` - Reusable WebSocket connection manager
- `pyproject.toml` - Root-level dependencies and configuration

**Individual MCP Servers**
- `mcp-strudel/` - Strudel live coding environment with web interface
- `mcp-button-state/` - Button state management with interactive UI controls
- `mcp-company-selector/` - Company selection interface (appears to be in development)

### MCP Server Architecture Pattern

Each MCP server follows a consistent pattern:

**Core Server (server.py)**
- Uses FastMCP framework for MCP protocol handling
- Tools defined with `@mcp.tool()` decorator
- Runs in STDIO mode: `mcp.run()`
- Communicates with web interface via shared WebSocket manager

**SSE Server (sse_server.py)**
- FastAPI wrapper around core MCP server
- Provides `/sse` endpoint for HTTP/SSE transport
- WebSocket endpoint for real-time communication with web interface
- Serves static files for web UI
- Includes CORS middleware and OAuth metadata

**Web Interface**
- Static HTML/JavaScript files for interactive UI
- WebSocket client for real-time communication
- Integration with MCP server functionality

### Key Dependencies

**Core MCP Framework**
- `fastmcp>=2.8.0` - MCP server framework
- `fastapi>=0.115.0` - HTTP server for SSE transport
- `uvicorn[standard]>=0.34.0` - ASGI server
- `websockets>=15.0.0` - WebSocket support

**Web Interface**
- `chainlit` - Interactive web UI for MCP tool testing
- `openai` - LLM integration via OpenRouter
- `httpx>=0.25.0` - HTTP client
- `requests>=2.31.0` - HTTP requests

### Development Tools
- `black>=23.0.0` - Code formatting
- `isort>=5.12.0` - Import sorting  
- `mypy>=1.0.0` - Type checking
- `pytest>=7.0.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async testing support

### Integration Patterns

**WebSocket Communication**
- Shared `ConnectionManager` class handles WebSocket connections
- Session-based connections with memorable 4-character IDs
- Broadcasting support for multiple browser connections
- Automatic reconnection and error handling

**MCP Tool Integration**
- Tools communicate with web interfaces through WebSocket broadcasting
- Real-time pattern execution and state updates
- Error reporting from browser back to MCP server
- Validation and security checks for user input

**Unified Deployment**
- `unified_server.py` dynamically loads individual servers as sub-applications
- Each server maintains its own directory context and dependencies
- Centralized routing with `/strudel` and `/button` prefixes
- Shared CORS configuration and OAuth metadata

### Security Considerations
- Input validation for all MCP tools to prevent code injection
- CORS configuration allows all origins (suitable for development)
- Session-based WebSocket connections for state isolation
- No sensitive data storage in repository (API keys handled via environment)