#!/usr/bin/env python3
"""
Script to run the Celery worker for the AR System
"""

import os
import sys
import uuid

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery_app import celery_app

if __name__ == '__main__':
    # Generate a unique node name to prevent conflicts
    node_name = f"ar-worker-{uuid.uuid4().hex[:8]}"
    
    # Run the Celery worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--pool=prefork',
        f'--hostname={node_name}'
    ]) 