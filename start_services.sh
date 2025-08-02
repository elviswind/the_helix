#!/bin/bash

# AR System v3.0 - Service Startup Script
# This script starts all services required for the Agentic Retrieval System

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to wait for a service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready on $host:$port..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $max_attempts seconds"
    return 1
}

# Function to start Redis
start_redis() {
    print_status "Starting Redis..."
    
    if command_exists redis-server; then
        if ! port_in_use 6379; then
            redis-server --daemonize yes
            wait_for_service localhost 6379 "Redis"
            print_success "Redis started successfully"
        else
            print_warning "Redis is already running on port 6379"
        fi
    else
        print_error "Redis is not installed. Please install Redis first."
        print_status "On Ubuntu/Debian: sudo apt-get install redis-server"
        print_status "On macOS: brew install redis"
        exit 1
    fi
}

# Function to start Celery worker
start_celery_worker() {
    print_status "Starting Celery worker..."
    
    if [ -f "run_worker.py" ]; then
        # Start Celery worker in background
        python3 run_worker.py &
        CELERY_PID=$!
        echo $CELERY_PID > .celery_worker.pid
        print_success "Celery worker started with PID $CELERY_PID"
    else
        print_error "run_worker.py not found"
        exit 1
    fi
}

# Function to start FastAPI server
start_fastapi_server() {
    print_status "Starting FastAPI server..."
    
    if [ -f "main.py" ]; then
        # Start FastAPI server in background
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
        FASTAPI_PID=$!
        echo $FASTAPI_PID > .fastapi_server.pid
        print_success "FastAPI server started with PID $FASTAPI_PID"
        print_status "FastAPI server will be available at http://localhost:8000"
    else
        print_error "main.py not found"
        exit 1
    fi
}

# Function to start MCP server
start_mcp_server() {
    print_status "Starting MCP server..."
    
    if [ -f "start_mcp_server.py" ]; then
        # Start MCP server in background
        python3 start_mcp_server.py &
        MCP_PID=$!
        echo $MCP_PID > .mcp_server.pid
        print_success "MCP server started with PID $MCP_PID"
        print_status "MCP server will be available at http://localhost:8001"
    else
        print_error "start_mcp_server.py not found"
        exit 1
    fi
}

# Function to check Python dependencies
check_dependencies() {
    print_status "Checking Python dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    
    # Check if virtual environment is activated
    if [ -z "$VIRTUAL_ENV" ]; then
        print_warning "No virtual environment detected. Consider using a virtual environment."
    fi
    
    # Check if all required packages are installed
    if ! python3 -c "import fastapi, uvicorn, celery, redis, sqlalchemy" 2>/dev/null; then
        print_error "Some required Python packages are missing."
        print_status "Installing dependencies from requirements.txt..."
        pip install -r requirements.txt
    else
        print_success "All required Python packages are installed"
    fi
}

# Function to create database tables
setup_database() {
    print_status "Setting up database..."
    
    if [ -f "main.py" ]; then
        python3 -c "
import sys
sys.path.insert(0, '.')
from models import create_tables
create_tables()
print('Database tables created successfully')
"
        print_success "Database setup completed"
    else
        print_error "main.py not found - cannot setup database"
        exit 1
    fi
}

# Function to stop all services
stop_services() {
    print_status "Stopping all services..."
    
    # Stop Celery worker
    if [ -f ".celery_worker.pid" ]; then
        CELERY_PID=$(cat .celery_worker.pid)
        if kill -0 $CELERY_PID 2>/dev/null; then
            kill $CELERY_PID
            print_success "Celery worker stopped"
        fi
        rm -f .celery_worker.pid
    fi
    
    # Stop FastAPI server
    if [ -f ".fastapi_server.pid" ]; then
        FASTAPI_PID=$(cat .fastapi_server.pid)
        if kill -0 $FASTAPI_PID 2>/dev/null; then
            kill $FASTAPI_PID
            print_success "FastAPI server stopped"
        fi
        rm -f .fastapi_server.pid
    fi
    
    # Stop MCP server
    if [ -f ".mcp_server.pid" ]; then
        MCP_PID=$(cat .mcp_server.pid)
        if kill -0 $MCP_PID 2>/dev/null; then
            kill $MCP_PID
            print_success "MCP server stopped"
        fi
        rm -f .mcp_server.pid
    fi
    
    # Stop Redis (if started by this script)
    if command_exists redis-cli; then
        redis-cli shutdown 2>/dev/null || true
        print_success "Redis stopped"
    fi
}

