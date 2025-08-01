#!/usr/bin/env python3
"""
Test script to verify tool request tracking functionality.
This script tests the new tool request tracking feature.
"""

import requests
import time
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
MCP_BASE_URL = "http://localhost:8001"

def test_mcp_server_delays():
    """Test that the MCP server has delays implemented"""
    print("Testing MCP server delays...")
    
    # Test manifest endpoint
    start_time = time.time()
    response = requests.get(f"{MCP_BASE_URL}/manifest")
    manifest_time = time.time() - start_time
    
    print(f"Manifest request took {manifest_time:.2f} seconds")
    
    # Test search endpoint
    start_time = time.time()
    response = requests.post(
        f"{MCP_BASE_URL}/search",
        json={
            "query": "market growth",
            "tool_name": "market-data-api",
            "max_results": 5
        }
    )
    search_time = time.time() - start_time
    
    print(f"Search request took {search_time:.2f} seconds")
    
    if manifest_time > 0.3 and search_time > 1.5:
        print("✅ MCP server delays are working correctly")
        return True
    else:
        print("❌ MCP server delays are not working as expected")
        return False

def test_tool_request_tracking():
    """Test the complete tool request tracking flow"""
    print("\nTesting tool request tracking...")
    
    # Step 1: Create a research job
    print("1. Creating research job...")
    response = requests.post(
        f"{API_BASE_URL}/v2/research",
        json={"query": "Test tool tracking functionality"}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create job: {response.status_code}")
        return False
    
    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✅ Created job: {job_id}")
    
    # Step 2: Wait for the job to start processing
    print("2. Waiting for job to start processing...")
    max_wait = 30  # 30 seconds max wait
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{API_BASE_URL}/v2/research/{job_id}/status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"   Job status: {status_data['status']}")
            
            if status_data['status'] in ['RESEARCHING', 'AWAITING_VERIFICATION']:
                break
        
        time.sleep(2)
    
    # Step 3: Check for tool requests
    print("3. Checking for tool requests...")
    response = requests.get(f"{API_BASE_URL}/v2/research/{job_id}/tool-requests")
    
    if response.status_code != 200:
        print(f"❌ Failed to get tool requests: {response.status_code}")
        return False
    
    tool_requests = response.json()
    
    print(f"   Pending requests: {len(tool_requests['pending_requests'])}")
    print(f"   In progress requests: {len(tool_requests['in_progress_requests'])}")
    print(f"   Completed requests: {len(tool_requests['completed_requests'])}")
    print(f"   Failed requests: {len(tool_requests['failed_requests'])}")
    
    total_requests = (len(tool_requests['pending_requests']) + 
                     len(tool_requests['in_progress_requests']) + 
                     len(tool_requests['completed_requests']) + 
                     len(tool_requests['failed_requests']))
    
    if total_requests > 0:
        print("✅ Tool requests are being tracked")
        
        # Show details of some requests
        if tool_requests['completed_requests']:
            req = tool_requests['completed_requests'][0]
            print(f"   Example completed request:")
            print(f"     Tool: {req['tool_name']}")
            print(f"     Type: {req['request_type']}")
            print(f"     Query: {req['query']}")
            print(f"     Duration: {req['started_at']} to {req['completed_at']}")
        
        return True
    else:
        print("❌ No tool requests found")
        return False

def test_llm_request_tracking():
    """Test that LLM request tracking is still working"""
    print("\nTesting LLM request tracking...")
    
    # Get the most recent job
    response = requests.get(f"{API_BASE_URL}/v2/research/recent")
    if response.status_code != 200:
        print("❌ Could not get recent jobs")
        return False
    
    jobs = response.json()
    if not jobs:
        print("❌ No jobs found")
        return False
    
    job_id = jobs[0]["id"]
    
    # Check LLM requests
    response = requests.get(f"{API_BASE_URL}/v2/research/{job_id}/llm-requests")
    if response.status_code != 200:
        print(f"❌ Failed to get LLM requests: {response.status_code}")
        return False
    
    llm_requests = response.json()
    
    print(f"   Pending LLM requests: {len(llm_requests['pending_requests'])}")
    print(f"   In progress LLM requests: {len(llm_requests['in_progress_requests'])}")
    print(f"   Completed LLM requests: {len(llm_requests['completed_requests'])}")
    print(f"   Failed LLM requests: {len(llm_requests['failed_requests'])}")
    
    total_llm_requests = (len(llm_requests['pending_requests']) + 
                         len(llm_requests['in_progress_requests']) + 
                         len(llm_requests['completed_requests']) + 
                         len(llm_requests['failed_requests']))
    
    if total_llm_requests > 0:
        print("✅ LLM request tracking is working")
        return True
    else:
        print("❌ No LLM requests found")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Tool Request Tracking Feature")
    print("=" * 50)
    
    # Test 1: MCP server delays
    delays_ok = test_mcp_server_delays()
    
    # Test 2: Tool request tracking
    tracking_ok = test_tool_request_tracking()
    
    # Test 3: LLM request tracking (should still work)
    llm_ok = test_llm_request_tracking()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   MCP Server Delays: {'✅ PASS' if delays_ok else '❌ FAIL'}")
    print(f"   Tool Request Tracking: {'✅ PASS' if tracking_ok else '❌ FAIL'}")
    print(f"   LLM Request Tracking: {'✅ PASS' if llm_ok else '❌ FAIL'}")
    
    if delays_ok and tracking_ok and llm_ok:
        print("\n🎉 All tests passed! Tool request tracking is working correctly.")
        return True
    else:
        print("\n💥 Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 