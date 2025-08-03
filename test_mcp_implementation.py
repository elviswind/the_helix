#!/usr/bin/env python3
"""
Test script for the MCP implementation
"""

import requests
import json
import time
from datetime import datetime

# Configuration
MCP_API_URL = "http://localhost:8000"
MOCK_MCP_URL = "http://localhost:8001"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{MCP_API_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Status: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_available_tools():
    """Test the available tools endpoint"""
    print("\nTesting available tools...")
    try:
        response = requests.get(f"{MCP_API_URL}/tools/available")
        if response.status_code == 200:
            tools = response.json()
            print("✅ Available tools endpoint works")
            print(f"   Found {len(tools['tools'])} tools:")
            for tool in tools['tools']:
                print(f"   - {tool['name']}: {tool['description']}")
        else:
            print(f"❌ Available tools failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Available tools error: {e}")

def test_tool_execution():
    """Test tool execution"""
    print("\nTesting tool execution...")
    try:
        # Test XBRL tool
        xbrl_request = {
            "tool_name": "xbrl_financial_fact_retriever",
            "parameters": {
                "symbol": "AAPL",
                "year": 2023,
                "concept": "Revenue"
            }
        }
        
        response = requests.post(f"{MCP_API_URL}/tools/execute", json=xbrl_request)
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ XBRL tool execution successful")
                print(f"   Result: {result['result']}")
            else:
                print(f"❌ XBRL tool execution failed: {result['error']}")
        else:
            print(f"❌ Tool execution request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Tool execution error: {e}")

def test_research_job_creation():
    """Test creating a research job"""
    print("\nTesting research job creation...")
    try:
        research_request = {
            "query": "Evaluate the long-term investment case for Apple (AAPL)",
            "user_id": "test_user"
        }
        
        response = requests.post(f"{MCP_API_URL}/research/start", json=research_request)
        if response.status_code == 202:
            result = response.json()
            job_id = result['job_id']
            print("✅ Research job created successfully")
            print(f"   Job ID: {job_id}")
            return job_id
        else:
            print(f"❌ Research job creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Research job creation error: {e}")
        return None

def test_job_status(job_id):
    """Test checking job status"""
    if not job_id:
        return
        
    print(f"\nTesting job status for {job_id}...")
    try:
        response = requests.get(f"{MCP_API_URL}/research/{job_id}/status")
        if response.status_code == 200:
            status = response.json()
            print("✅ Job status retrieved successfully")
            print(f"   Status: {status['status']}")
            print(f"   Query: {status['initial_query']}")
            return status
        else:
            print(f"❌ Job status failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Job status error: {e}")
        return None

def test_mock_mcp_server():
    """Test the mock MCP server"""
    print("\nTesting mock MCP server...")
    try:
        # Test manifest
        response = requests.get(f"{MOCK_MCP_URL}/manifest")
        if response.status_code == 200:
            manifest = response.json()
            print("✅ Mock MCP manifest retrieved")
            print(f"   Name: {manifest['name']}")
            print(f"   Tools: {len(manifest['tools'])}")
        else:
            print(f"❌ Mock MCP manifest failed: {response.status_code}")
            
        # Test 10-K report
        report_request = {"ticker": "AAPL", "section": "business_overview"}
        response = requests.post(f"{MOCK_MCP_URL}/10k-report", json=report_request)
        if response.status_code == 200:
            report = response.json()
            print("✅ Mock MCP 10-K report retrieved")
            print(f"   Company: {report['company_name']}")
            print(f"   Section: {report['section']}")
        else:
            print(f"❌ Mock MCP 10-K report failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Mock MCP server error: {e}")

def test_verification_status(job_id):
    """Test verification status endpoint"""
    if not job_id:
        return
        
    print(f"\nTesting verification status for {job_id}...")
    try:
        response = requests.get(f"{MCP_API_URL}/research/{job_id}/verification-status")
        if response.status_code == 200:
            status = response.json()
            print("✅ Verification status retrieved successfully")
            print(f"   Thesis approved: {status['thesis_approved']}")
            print(f"   Antithesis approved: {status['antithesis_approved']}")
            print(f"   Can proceed to synthesis: {status['can_proceed_to_synthesis']}")
        else:
            print(f"❌ Verification status failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Verification status error: {e}")

def main():
    """Run all tests"""
    print("🧪 Testing MCP Implementation")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"MCP API URL: {MCP_API_URL}")
    print(f"Mock MCP URL: {MOCK_MCP_URL}")
    print("=" * 50)
    
    # Test basic functionality
    test_health_check()
    test_available_tools()
    test_tool_execution()
    test_mock_mcp_server()
    
    # Test research workflow
    job_id = test_research_job_creation()
    if job_id:
        test_job_status(job_id)
        test_verification_status(job_id)
        
        # Wait a bit and check status again
        print(f"\nWaiting 5 seconds before checking status again...")
        time.sleep(5)
        test_job_status(job_id)
    
    print("\n" + "=" * 50)
    print("🏁 Testing completed")
    print("=" * 50)

if __name__ == "__main__":
    main() 