#!/usr/bin/env python3
"""
Script to start the Mock MCP Server for Checkpoint 4 testing
"""

import uvicorn
from mcp_server import app

if __name__ == "__main__":
    print("Starting Mock MCP Server on http://localhost:8001")
    print("Available endpoints:")
    print("  - GET  /manifest  - Get available tools")
    print("  - POST /search    - Search for data")
    print("  - GET  /health    - Health check")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info") 