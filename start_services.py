#!/usr/bin/env python3
"""
AR System v3.0 - Service Startup Script (Python Version)
This script starts all services required for the Agentic Retrieval System
"""

import os
import sys
import time
import signal
import subprocess
import threading
import socket
from pathlib import Path
from typing import Optional, Dict, List

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_status(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

def print_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def print_error(message: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

class ServiceManager:
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.pid_files = {
            'celery': '.celery_worker.pid',
            'fastapi': '.fastapi_server.pid',
            'mcp': '.mcp_server.pid'
        }
        
    def check_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False
    
    def wait_for_port(self, port: int, timeout: int = 30) -> bool:
        """Wait for a port to become available"""
        print_status(f"Waiting for port {port} to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(('localhost', port))
                    print_success(f"Port {port} is ready!")
                    return True
            except OSError:
                time.sleep(1)
        
        print_error(f"Port {port} failed to become ready within {timeout} seconds")
        return False
    
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        print_status("Checking Python dependencies...")
        
        if not Path("requirements.txt").exists():
            print_error("requirements.txt not found")
            sys.exit(1)
        
        # Check if virtual environment is activated
        if not os.getenv('VIRTUAL_ENV'):
            print_warning("No virtual environment detected. Consider using a virtual environment.")
        
        # Check required packages
        required_packages = ['fastapi', 'uvicorn', 'celery', 'redis', 'sqlalchemy']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print_error(f"Missing packages: {', '.join(missing_packages)}")
            print_status("Installing dependencies from requirements.txt...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        else:
            print_success("All required Python packages are installed")
    
    def setup_database(self):
        """Setup database tables"""
        print_status("Setting up database...")
        
        if not Path("main.py").exists():
            print_error("main.py not found - cannot setup database")
            sys.exit(1)
        
        try:
            # Add current directory to Python path
            sys.path.insert(0, str(Path.cwd()))
            from models import create_tables
            create_tables()
            print_success("Database setup completed")
        except Exception as e:
            print_error(f"Database setup failed: {e}")
            sys.exit(1)
    
    def start_redis(self):
        """Start Redis server"""
        print_status("Starting Redis...")
        
        if not self.check_port_available(6379):
            print_warning("Redis is already running on port 6379")
            return
        
        try:
            # Try to start Redis
            process = subprocess.Popen(
                ['redis-server', '--daemonize', 'yes'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            process.wait()
            
            if self.wait_for_port(6379):
                print_success("Redis started successfully")
            else:
                print_error("Failed to start Redis")
                sys.exit(1)
        except FileNotFoundError:
            print_error("Redis is not installed. Please install Redis first.")
            print_status("On Ubuntu/Debian: sudo apt-get install redis-server")
            print_status("On macOS: brew install redis")
            sys.exit(1)
    
    def start_celery_worker(self):
        """Start Celery worker"""
        print_status("Starting Celery worker...")
        
        if not Path("run_worker.py").exists():
            print_error("run_worker.py not found")
            sys.exit(1)
        
        try:
            process = subprocess.Popen(
                [sys.executable, 'run_worker.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['celery'] = process
            
            # Save PID to file
            with open(self.pid_files['celery'], 'w') as f:
                f.write(str(process.pid))
            
            print_success(f"Celery worker started with PID {process.pid}")
        except Exception as e:
            print_error(f"Failed to start Celery worker: {e}")
            sys.exit(1)
    
    def start_fastapi_server(self):
        """Start FastAPI server"""
        print_status("Starting FastAPI server...")
        
        if not Path("main.py").exists():
            print_error("main.py not found")
            sys.exit(1)
        
        try:
            process = subprocess.Popen([
                sys.executable, '-m', 'uvicorn', 'main:app',
                '--host', '0.0.0.0', '--port', '8000', '--reload'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes['fastapi'] = process
            
            # Save PID to file
            with open(self.pid_files['fastapi'], 'w') as f:
                f.write(str(process.pid))
            
            print_success(f"FastAPI server started with PID {process.pid}")
            print_status("FastAPI server will be available at http://localhost:8000")
        except Exception as e:
            print_error(f"Failed to start FastAPI server: {e}")
            sys.exit(1)
    
    def start_mcp_server(self):
        """Start MCP server"""
        print_status("Starting MCP server...")
        
        if not Path("start_mcp_server.py").exists():
            print_error("start_mcp_server.py not found")
            sys.exit(1)
        
        try:
            process = subprocess.Popen([
                sys.executable, 'start_mcp_server.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes['mcp'] = process
            
            # Save PID to file
            with open(self.pid_files['mcp'], 'w') as f:
                f.write(str(process.pid))
            
            print_success(f"MCP server started with PID {process.pid}")
            print_status("MCP server will be available at http://localhost:8001")
        except Exception as e:
            print_error(f"Failed to start MCP server: {e}")
            sys.exit(1)
    
    def stop_services(self):
        """Stop all running services"""
        print_status("Stopping all services...")
        
        # Stop processes started by this script
        for name, process in self.processes.items():
            if process.poll() is None:  # Process is still running
                process.terminate()
                try:
                    process.wait(timeout=5)
                    print_success(f"{name.capitalize()} service stopped")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print_warning(f"{name.capitalize()} service force killed")
        
        # Clean up PID files
        for pid_file in self.pid_files.values():
            if Path(pid_file).exists():
                Path(pid_file).unlink()
        
        # Stop Redis
        try:
            subprocess.run(['redis-cli', 'shutdown'], check=False)
            print_success("Redis stopped")
        except FileNotFoundError:
            pass
        
        print_success("All services stopped")
    
    def show_status(self):
        """Show status of all services"""
        print_status("Service Status:")
        print("==================")
        
        # Check Redis
        if not self.check_port_available(6379):
            print(f"{Colors.GREEN}✓{Colors.NC} Redis (port 6379) - Running")
        else:
            print(f"{Colors.RED}✗{Colors.NC} Redis (port 6379) - Not running")
        
        # Check FastAPI server
        if not self.check_port_available(8000):
            print(f"{Colors.GREEN}✓{Colors.NC} FastAPI Server (port 8000) - Running")
        else:
            print(f"{Colors.RED}✗{Colors.NC} FastAPI Server (port 8000) - Not running")
        
        # Check MCP server
        if not self.check_port_available(8001):
            print(f"{Colors.GREEN}✓{Colors.NC} MCP Server (port 8001) - Running")
        else:
            print(f"{Colors.RED}✗{Colors.NC} MCP Server (port 8001) - Not running")
        
        # Check Celery worker
        celery_pid_file = Path(self.pid_files['celery'])
        if celery_pid_file.exists():
            try:
                with open(celery_pid_file) as f:
                    pid = int(f.read().strip())
                # Check if process is running
                os.kill(pid, 0)
                print(f"{Colors.GREEN}✓{Colors.NC} Celery Worker (PID {pid}) - Running")
            except (ValueError, OSError):
                print(f"{Colors.RED}✗{Colors.NC} Celery Worker - Not running (stale PID file)")
        else:
            print(f"{Colors.RED}✗{Colors.NC} Celery Worker - Not running")
    
    def start_all(self):
        """Start all services"""
        print("Starting AR System v3.0...")
        print("==========================")
        
        self.check_dependencies()
        self.setup_database()
        self.start_redis()
        self.start_celery_worker()
        time.sleep(2)  # Give Celery worker time to start
        self.start_fastapi_server()
        time.sleep(2)  # Give FastAPI server time to start
        self.start_mcp_server()
        
        print("")
        print_success("All services started successfully!")
        print("")
        print("Services are now running:")
        print("  - Redis: localhost:6379")
        print("  - FastAPI Server: http://localhost:8000")
        print("  - MCP Server: http://localhost:8001")
        print("  - Celery Worker: Background process")
        print("")
        print("Web Interface:")
        print("  - Main UI: http://localhost:8000")
        print("  - Research Interface: http://localhost:8000/static/research.html")
        print("  - API Documentation: http://localhost:8000/docs")
        print("")
        print("To stop all services, run: python start_services.py stop")
        print("To check status, run: python start_services.py status")
    
    def show_help(self):
        """Show help message"""
        print("AR System v3.0 - Service Management Script (Python)")
        print("==================================================")
        print("")
        print("Usage: python start_services.py [COMMAND]")
        print("")
        print("Commands:")
        print("  start     Start all services (default)")
        print("  stop      Stop all services")
        print("  restart   Restart all services")
        print("  status    Show status of all services")
        print("  help      Show this help message")
        print("")
        print("Services:")
        print("  - Redis (port 6379)")
        print("  - Celery Worker")
        print("  - FastAPI Server (port 8000)")
        print("  - MCP Server (port 8001)")
        print("")
        print("Web Interface:")
        print("  - Main UI: http://localhost:8000")
        print("  - Research Interface: http://localhost:8000/static/research.html")
        print("  - API Documentation: http://localhost:8000/docs")

def main():
    manager = ServiceManager()
    
    # Handle command line arguments
    command = sys.argv[1] if len(sys.argv) > 1 else "start"
    
    try:
        if command == "start":
            manager.start_all()
        elif command == "stop":
            manager.stop_services()
        elif command == "restart":
            print_status("Restarting all services...")
            manager.stop_services()
            time.sleep(2)
            manager.start_all()
        elif command == "status":
            manager.show_status()
        elif command in ["help", "-h", "--help"]:
            manager.show_help()
        else:
            print_error(f"Unknown command: {command}")
            print("")
            manager.show_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nReceived interrupt signal, stopping services...")
        manager.stop_services()
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        manager.stop_services()
        sys.exit(1)

if __name__ == "__main__":
    main() 