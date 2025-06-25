from fastmcp import FastMCP
import asyncio
import logging
import json
import uuid
import time
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP("CompanySelectorMCPServer")

# Global variable to store the WebSocket manager reference
# This will be set by sse_server.py
websocket_manager = None

# Global dictionary to store pending state requests
pending_state_requests = {}

def set_websocket_manager(manager):
    """Set the WebSocket manager from sse_server.py"""
    global websocket_manager
    websocket_manager = manager

def handle_state_response(request_id: str, state: Dict[str, Any]):
    """Handle state response from browser and resolve the pending request"""
    global pending_state_requests
    if request_id in pending_state_requests:
        future = pending_state_requests[request_id]
        if not future.done():
            future.set_result(state)
        del pending_state_requests[request_id]
        logger.info(f"Resolved state request {request_id} with state: {state}")

@mcp.tool()
async def get_company_selections(session_id: str) -> str:
    """
    Get the current company selections from the web interface via WebSocket.
    
    Args:
        session_id: Required session ID to target specific browser connection
        
    Returns:
        JSON string containing the selected companies and page data from the web interface
    """
    global websocket_manager, pending_state_requests
    
    # Validate session_id is provided
    if not session_id or session_id.strip() == "":
        return json.dumps({
            "error": "session_id is required",
            "status": "invalid_input"
        })
    
    if not websocket_manager:
        return json.dumps({
            "error": "WebSocket manager not available",
            "status": "disconnected"
        })
    
    # Check if there are any connected clients
    if not websocket_manager.has_connections():
        return json.dumps({
            "error": "No web interface clients connected",
            "status": "no_clients"
        })
    
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    # Create a future to wait for the response
    future = asyncio.Future()
    pending_state_requests[request_id] = future
    
    # Send request to get current state
    message = {
        "type": "get-company-data",
        "request_id": request_id,
        "timestamp": int(time.time() * 1000)
    }
    
    try:
        # Send the request to the specific session
        success = await websocket_manager.send_to_session(session_id, json.dumps(message))
        if not success:
            return json.dumps({
                "error": f"Session '{session_id}' not found or not connected",
                "status": "session_not_found"
            })
        
        logger.info(f"Sent company data request {request_id}")
        
        # Wait for response with timeout
        try:
            state = await asyncio.wait_for(future, timeout=10.0)
            return json.dumps({
                "status": "success",
                "state": state,
                "request_id": request_id,
                "timestamp": int(time.time() * 1000)
            })
        except asyncio.TimeoutError:
            # Clean up the pending request
            if request_id in pending_state_requests:
                del pending_state_requests[request_id]
            return json.dumps({
                "error": "Timeout waiting for company data response from web interface",
                "status": "timeout",
                "request_id": request_id
            })
            
    except Exception as e:
        # Clean up the pending request
        if request_id in pending_state_requests:
            del pending_state_requests[request_id]
        logger.error(f"Error getting company data: {e}")
        return json.dumps({
            "error": f"Failed to get company data: {str(e)}",
            "status": "error"
        })

