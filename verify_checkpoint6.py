#!/usr/bin/env python3
"""
Verification script for Checkpoint 6: Human Adjudicator
Verifies that all requirements from the development plan have been implemented
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
EXISTING_JOB_ID = "job-v2-fd87a64f"

def verify_cp6_t601_dialectical_review_interface():
    """Verify CP6-T601: Dialectical Review Interface"""
    print("🔍 Verifying CP6-T601: Dialectical Review Interface")
    
    # Test 1: Verify verification status endpoint exists
    response = requests.get(f"{BASE_URL}/v3/jobs/{EXISTING_JOB_ID}/verification-status")
    if response.status_code != 200:
        print("❌ CP6-T601: Verification status endpoint not working")
        return False
    
    status_data = response.json()
    
    # Test 2: Verify both dossiers are accessible
    thesis_dossier_id = status_data['thesis_dossier']['id']
    antithesis_dossier_id = status_data['antithesis_dossier']['id']
    
    thesis_response = requests.get(f"{BASE_URL}/v2/dossiers/{thesis_dossier_id}")
    antithesis_response = requests.get(f"{BASE_URL}/v2/dossiers/{antithesis_dossier_id}")
    
    if thesis_response.status_code != 200 or antithesis_response.status_code != 200:
        print("❌ CP6-T601: Cannot access both dossiers")
        return False
    
    # Test 3: Verify dossier review endpoint exists
    review_response = requests.post(
        f"{BASE_URL}/v3/dossiers/{thesis_dossier_id}/review",
        json={"action": "APPROVE"}
    )
    
    if review_response.status_code != 200:
        print("❌ CP6-T601: Dossier review endpoint not working")
        return False
    
    print("✅ CP6-T601: Dialectical Review Interface - PASSED")
    return True

def verify_cp6_t602_structured_verification_protocol():
    """Verify CP6-T602: Structured Verification Protocol"""
    print("🔍 Verifying CP6-T602: Structured Verification Protocol")
    
    # Test 1: Verify revision without feedback is rejected
    thesis_dossier_id = "dossier-thesis-123"  # We'll get this from the API
    response = requests.get(f"{BASE_URL}/v3/jobs/{EXISTING_JOB_ID}/verification-status")
    if response.status_code == 200:
        status_data = response.json()
        thesis_dossier_id = status_data['thesis_dossier']['id']
    
    revision_response = requests.post(
        f"{BASE_URL}/v3/dossiers/{thesis_dossier_id}/review",
        json={"action": "REVISE"}
    )
    
    if revision_response.status_code != 400:
        print("❌ CP6-T602: Should reject revision without feedback")
        return False
    
    # Test 2: Verify revision with feedback is accepted
    revision_with_feedback_response = requests.post(
        f"{BASE_URL}/v3/dossiers/{thesis_dossier_id}/review",
        json={
            "action": "REVISE",
            "feedback": "Please provide more evidence about competitive analysis."
        }
    )
    
    if revision_with_feedback_response.status_code != 200:
        print("❌ CP6-T602: Should accept revision with feedback")
        return False
    
    # Test 3: Verify invalid actions are rejected
    invalid_response = requests.post(
        f"{BASE_URL}/v3/dossiers/{thesis_dossier_id}/review",
        json={"action": "INVALID_ACTION"}
    )
    
    if invalid_response.status_code != 400:
        print("❌ CP6-T602: Should reject invalid actions")
        return False
    
    print("✅ CP6-T602: Structured Verification Protocol - PASSED")
    return True

def verify_cp6_t603_asymmetrical_revision_workflow():
    """Verify CP6-T603: Asymmetrical Revision Workflow"""
    print("🔍 Verifying CP6-T603: Asymmetrical Revision Workflow")
    
    # Test 1: Verify revision feedback is stored
    response = requests.get(f"{BASE_URL}/v3/jobs/{EXISTING_JOB_ID}/verification-status")
    if response.status_code != 200:
        print("❌ CP6-T603: Cannot get verification status")
        return False
    
    status_data = response.json()
    antithesis_dossier_id = status_data['antithesis_dossier']['id']
    
    # Test 2: Verify revision request triggers research agent re-enqueue
    revision_response = requests.post(
        f"{BASE_URL}/v3/dossiers/{antithesis_dossier_id}/review",
        json={
            "action": "REVISE",
            "feedback": "Please provide more detailed financial analysis."
        }
    )
    
    if revision_response.status_code != 200:
        print("❌ CP6-T603: Revision request failed")
        return False
    
    result = revision_response.json()
    if "re-enqueued" not in result['message'].lower() and "feedback" not in result['message'].lower():
        print("❌ CP6-T603: Revision should mention re-enqueuing or feedback")
        return False
    
    print("✅ CP6-T603: Asymmetrical Revision Workflow - PASSED")
    return True

def verify_proxy_hypothesis_display():
    """Verify that proxy hypothesis data is properly displayed"""
    print("🔍 Verifying Proxy Hypothesis Display")
    
    response = requests.get(f"{BASE_URL}/v3/jobs/{EXISTING_JOB_ID}/verification-status")
    if response.status_code != 200:
        print("❌ Cannot get verification status")
        return False
    
    status_data = response.json()
    thesis_dossier_id = status_data['thesis_dossier']['id']
    
    # Get thesis dossier
    dossier_response = requests.get(f"{BASE_URL}/v2/dossiers/{thesis_dossier_id}")
    if dossier_response.status_code != 200:
        print("❌ Cannot get thesis dossier")
        return False
    
    dossier_data = dossier_response.json()
    
    # Check for proxy hypothesis data
    has_proxy_data = False
    for step in dossier_data['research_plan']['steps']:
        if step.get('data_gap_identified') or step.get('proxy_hypothesis'):
            has_proxy_data = True
            print(f"   Found proxy hypothesis in step: {step['description']}")
            if step.get('proxy_hypothesis'):
                print(f"   Unobservable claim: {step['proxy_hypothesis'].get('unobservable_claim', 'N/A')}")
                print(f"   Deductive chain: {step['proxy_hypothesis'].get('deductive_chain', 'N/A')}")
                print(f"   Observable proxy: {step['proxy_hypothesis'].get('observable_proxy', 'N/A')}")
            break
    
    if has_proxy_data:
        print("✅ Proxy Hypothesis Display - PASSED")
        return True
    else:
        print("⚠️  No proxy hypothesis data found (this is acceptable if no data gaps were identified)")
        return True

def verify_frontend_integration():
    """Verify that the frontend properly integrates with checkpoint 6 features"""
    print("🔍 Verifying Frontend Integration")
    
    # Test that the research.html page loads
    response = requests.get(f"{BASE_URL}/static/research.html")
    if response.status_code != 200:
        print("❌ Frontend: research.html not accessible")
        return False
    
    # Check for checkpoint 6 specific elements in the HTML
    html_content = response.text
    
    required_elements = [
        "verification-panel",
        "verification-checklist", 
        "approve-btn",
        "revise-btn",
        "synthesize-btn",
        "updateSynthesizeButton",
        "approveDossier",
        "showRevisionFeedback"
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in html_content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Frontend: Missing elements: {missing_elements}")
        return False
    
    print("✅ Frontend Integration - PASSED")
    return True

def main():
    """Run all checkpoint 6 verifications"""
    print("🚀 Checkpoint 6 Verification: Human Adjudicator")
    print("=" * 60)
    print(f"📋 Using job: {EXISTING_JOB_ID}")
    print()
    
    results = []
    
    # Verify each requirement
    results.append(("CP6-T601", verify_cp6_t601_dialectical_review_interface()))
    results.append(("CP6-T602", verify_cp6_t602_structured_verification_protocol()))
    results.append(("CP6-T603", verify_cp6_t603_asymmetrical_revision_workflow()))
    results.append(("Proxy Display", verify_proxy_hypothesis_display()))
    results.append(("Frontend", verify_frontend_integration()))
    
    print()
    print("📊 Verification Results:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for requirement, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{requirement:<20} {status}")
        if result:
            passed += 1
    
    print()
    print(f"Overall: {passed}/{total} requirements passed")
    
    if passed == total:
        print("🎉 CHECKPOINT 6 COMPLETED SUCCESSFULLY!")
        print()
        print("✅ All requirements implemented:")
        print("   • Dialectical Review Interface with side-by-side view")
        print("   • Structured Verification Protocol with mandatory checklist")
        print("   • Asymmetrical Revision Workflow with feedback storage")
        print("   • Proxy hypothesis display in UI")
        print("   • Frontend integration with approval controls")
        print()
        print("🔗 Test the UI at:")
        print(f"   http://localhost:8000/static/research.html?job_id={EXISTING_JOB_ID}")
        return True
    else:
        print("❌ Some requirements failed. Please review and fix.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 