"""
Configuration file for AR System v3.0
Centralizes all port assignments and settings to prevent conflicts.
"""

import os
from typing import Dict, Any

class Config:
    """Central configuration for AR System v3.0"""
    
    # Port assignments
    PORTS = {
        "fastapi_main": 8000,      # Main FastAPI application
        "mcp_server": 8001,        # MCP (Master Control Program) server
        "redis": 6379,             # Redis cache/database
        "celery_flower": 5555,     # Celery monitoring (optional)
    }
    
    # Host settings
    HOST = "0.0.0.0"
    
    # Database settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ar_system.db")
    
    # Redis settings
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Celery settings
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # API settings
    API_TITLE = "AR v3.0 MCP Server"
    API_VERSION = "3.0.0"
    API_DESCRIPTION = "Master Control Program for Agentic Retrieval System"
    
    # Development settings
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    RELOAD = os.getenv("RELOAD", "True").lower() == "true"
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
    
    @classmethod
    def get_port(cls, service: str) -> int:
        """Get port for a specific service"""
        return cls.PORTS.get(service)
    
    @classmethod
    def get_url(cls, service: str) -> str:
        """Get full URL for a service"""
        port = cls.get_port(service)
        if port:
            return f"http://localhost:{port}"
        return None
    
    @classmethod
    def get_all_urls(cls) -> Dict[str, str]:
        """Get all service URLs"""
        return {
            service: cls.get_url(service)
            for service in cls.PORTS.keys()
        }

# Create a global config instance
config = Config() 