# Function to show service status
show_status() {
    print_status "Service Status:"
    echo "=================="
    
    # Check Redis
    if port_in_use 6379; then
        echo -e "${GREEN}✓${NC} Redis (port 6379) - Running"
    else
        echo -e "${RED}✗${NC} Redis (port 6379) - Not running"
    fi
    
    # Check FastAPI server
    if port_in_use 8000; then
        echo -e "${GREEN}✓${NC} FastAPI Server (port 8000) - Running"
    else
        echo -e "${RED}✗${NC} FastAPI Server (port 8000) - Not running"
    fi
    
    # Check MCP server
    if port_in_use 8001; then
        echo -e "${GREEN}✓${NC} MCP Server (port 8001) - Running"
    else
        echo -e "${RED}✗${NC} MCP Server (port 8001) - Not running"
    fi
    
    # Check Celery worker
    if [ -f ".celery_worker.pid" ]; then
        CELERY_PID=$(cat .celery_worker.pid)
        if kill -0 $CELERY_PID 2>/dev/null; then
            echo -e "${GREEN}✓${NC} Celery Worker (PID $CELERY_PID) - Running"
        else
            echo -e "${RED}✗${NC} Celery Worker - Not running (stale PID file)"
        fi
    else
        echo -e "${RED}✗${NC} Celery Worker - Not running"
    fi
}

# Function to show help
show_help() {
    echo "AR System v3.0 - Service Management Script"
    echo "=========================================="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start all services (default)"
    echo "  stop      Stop all services"
    echo "  restart   Restart all services"
    echo "  status    Show status of all services"
    echo "  help      Show this help message"
    echo ""
    echo "Services:"
    echo "  - Redis (port 6379)"
    echo "  - Celery Worker"
    echo "  - FastAPI Server (port 8000)"
    echo "  - MCP Server (port 8001)"
    echo ""
    echo "Web Interface:"
    echo "  - Main UI: http://localhost:8000"
    echo "  - Research Interface: http://localhost:8000/static/research.html"
    echo "  - API Documentation: http://localhost:8000/docs"
}

# Main script logic
case "${1:-start}" in
    "start")
        echo "Starting AR System v3.0..."
        echo "=========================="
        
        check_dependencies
        setup_database
        start_redis
        start_celery_worker
        sleep 2  # Give Celery worker time to start
        start_fastapi_server
        sleep 2  # Give FastAPI server time to start
        start_mcp_server
        
        echo ""
        print_success "All services started successfully!"
        echo ""
        echo "Services are now running:"
        echo "  - Redis: localhost:6379"
        echo "  - FastAPI Server: http://localhost:8000"
        echo "  - MCP Server: http://localhost:8001"
        echo "  - Celery Worker: Background process"
        echo ""
        echo "Web Interface:"
        echo "  - Main UI: http://localhost:8000"
        echo "  - Research Interface: http://localhost:8000/static/research.html"
        echo "  - API Documentation: http://localhost:8000/docs"
        echo ""
        echo "To stop all services, run: $0 stop"
        echo "To check status, run: $0 status"
        ;;
    "stop")
        stop_services
        print_success "All services stopped"
        ;;
    "restart")
        print_status "Restarting all services..."
        stop_services
        sleep 2
        $0 start
        ;;
    "status")
        show_status
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 