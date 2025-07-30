#!/usr/bin/env python3
"""
Test script for LLM request tracking functionality
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_llm_tracking():
    """Test the complete LLM tracking workflow"""
    
    print("=== Testing LLM Request Tracking ===\n")
    
    # Test 1: Create a research job
    print("1. Creating a research job...")
    query = "Should we invest in artificial intelligence companies?"
    
    response = requests.post(
        f"{BASE_URL}/v2/research",
        json={"query": query}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create job: {response.status_code}")
        return False
    
    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✅ Job created with ID: {job_id}")
    
    # Test 2: Check LLM requests immediately after job creation
    print("\n2. Checking initial LLM requests...")
    response = requests.get(f"{BASE_URL}/v2/research/{job_id}/llm-requests")
    
    if response.status_code != 200:
        print(f"❌ Failed to get LLM requests: {response.status_code}")
        return False
    
    llm_data = response.json()
    print(f"✅ LLM requests retrieved")
    print(f"   Pending: {len(llm_data['pending_requests'])}")
    print(f"   In Progress: {len(llm_data['in_progress_requests'])}")
    print(f"   Completed: {len(llm_data['completed_requests'])}")
    print(f"   Failed: {len(llm_data['failed_requests'])}")
    
    # Test 3: Monitor LLM requests as they progress
    print("\n3. Monitoring LLM requests progress...")
    max_wait = 120  # 2 minutes max wait
    wait_time = 0
    last_total = 0
    
    while wait_time < max_wait:
        response = requests.get(f"{BASE_URL}/v2/research/{job_id}/llm-requests")
        if response.status_code == 200:
            llm_data = response.json()
            total_requests = (len(llm_data['pending_requests']) + 
                            len(llm_data['in_progress_requests']) + 
                            len(llm_data['completed_requests']) + 
                            len(llm_data['failed_requests']))
            
            if total_requests != last_total:
                print(f"   Time {wait_time}s: Pending={len(llm_data['pending_requests'])}, "
                      f"In Progress={len(llm_data['in_progress_requests'])}, "
                      f"Completed={len(llm_data['completed_requests'])}, "
                      f"Failed={len(llm_data['failed_requests'])}")
                last_total = total_requests
            
            # Check if we have some completed requests
            if len(llm_data['completed_requests']) > 0:
                print("✅ LLM requests are being processed!")
                break
        
        time.sleep(5)
        wait_time += 5
    
    if wait_time >= max_wait:
        print("❌ Timeout waiting for LLM requests to be processed")
        return False
    
    # Test 4: Check job status
    print("\n4. Checking job status...")
    response = requests.get(f"{BASE_URL}/v2/research/{job_id}/status")
    
    if response.status_code == 200:
        status_data = response.json()
        print(f"✅ Job status: {status_data['status']}")
        
        if status_data['status'] == 'AWAITING_VERIFICATION':
            print("✅ Job completed successfully!")
        else:
            print(f"   Job still processing: {status_data['status']}")
    
    # Test 5: Show final LLM request summary
    print("\n5. Final LLM request summary...")
    response = requests.get(f"{BASE_URL}/v2/research/{job_id}/llm-requests")
    
    if response.status_code == 200:
        llm_data = response.json()
        print(f"✅ Final LLM request counts:")
        print(f"   Pending: {len(llm_data['pending_requests'])}")
        print(f"   In Progress: {len(llm_data['in_progress_requests'])}")
        print(f"   Completed: {len(llm_data['completed_requests'])}")
        print(f"   Failed: {len(llm_data['failed_requests'])}")
        
        # Show some details of completed requests
        if llm_data['completed_requests']:
            print(f"\n   Sample completed request:")
            req = llm_data['completed_requests'][0]
            print(f"   Type: {req['request_type']}")
            print(f"   Prompt: {req['prompt'][:100]}...")
            print(f"   Response: {req['response'][:100] if req['response'] else 'None'}...")
    
    print("\n✅ LLM request tracking test completed successfully!")
    return True

if __name__ == "__main__":
    test_llm_tracking() 