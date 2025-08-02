#!/usr/bin/env python3
"""
Quick test script for Checkpoint 6 using existing job
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
EXISTING_JOB_ID = "job-v2-fd87a64f"  # Job that's already in AWAITING_VERIFICATION

def test_verification_status_endpoint(job_id):
    """Test the verification status endpoint"""
    print("🧪 Testing verification status endpoint...")
    
    response = requests.get(f"{BASE_URL}/v3/jobs/{job_id}/verification-status")
    
    if response.status_code == 200:
        status_data = response.json()
        print("✅ Verification status retrieved successfully:")
        print(f"   Job status: {status_data['job_status']}")
        print(f"   Thesis status: {status_data['thesis_dossier']['status']}")
        print(f"   Antithesis status: {status_data['antithesis_dossier']['status']}")
        return status_data
    else:
        print(f"❌ Failed to get verification status: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_dossier_approval(job_id, status_data):
    """Test approving a dossier"""
    print("🧪 Testing dossier approval...")
    
    # Get thesis dossier ID
    thesis_dossier_id = status_data['thesis_dossier']['id']
    
    # Test approval
    response = requests.post(
        f"{BASE_URL}/v3/dossiers/{thesis_dossier_id}/review",
        json={"action": "APPROVE"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Thesis dossier approved: {result['message']}")
        return True
    else:
        print(f"❌ Failed to approve thesis dossier: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_dossier_revision(job_id, status_data):
    """Test requesting a dossier revision"""
    print("🧪 Testing dossier revision request...")
    
    # Get antithesis dossier ID
    antithesis_dossier_id = status_data['antithesis_dossier']['id']
    
    # Test revision request
    revision_feedback = "Please provide more evidence about competitive threats and market share analysis."
    response = requests.post(
        f"{BASE_URL}/v3/dossiers/{antithesis_dossier_id}/review",
        json={
            "action": "REVISE",
            "feedback": revision_feedback
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Revision requested: {result['message']}")
        return True
    else:
        print(f"❌ Failed to request revision: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_invalid_review_actions(job_id, status_data):
    """Test invalid review actions"""
    print("🧪 Testing invalid review actions...")
    
    thesis_dossier_id = status_data['thesis_dossier']['id']
    
    # Test revision without feedback
    response = requests.post(
        f"{BASE_URL}/v3/dossiers/{thesis_dossier_id}/review",
        json={"action": "REVISE"}
    )
    
    if response.status_code == 400:
        print("✅ Correctly rejected revision without feedback")
    else:
        print(f"❌ Should have rejected revision without feedback: {response.status_code}")
    
    # Test invalid action
    response = requests.post(
        f"{BASE_URL}/v3/dossiers/{thesis_dossier_id}/review",
        json={"action": "INVALID_ACTION"}
    )
    
    if response.status_code == 400:
        print("✅ Correctly rejected invalid action")
    else:
        print(f"❌ Should have rejected invalid action: {response.status_code}")

def test_dossier_endpoints(job_id, status_data):
    """Test dossier endpoints to verify proxy hypothesis display"""
    print("🧪 Testing dossier endpoints...")
    
    thesis_dossier_id = status_data['thesis_dossier']['id']
    antithesis_dossier_id = status_data['antithesis_dossier']['id']
    
    # Test thesis dossier
    response = requests.get(f"{BASE_URL}/v2/dossiers/{thesis_dossier_id}")
    if response.status_code == 200:
        dossier_data = response.json()
        print("✅ Thesis dossier retrieved successfully")
        
        # Check for proxy hypothesis data
        has_proxy_data = False
        for step in dossier_data['research_plan']['steps']:
            if step.get('data_gap_identified') or step.get('proxy_hypothesis'):
                has_proxy_data = True
                print(f"   Found proxy hypothesis in step: {step['description']}")
                break
        
        if has_proxy_data:
            print("✅ Proxy hypothesis data found in thesis dossier")
        else:
            print("⚠️  No proxy hypothesis data found in thesis dossier")
    
    # Test antithesis dossier
    response = requests.get(f"{BASE_URL}/v2/dossiers/{antithesis_dossier_id}")
    if response.status_code == 200:
        dossier_data = response.json()
        print("✅ Antithesis dossier retrieved successfully")
        
        # Check for proxy hypothesis data
        has_proxy_data = False
        for step in dossier_data['research_plan']['steps']:
            if step.get('data_gap_identified') or step.get('proxy_hypothesis'):
                has_proxy_data = True
                print(f"   Found proxy hypothesis in step: {step['description']}")
                break
        
        if has_proxy_data:
            print("✅ Proxy hypothesis data found in antithesis dossier")
        else:
            print("⚠️  No proxy hypothesis data found in antithesis dossier")

def main():
    """Run all checkpoint 6 tests with existing job"""
    print("🚀 Starting Checkpoint 6 Tests: Human Adjudicator (Using Existing Job)")
    print("=" * 70)
    print(f"📋 Using existing job: {EXISTING_JOB_ID}")
    
    # Test 1: Test verification status endpoint
    verification_status = test_verification_status_endpoint(EXISTING_JOB_ID)
    if not verification_status:
        print("❌ Cannot continue without verification status")
        return
    
    print()
    
    # Test 2: Test dossier endpoints
    test_dossier_endpoints(EXISTING_JOB_ID, verification_status)
    
    print()
    
    # Test 3: Test dossier approval
    test_dossier_approval(EXISTING_JOB_ID, verification_status)
    
    print()
    
    # Test 4: Test dossier revision
    test_dossier_revision(EXISTING_JOB_ID, verification_status)
    
    print()
    
    # Test 5: Test invalid actions
    test_invalid_review_actions(EXISTING_JOB_ID, verification_status)
    
    print()
    print("🎉 Checkpoint 6 Tests Completed!")
    print("=" * 70)
    print("📋 Summary of implemented features:")
    print("   ✅ Dialectical Review Interface (CP6-T601)")
    print("   ✅ Structured Verification Protocol (CP6-T602)")
    print("   ✅ Asymmetrical Revision Workflow (CP6-T603)")
    print()
    print("🔗 To test the UI, visit:")
    print(f"   http://localhost:8000/static/research.html?job_id={EXISTING_JOB_ID}")

if __name__ == "__main__":
    main() 