#!/usr/bin/env python3
"""
Display current AR System configuration
"""

from config import config

def main():
    print("AR System v3.0 Configuration")
    print("=" * 40)
    
    print("\nPort Assignments:")
    print("-" * 20)
    for service, port in config.PORTS.items():
        print(f"  {service}: {port}")
    
    print("\nService URLs:")
    print("-" * 20)
    urls = config.get_all_urls()
    for service, url in urls.items():
        print(f"  {service}: {url}")
    
    print("\nOther Settings:")
    print("-" * 20)
    print(f"  Host: {config.HOST}")
    print(f"  Debug: {config.DEBUG}")
    print(f"  Reload: {config.RELOAD}")
    print(f"  Log Level: {config.LOG_LEVEL}")
    print(f"  Database URL: {config.DATABASE_URL}")
    print(f"  Redis URL: {config.REDIS_URL}")

if __name__ == "__main__":
    main() 