@mcp.tool()
async def set_company_info(session_id: str, company1: str, company1_year: str, company2: str, company2_year: str) -> str:
    """
    Set the company selections and years in the web interface via WebSocket.
    
    Args:
        session_id: Required session ID to target specific browser connection
        company1: First company name (Apple, Microsoft, Google, Amazon, Tesla, Meta, Nvidia, Netflix, Salesforce, Adobe)
        company1_year: Year for first company (2018-2024)
        company2: Second company name (Apple, Microsoft, Google, Amazon, Tesla, Meta, Nvidia, Netflix, Salesforce, Adobe)
        company2_year: Year for second company (2018-2024)
        
    Returns:
        JSON string confirming the update was sent to the web interface
    """
    global websocket_manager, pending_state_requests
    
    # Validate session_id is provided
    if not session_id or session_id.strip() == "":
        return json.dumps({
            "error": "session_id is required",
            "status": "invalid_input"
        })
    
    if not websocket_manager:
        return json.dumps({
            "error": "WebSocket manager not available",
            "status": "disconnected"
        })
    
    # Check if there are any connected clients
    if not websocket_manager.has_connections():
        return json.dumps({
            "error": "No web interface clients connected",
            "status": "no_clients"
        })
    
    # Validate company names
    valid_companies = ["Apple", "Microsoft", "Google", "Amazon", "Tesla", "Meta", "Nvidia", "Netflix", "Salesforce", "Adobe"]
    if company1 not in valid_companies:
        return json.dumps({
            "error": f"Invalid company1: {company1}. Must be one of: {', '.join(valid_companies)}",
            "status": "invalid_input"
        })
    
    if company2 not in valid_companies:
        return json.dumps({
            "error": f"Invalid company2: {company2}. Must be one of: {', '.join(valid_companies)}",
            "status": "invalid_input"
        })
    
    # Validate years
    valid_years = ["2018", "2019", "2020", "2021", "2022", "2023", "2024"]
    if company1_year not in valid_years:
        return json.dumps({
            "error": f"Invalid company1_year: {company1_year}. Must be one of: {', '.join(valid_years)}",
            "status": "invalid_input"
        })
    
    if company2_year not in valid_years:
        return json.dumps({
            "error": f"Invalid company2_year: {company2_year}. Must be one of: {', '.join(valid_years)}",
            "status": "invalid_input"
        })
    
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    # Send update request to browser
    message = {
        "type": "set-company-data",
        "request_id": request_id,
        "company1": company1,
        "company1Year": company1_year,
        "company2": company2,
        "company2Year": company2_year,
        "timestamp": int(time.time() * 1000)
    }
    
    try:
        # Send the request to the specific session
        success = await websocket_manager.send_to_session(session_id, json.dumps(message))
        if not success:
            return json.dumps({
                "error": f"Session '{session_id}' not found or not connected",
                "status": "session_not_found"
            })
        
        logger.info(f"Sent company update request {request_id}")
        
        return json.dumps({
            "status": "success",
            "message": f"Company info update sent to session {session_id}",
            "company1": company1,
            "company1_year": company1_year,
            "company2": company2,
            "company2_year": company2_year,
            "request_id": request_id,
            "timestamp": int(time.time() * 1000)
        })
            
    except Exception as e:
        logger.error(f"Error setting company data: {e}")
        return json.dumps({
            "error": f"Failed to set company data: {str(e)}",
            "status": "error"
        })

@mcp.tool()
async def set_company1(session_id: str, company: str, year: str) -> str:
    """
    Set only the first company selection and year in the web interface via WebSocket.
    
    Args:
        session_id: Required session ID to target specific browser connection
        company: Company name (Apple, Microsoft, Google, Amazon, Tesla, Meta, Nvidia, Netflix, Salesforce, Adobe)
        year: Year for the company (2018-2024)
        
    Returns:
        JSON string confirming the update was sent to the web interface
    """
    global websocket_manager
    
    # Validate session_id is provided
    if not session_id or session_id.strip() == "":
        return json.dumps({
            "error": "session_id is required",
            "status": "invalid_input"
        })
    
    if not websocket_manager:
        return json.dumps({
            "error": "WebSocket manager not available",
            "status": "disconnected"
        })
    
    # Check if there are any connected clients
    if not websocket_manager.has_connections():
        return json.dumps({
            "error": "No web interface clients connected",
            "status": "no_clients"
        })
    
    # Validate company name
    valid_companies = ["Apple", "Microsoft", "Google", "Amazon", "Tesla", "Meta", "Nvidia", "Netflix", "Salesforce", "Adobe"]
    if company not in valid_companies:
        return json.dumps({
            "error": f"Invalid company: {company}. Must be one of: {', '.join(valid_companies)}",
            "status": "invalid_input"
        })
    
    # Validate year
    valid_years = ["2018", "2019", "2020", "2021", "2022", "2023", "2024"]
    if year not in valid_years:
        return json.dumps({
            "error": f"Invalid year: {year}. Must be one of: {', '.join(valid_years)}",
            "status": "invalid_input"
        })
    
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    # Send update request to browser
    message = {
        "type": "set-company1-data",
        "request_id": request_id,
        "company": company,
        "year": year,
        "timestamp": int(time.time() * 1000)
    }
    
    try:
        # Send the request to the specific session
        success = await websocket_manager.send_to_session(session_id, json.dumps(message))
        if not success:
            return json.dumps({
                "error": f"Session '{session_id}' not found or not connected",
                "status": "session_not_found"
            })
        
        logger.info(f"Sent company1 update request {request_id}")
        
        return json.dumps({
            "status": "success",
            "message": f"Company1 update sent to session {session_id}",
            "company": company,
            "year": year,
            "request_id": request_id,
            "timestamp": int(time.time() * 1000)
        })
            
    except Exception as e:
        logger.error(f"Error setting company1 data: {e}")
        return json.dumps({
            "error": f"Failed to set company1 data: {str(e)}",
            "status": "error"
        })

