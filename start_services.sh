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

# Function to find process by name and optional port
find_process() {
    local process_name=$1
    local port=${2:-}
    
    if [ -n "$port" ]; then
        # Find process by port
        lsof -ti :$port 2>/dev/null | head -1
    else
        # Find process by name
        pgrep -f "$process_name" 2>/dev/null | head -1
    fi
}

# Function to check if process is running
is_process_running() {
    local process_name=$1
    local port=${2:-}
    
    if [ -n "$port" ]; then
        # Check by port
        lsof -i :$port >/dev/null 2>&1
    else
        # Check by process name
        pgrep -f "$process_name" >/dev/null 2>&1
    fi
}

# Function to kill process by name or port
kill_process() {
    local process_name=$1
    local port=${2:-}
    local signal=${3:-TERM}
    
    if [ -n "$port" ]; then
        # Kill by port
        local pid=$(lsof -ti :$port 2>/dev/null | head -1)
        if [ -n "$pid" ]; then
            kill -$signal $pid 2>/dev/null || true
            return 0
        fi
    else
        # Kill by process name
        local pids=$(pgrep -f "$process_name" 2>/dev/null)
        if [ -n "$pids" ]; then
            echo $pids | xargs kill -$signal 2>/dev/null || true
            return 0
        fi
    fi
    return 1
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
    
    # Get port from config
    local port=$(python3 -c "from config import config; print(config.get_port('redis'))")
    
    if command_exists redis-server; then
        if ! port_in_use $port; then
            redis-server --daemonize yes
            wait_for_service localhost $port "Redis"
            print_success "Redis started successfully"
        else
            print_warning "Redis is already running on port $port"
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
        if ! is_process_running "run_worker.py"; then
            # Start Celery worker in background
            python3 run_worker.py &
            sleep 2  # Give process time to start
            if is_process_running "run_worker.py"; then
                local pid=$(find_process "run_worker.py")
                print_success "Celery worker started with PID $pid"
            else
                print_error "Failed to start Celery worker"
                exit 1
            fi
        else
            local pid=$(find_process "run_worker.py")
            print_warning "Celery worker is already running with PID $pid"
        fi
    else
        print_error "run_worker.py not found"
        exit 1
    fi
}

# Function to start FastAPI server
start_fastapi_server() {
    print_status "Starting FastAPI server..."
    
    # Get port from config
    local port=$(python3 -c "from config import config; print(config.get_port('fastapi_main'))")
    
    if [ -f "main.py" ]; then
        if ! is_process_running "uvicorn main:app" && ! port_in_use $port; then
            # Start FastAPI server in background
            uvicorn main:app --host 0.0.0.0 --port $port --reload &
            sleep 2  # Give process time to start
            if port_in_use $port; then
                local pid=$(find_process "uvicorn main:app")
                print_success "FastAPI server started with PID $pid"
                print_status "FastAPI server will be available at http://localhost:$port"
            else
                print_error "Failed to start FastAPI server"
                exit 1
            fi
        else
            if port_in_use $port; then
                local pid=$(find_process "uvicorn main:app")
                print_warning "FastAPI server is already running with PID $pid on port $port"
            else
                print_warning "FastAPI server process found but port $port is not responding"
            fi
        fi
    else
        print_error "main.py not found"
        exit 1
    fi
}

# Function to start MCP server
start_mcp_server() {
    print_status "Starting MCP server..."
    
    # Get port from config
    local port=$(python3 -c "from config import config; print(config.get_port('mcp_server'))")
    
    if [ -f "start_mcp_server.py" ]; then
        if ! is_process_running "start_mcp_server.py" && ! port_in_use $port; then
            # Start MCP server in background
            python3 start_mcp_server.py &
            sleep 2  # Give process time to start
            if port_in_use $port; then
                local pid=$(find_process "start_mcp_server.py")
                print_success "MCP server started with PID $pid"
                print_status "MCP server will be available at http://localhost:$port"
            else
                print_error "Failed to start MCP server"
                exit 1
            fi
        else
            if port_in_use $port; then
                local pid=$(find_process "start_mcp_server.py")
                print_warning "MCP server is already running with PID $pid on port $port"
            else
                print_warning "MCP server process found but port $port is not responding"
            fi
        fi
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
    if is_process_running "run_worker.py"; then
        if kill_process "run_worker.py"; then
            print_success "Celery worker stopped"
        else
            print_warning "Failed to stop Celery worker"
        fi
    else
        print_warning "Celery worker is not running"
    fi
    
    # Stop FastAPI server
    if is_process_running "uvicorn main:app" || port_in_use 8000; then
        if kill_process "uvicorn main:app" || kill_process "" 8000; then
            print_success "FastAPI server stopped"
        else
            print_warning "Failed to stop FastAPI server"
        fi
    else
        print_warning "FastAPI server is not running"
    fi
    
    # Stop MCP server
    if is_process_running "start_mcp_server.py" || port_in_use 8001; then
        if kill_process "start_mcp_server.py" || kill_process "" 8001; then
            print_success "MCP server stopped"
        else
            print_warning "Failed to stop MCP server"
        fi
    else
        print_warning "MCP server is not running"
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
    
    # Get ports from config
    local redis_port=$(python3 -c "from config import config; print(config.get_port('redis'))")
    local fastapi_port=$(python3 -c "from config import config; print(config.get_port('fastapi_main'))")
    local mcp_port=$(python3 -c "from config import config; print(config.get_port('mcp_server'))")
    
    # Check Redis
    if port_in_use $redis_port; then
        local redis_pid=$(find_process "" $redis_port)
        echo -e "${GREEN}✓${NC} Redis (port $redis_port, PID $redis_pid) - Running"
    else
        echo -e "${RED}✗${NC} Redis (port $redis_port) - Not running"
    fi
    
    # Check FastAPI server
    if port_in_use $fastapi_port; then
        local fastapi_pid=$(find_process "uvicorn main:app")
        echo -e "${GREEN}✓${NC} FastAPI Server (port $fastapi_port, PID $fastapi_pid) - Running"
    else
        echo -e "${RED}✗${NC} FastAPI Server (port $fastapi_port) - Not running"
    fi
    
    # Check MCP server
    if port_in_use $mcp_port; then
        local mcp_pid=$(find_process "start_mcp_server.py")
        echo -e "${GREEN}✓${NC} MCP Server (port $mcp_port, PID $mcp_pid) - Running"
    else
        echo -e "${RED}✗${NC} MCP Server (port $mcp_port) - Not running"
    fi
    
    # Check Celery worker
    if is_process_running "run_worker.py"; then
        local celery_pid=$(find_process "run_worker.py")
        echo -e "${GREEN}✓${NC} Celery Worker (PID $celery_pid) - Running"
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
        redis_port=$(python3 -c "from config import config; print(config.get_port('redis'))")
        fastapi_port=$(python3 -c "from config import config; print(config.get_port('fastapi_main'))")
        mcp_port=$(python3 -c "from config import config; print(config.get_port('mcp_server'))")
        echo "  - Redis: localhost:$redis_port"
        echo "  - FastAPI Server: http://localhost:$fastapi_port"
        echo "  - MCP Server: http://localhost:$mcp_port"
        echo "  - Celery Worker: Background process"
        echo ""
        echo "Web Interface:"
        echo "  - Main UI: http://localhost:$fastapi_port"
        echo "  - Research Interface: http://localhost:$fastapi_port/static/research.html"
        echo "  - API Documentation: http://localhost:$fastapi_port/docs"
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