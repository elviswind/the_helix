#!/usr/bin/env python3
"""
Test script for Checkpoint 2 implementation
Tests the database-backed endpoints and canned research process
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_checkpoint2():
    print("🧪 Testing Checkpoint 2: Database-Backed Endpoints with Canned Research")
    print("=" * 70)
    
    # Test 1: Create a research job
    print("\n1. Creating research job...")
    query = "Should we invest in Apple stock?"
    response = requests.post(
        f"{BASE_URL}/v2/research",
        json={"query": query},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create job: {response.status_code}")
        return False
    
    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✅ Job created: {job_id}")
    
    # Test 2: Check job status (should be RESEARCHING initially)
    print("\n2. Checking initial job status...")
    response = requests.get(f"{BASE_URL}/v2/research/{job_id}/status")
    
    if response.status_code != 200:
        print(f"❌ Failed to get job status: {response.status_code}")
        return False
    
    status_data = response.json()
    print(f"✅ Initial status: {status_data['status']}")
    
    # Test 3: Wait for job completion and check final status
    print("\n3. Waiting for job completion...")
    max_wait = 30  # seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{BASE_URL}/v2/research/{job_id}/status")
        if response.status_code == 200:
            status_data = response.json()
            if status_data["status"] == "AWAITING_VERIFICATION":
                print(f"✅ Job completed: {status_data['status']}")
                break
            elif status_data["status"] == "RESEARCHING":
                print(f"⏳ Still researching... ({int(time.time() - start_time)}s)")
                time.sleep(2)
            else:
                print(f"❌ Unexpected status: {status_data['status']}")
                return False
        else:
            print(f"❌ Failed to get status: {response.status_code}")
            return False
    else:
        print("❌ Job did not complete within timeout")
        return False
    
    # Test 4: Verify dossier IDs are present
    if not status_data.get("thesis_dossier_id") or not status_data.get("antithesis_dossier_id"):
        print("❌ Missing dossier IDs in status response")
        return False
    
    thesis_dossier_id = status_data["thesis_dossier_id"]
    antithesis_dossier_id = status_data["antithesis_dossier_id"]
    print(f"✅ Thesis dossier: {thesis_dossier_id}")
    print(f"✅ Antithesis dossier: {antithesis_dossier_id}")
    
    # Test 5: Fetch thesis dossier
    print("\n4. Fetching thesis dossier...")
    response = requests.get(f"{BASE_URL}/v2/dossiers/{thesis_dossier_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get thesis dossier: {response.status_code}")
        return False
    
    thesis_data = response.json()
    print(f"✅ Thesis mission: {thesis_data['mission'][:60]}...")
    print(f"✅ Thesis status: {thesis_data['status']}")
    print(f"✅ Thesis evidence items: {len(thesis_data['evidence_items'])}")
    print(f"✅ Thesis plan steps: {len(thesis_data['research_plan']['steps'])}")
    
    # Test 6: Fetch antithesis dossier
    print("\n5. Fetching antithesis dossier...")
    response = requests.get(f"{BASE_URL}/v2/dossiers/{antithesis_dossier_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get antithesis dossier: {response.status_code}")
        return False
    
    antithesis_data = response.json()
    print(f"✅ Antithesis mission: {antithesis_data['mission'][:60]}...")
    print(f"✅ Antithesis status: {antithesis_data['status']}")
    print(f"✅ Antithesis evidence items: {len(antithesis_data['evidence_items'])}")
    print(f"✅ Antithesis plan steps: {len(antithesis_data['research_plan']['steps'])}")
    
    # Test 7: Verify data structure
    print("\n6. Verifying data structure...")
    
    # Check that both dossiers have the expected structure
    required_fields = ['dossier_id', 'mission', 'status', 'research_plan', 'evidence_items', 'summary_of_findings']
    for field in required_fields:
        if field not in thesis_data or field not in antithesis_data:
            print(f"❌ Missing required field: {field}")
            return False
    
    # Check that research plans have steps
    if not thesis_data['research_plan']['steps'] or not antithesis_data['research_plan']['steps']:
        print("❌ Research plans missing steps")
        return False
    
    # Check that evidence items exist
    if not thesis_data['evidence_items'] or not antithesis_data['evidence_items']:
        print("❌ Missing evidence items")
        return False
    
    print("✅ Data structure verification passed")
    
    # Test 8: Verify dialectical structure
    print("\n7. Verifying dialectical structure...")
    
    # Check that missions are opposing
    thesis_mission = thesis_data['mission'].lower()
    antithesis_mission = antithesis_data['mission'].lower()
    
    if 'for' not in thesis_mission or 'against' not in antithesis_mission:
        print("❌ Missions don't follow dialectical structure")
        return False
    
    # Check that evidence items have different content
    thesis_evidence_titles = [item['title'] for item in thesis_data['evidence_items']]
    antithesis_evidence_titles = [item['title'] for item in antithesis_data['evidence_items']]
    
    if set(thesis_evidence_titles) == set(antithesis_evidence_titles):
        print("❌ Evidence items are identical between dossiers")
        return False
    
    print("✅ Dialectical structure verification passed")
    
    print("\n" + "=" * 70)
    print("🎉 Checkpoint 2 Implementation Test PASSED!")
    print("✅ Database models implemented")
    print("✅ DB-backed endpoints working")
    print("✅ Canned research process functional")
    print("✅ Real dossier data from two sources")
    print("✅ Dialectical structure maintained")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    try:
        success = test_checkpoint2()
        if not success:
            print("\n❌ Checkpoint 2 test failed")
            exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        exit(1) 