@mcp.tool()
async def set_company2(session_id: str, company: str, year: str) -> str:
    """
    Set only the second company selection and year in the web interface via WebSocket.
    
    Args:
        session_id: Required session ID to target specific browser connection
        company: Company name (Apple, Microsoft, Google, Amazon, Tesla, Meta, Nvidia, Netflix, Salesforce, Adobe)
        year: Year for the company (2018-2024)
        
    Returns:
        JSON string confirming the update was sent to the web interface
    """
    global websocket_manager
    
    # Validate session_id is provided
    if not session_id or session_id.strip() == "":
        return json.dumps({
            "error": "session_id is required",
            "status": "invalid_input"
        })
    
    if not websocket_manager:
        return json.dumps({
            "error": "WebSocket manager not available",
            "status": "disconnected"
        })
    
    # Check if there are any connected clients
    if not websocket_manager.has_connections():
        return json.dumps({
            "error": "No web interface clients connected",
            "status": "no_clients"
        })
    
    # Validate company name
    valid_companies = ["Apple", "Microsoft", "Google", "Amazon", "Tesla", "Meta", "Nvidia", "Netflix", "Salesforce", "Adobe"]
    if company not in valid_companies:
        return json.dumps({
            "error": f"Invalid company: {company}. Must be one of: {', '.join(valid_companies)}",
            "status": "invalid_input"
        })
    
    # Validate year
    valid_years = ["2018", "2019", "2020", "2021", "2022", "2023", "2024"]
    if year not in valid_years:
        return json.dumps({
            "error": f"Invalid year: {year}. Must be one of: {', '.join(valid_years)}",
            "status": "invalid_input"
        })
    
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    # Send update request to browser
    message = {
        "type": "set-company2-data",
        "request_id": request_id,
        "company": company,
        "year": year,
        "timestamp": int(time.time() * 1000)
    }
    
    try:
        # Send the request to the specific session
        success = await websocket_manager.send_to_session(session_id, json.dumps(message))
        if not success:
            return json.dumps({
                "error": f"Session '{session_id}' not found or not connected",
                "status": "session_not_found"
            })
        
        logger.info(f"Sent company2 update request {request_id}")
        
        return json.dumps({
            "status": "success",
            "message": f"Company2 update sent to session {session_id}",
            "company": company,
            "year": year,
            "request_id": request_id,
            "timestamp": int(time.time() * 1000)
        })
            
    except Exception as e:
        logger.error(f"Error setting company2 data: {e}")
        return json.dumps({
            "error": f"Failed to set company2 data: {str(e)}",
            "status": "error"
        })

@mcp.tool()
async def get_connection_status() -> str:
    """
    Get the status of WebSocket connections to the web interface.
    
    Returns:
        JSON string with connection status information
    """
    global websocket_manager
    
    if not websocket_manager:
        return json.dumps({
            "status": "disconnected",
            "message": "WebSocket manager not available"
        })
    
    connection_count = websocket_manager.get_connection_count()
    
    return json.dumps({
        "status": "connected" if connection_count > 0 else "no_clients",
        "connection_count": connection_count,
        "message": f"{connection_count} client(s) connected"
    })

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
