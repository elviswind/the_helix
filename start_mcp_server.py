#!/usr/bin/env python3
"""
Startup script for the AR v3.0 MCP Server
"""

import uvicorn
from config import config
from logging_config import get_file_logger

if __name__ == "__main__":
    logger = get_file_logger(
        logger_name="mcp.startup",
        log_file_path="logs/mcp_server.log",
    )

    logger.info("Starting AR v3.0 MCP Server...")
    logger.info("API will be available at: %s", config.get_url('mcp_server'))
    logger.info("API documentation at: %s", f"{config.get_url('mcp_server')}/docs")

    uvicorn.run(
        "mcp_api:app",
        host=config.HOST,
        port=config.get_port("mcp_server"),
        reload=config.RELOAD,
        log_level=config.LOG_LEVEL
    )