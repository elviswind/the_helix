#!/usr/bin/env python3
"""
Startup script for the AR v3.0 MCP Server
"""

import uvicorn
from config import config

if __name__ == "__main__":
    print("Starting AR v3.0 MCP Server...")
    print(f"API will be available at: {config.get_url('mcp_server')}")
    print(f"API documentation at: {config.get_url('mcp_server')}/docs")
    
    uvicorn.run(
        "mcp_api:app",
        host=config.HOST,
        port=config.get_port("mcp_server"),
        reload=config.RELOAD,
        log_level=config.LOG_LEVEL
    ) 