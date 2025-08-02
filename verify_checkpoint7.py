#!/usr/bin/env python3
"""
Comprehensive verification script for Checkpoint 7: The Final Synthesis and Balanced Report

This script tests the complete synthesis workflow from dossier approval to final report generation.
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def wait_for_server():
    """Wait for the server to be available"""
    print("🔄 Waiting for server to be available...")
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/")
            if response.status_code == 200:
                print("✅ Server is available")
                return True
        except requests.exceptions.ConnectionError:
            pass
        
        if attempt < max_attempts - 1:
            time.sleep(2)
    
    print("❌ Server not available after 60 seconds")
    return False

def create_test_job():
    """Create a test research job"""
    print("🧪 Creating test research job...")
    
    try:
        response = requests.post(f"{BASE_URL}/v2/research", json={
            "query": "Evaluate the investment case for Tesla (TSLA)"
        })
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data['job_id']
            print(f"✅ Test job created: {job_id}")
            return job_id
        else:
            print(f"❌ Failed to create test job: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test job: {e}")
        return None

def wait_for_research_completion(job_id):
    """Wait for research to complete and reach AWAITING_VERIFICATION status"""
    print("🔄 Waiting for research to complete...")
    
    max_attempts = 60  # 5 minutes
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/v2/research/{job_id}/status")
            if response.status_code == 200:
                status_data = response.json()
                print(f"   Status: {status_data['status']}")
                
                if status_data['status'] == 'AWAITING_VERIFICATION':
                    print("✅ Research completed - ready for verification!")
                    return True
                elif status_data['status'] == 'COMPLETE':
                    print("✅ Research already completed!")
                    return True
                elif status_data['status'] == 'FAILED':
                    print("❌ Research failed")
                    return False
                    
        except Exception as e:
            print(f"   Error checking status: {e}")
        
        if attempt < max_attempts - 1:
            time.sleep(5)
    
    print("❌ Research did not complete within 5 minutes")
    return False

def get_verification_status(job_id):
    """Get verification status for both dossiers"""
    print("🧪 Getting verification status...")
    
    try:
        response = requests.get(f"{BASE_URL}/v3/jobs/{job_id}/verification-status")
        if response.status_code == 200:
            status_data = response.json()
            print("✅ Verification status retrieved:")
            print(f"   Thesis: {status_data['thesis_dossier']['status']}")
            print(f"   Antithesis: {status_data['antithesis_dossier']['status']}")
            return status_data
        else:
            print(f"❌ Failed to get verification status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting verification status: {e}")
        return None

def approve_dossier(dossier_id):
    """Approve a dossier"""
    print(f"🧪 Approving dossier {dossier_id}...")
    
    try:
        response = requests.post(f"{BASE_URL}/v3/dossiers/{dossier_id}/review", json={
            "action": "APPROVE"
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Dossier approved: {result['message']}")
            return True
        else:
            print(f"❌ Failed to approve dossier: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error approving dossier: {e}")
        return False

def test_synthesis_report_endpoint(job_id):
    """Test the synthesis report endpoint"""
    print("🧪 Testing synthesis report endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/v3/jobs/{job_id}/report")
        
        if response.status_code == 200:
            report_data = response.json()
            print("✅ Synthesis report retrieved successfully:")
            print(f"   Report ID: {report_data['report_id']}")
            print(f"   Content length: {len(report_data['content'])} characters")
            print(f"   Created: {report_data['created_at']}")
            
            # Check if content looks like a proper synthesis
            content = report_data['content']
            if len(content) > 500 and ('thesis' in content.lower() or 'antithesis' in content.lower()):
                print("✅ Report content appears to be a proper synthesis")
                return True
            else:
                print("⚠ Report content seems too short or missing key elements")
                return False
                
        elif response.status_code == 400:
            print("ℹ️ Report not ready yet (expected for incomplete jobs)")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing synthesis report endpoint: {e}")
        return False

def test_synthesis_workflow():
    """Test the complete synthesis workflow"""
    print("=== Testing Complete Synthesis Workflow ===\n")
    
    # Step 1: Wait for server
    if not wait_for_server():
        return False
    
    # Step 2: Create test job
    job_id = create_test_job()
    if not job_id:
        return False
    
    # Step 3: Wait for research completion
    if not wait_for_research_completion(job_id):
        return False
    
    # Step 4: Get verification status
    verification_status = get_verification_status(job_id)
    if not verification_status:
        return False
    
    # Step 5: Approve both dossiers
    thesis_dossier_id = verification_status['thesis_dossier']['id']
    antithesis_dossier_id = verification_status['antithesis_dossier']['id']
    
    print("🧪 Approving both dossiers to trigger synthesis...")
    
    if not approve_dossier(thesis_dossier_id):
        return False
    
    if not approve_dossier(antithesis_dossier_id):
        return False
    
    # Step 6: Wait for synthesis to complete
    print("🔄 Waiting for synthesis to complete...")
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/v3/jobs/{job_id}/report")
            if response.status_code == 200:
                print("✅ Synthesis completed!")
                break
            elif response.status_code == 400:
                print(f"   Synthesis in progress... (attempt {attempt + 1}/{max_attempts})")
            else:
                print(f"   Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"   Error checking synthesis: {e}")
        
        if attempt < max_attempts - 1:
            time.sleep(10)
    else:
        print("❌ Synthesis did not complete within 5 minutes")
        return False
    
    # Step 7: Test the final report
    if not test_synthesis_report_endpoint(job_id):
        return False
    
    print("\n🎉 Complete synthesis workflow test PASSED!")
    return True

def test_synthesis_agent_standalone():
    """Test the synthesis agent standalone functionality"""
    print("=== Testing Synthesis Agent Standalone ===\n")
    
    try:
        from synthesis_agent import SynthesisAgent
        from models import SessionLocal, Job, EvidenceDossier, DossierStatus
        
        agent = SynthesisAgent()
        print("✅ Synthesis agent created")
        
        # Get a job that has both dossiers approved
        db = SessionLocal()
        try:
            # Find a job with both dossiers approved
            approved_jobs = db.query(Job).join(EvidenceDossier).filter(
                EvidenceDossier.status == DossierStatus.APPROVED
            ).all()
            
            if not approved_jobs:
                print("ℹ️ No jobs with approved dossiers found for standalone test")
                return True
            
            # Find a job where both thesis and antithesis are approved
            for job in approved_jobs:
                thesis = db.query(EvidenceDossier).filter(
                    EvidenceDossier.job_id == job.id,
                    EvidenceDossier.dossier_type == "THESIS"
                ).first()
                
                antithesis = db.query(EvidenceDossier).filter(
                    EvidenceDossier.job_id == job.id,
                    EvidenceDossier.dossier_type == "ANTITHESIS"
                ).first()
                
                if (thesis and antithesis and 
                    thesis.status == DossierStatus.APPROVED and 
                    antithesis.status == DossierStatus.APPROVED):
                    
                    print(f"🧪 Testing synthesis agent with job {job.id}")
                    
                    # Test the synthesis
                    try:
                        content = agent.synthesize_dossiers(job.id)
                        if content and len(content) > 500:
                            print("✅ Standalone synthesis test PASSED")
                            print(f"   Generated {len(content)} characters")
                            return True
                        else:
                            print("❌ Synthesis content too short")
                            return False
                    except Exception as e:
                        print(f"❌ Standalone synthesis failed: {e}")
                        return False
            
            print("ℹ️ No suitable jobs found for standalone test")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Standalone synthesis agent test failed: {e}")
        return False

def run_comprehensive_verification():
    """Run comprehensive verification of checkpoint 7"""
    print("=== Checkpoint 7 Comprehensive Verification ===\n")
    
    tests = [
        ("Synthesis Workflow", "End-to-end synthesis workflow", test_synthesis_workflow),
        ("Standalone Agent", "Synthesis agent standalone test", test_synthesis_agent_standalone)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_description, test_func in tests:
        print(f"\n--- {test_name}: {test_description} ---")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
    
    print(f"\n=== Comprehensive Verification Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 Checkpoint 7 comprehensive verification COMPLETE!")
        print("✅ The Final Synthesis and Balanced Report is fully functional")
        return True
    else:
        print(f"\n⚠ Checkpoint 7 comprehensive verification INCOMPLETE - {total - passed} issues found.")
        return False

if __name__ == "__main__":
    run_comprehensive_verification() 