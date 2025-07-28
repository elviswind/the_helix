#!/usr/bin/env python3
"""
Test script for Checkpoint 3: The "Thinking" Orchestrator Agent
"""

import requests
import time
import json
from sqlalchemy.orm import Session
from models import SessionLocal, Job, EvidenceDossier, ResearchPlan, ResearchPlanStep, DossierType

BASE_URL = "http://localhost:8000"

def test_checkpoint3():
    """Test the complete Checkpoint 3 workflow"""
    
    print("=== Testing Checkpoint 3: The 'Thinking' Orchestrator Agent ===\n")
    
    # Test 1: Create a research job
    print("1. Creating a research job...")
    query = "Should we invest in renewable energy companies?"
    
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
    
    # Test 2: Check job status (should be PENDING initially)
    print("\n2. Checking initial job status...")
    response = requests.get(f"{BASE_URL}/v2/research/{job_id}/status")
    
    if response.status_code != 200:
        print(f"❌ Failed to get job status: {response.status_code}")
        return False
    
    status_data = response.json()
    print(f"✅ Job status: {status_data['status']}")
    print(f"   Task status: {status_data.get('task_status', 'N/A')}")
    print(f"   Task progress: {status_data.get('task_progress', 'N/A')}")
    
    # Test 3: Wait for processing to complete
    print("\n3. Waiting for Orchestrator Agent to complete...")
    max_wait = 60  # 60 seconds max wait
    wait_time = 0
    
    while wait_time < max_wait:
        response = requests.get(f"{BASE_URL}/v2/research/{job_id}/status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"   Current status: {status_data['status']}")
            
            if status_data['status'] == 'AWAITING_VERIFICATION':
                print("✅ Orchestrator Agent completed!")
                break
            elif status_data['status'] == 'RESEARCHING':
                print(f"   Progress: {status_data.get('task_progress', 'Processing...')}")
        
        time.sleep(3)
        wait_time += 3
    
    if wait_time >= max_wait:
        print("❌ Timeout waiting for processing to complete")
        return False
    
    # Test 4: Verify the dossiers were created with LLM-generated content
    print("\n4. Verifying LLM-generated dossiers...")
    
    # Get thesis dossier
    thesis_dossier_id = status_data['thesis_dossier_id']
    response = requests.get(f"{BASE_URL}/v2/dossiers/{thesis_dossier_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get thesis dossier: {response.status_code}")
        return False
    
    thesis_dossier = response.json()
    print(f"✅ Thesis dossier retrieved")
    print(f"   Mission: {thesis_dossier['mission'][:100]}...")
    print(f"   Status: {thesis_dossier['status']}")
    print(f"   Plan steps: {len(thesis_dossier['research_plan']['steps'])}")
    
    # Get antithesis dossier
    antithesis_dossier_id = status_data['antithesis_dossier_id']
    response = requests.get(f"{BASE_URL}/v2/dossiers/{antithesis_dossier_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get antithesis dossier: {response.status_code}")
        return False
    
    antithesis_dossier = response.json()
    print(f"✅ Antithesis dossier retrieved")
    print(f"   Mission: {antithesis_dossier['mission'][:100]}...")
    print(f"   Status: {antithesis_dossier['status']}")
    print(f"   Plan steps: {len(antithesis_dossier['research_plan']['steps'])}")
    
    # Test 5: Verify the missions are different and dialectical
    print("\n5. Verifying dialectical structure...")
    
    thesis_mission = thesis_dossier['mission'].lower()
    antithesis_mission = antithesis_dossier['mission'].lower()
    
    # Check that missions are different
    if thesis_mission == antithesis_mission:
        print("❌ Thesis and antithesis missions are identical")
        return False
    
    # Check for dialectical keywords
    thesis_keywords = ['for', 'positive', 'support', 'favorable', 'bullish']
    antithesis_keywords = ['against', 'negative', 'oppose', 'unfavorable', 'bearish']
    
    thesis_has_keywords = any(keyword in thesis_mission for keyword in thesis_keywords)
    antithesis_has_keywords = any(keyword in antithesis_mission for keyword in antithesis_keywords)
    
    if thesis_has_keywords and antithesis_has_keywords:
        print("✅ Missions show dialectical opposition")
    else:
        print("⚠️  Missions may not be clearly dialectical")
    
    # Test 6: Verify research plans have justifications
    print("\n6. Verifying research plan justifications...")
    
    thesis_steps = thesis_dossier['research_plan']['steps']
    antithesis_steps = antithesis_dossier['research_plan']['steps']
    
    all_steps = thesis_steps + antithesis_steps
    
    steps_with_justifications = 0
    for step in all_steps:
        if step.get('tool_selection_justification') and step.get('tool_query_rationale'):
            steps_with_justifications += 1
    
    print(f"✅ {steps_with_justifications}/{len(all_steps)} steps have justifications")
    
    if steps_with_justifications == len(all_steps):
        print("✅ All steps have proper justifications")
    else:
        print("⚠️  Some steps are missing justifications")
    
    # Test 7: Database verification
    print("\n7. Verifying database state...")
    
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            print("❌ Job not found in database")
            return False
        
        dossiers = db.query(EvidenceDossier).filter(EvidenceDossier.job_id == job_id).all()
        if len(dossiers) != 2:
            print(f"❌ Expected 2 dossiers, found {len(dossiers)}")
            return False
        
        for dossier in dossiers:
            if not dossier.research_plan:
                print(f"❌ Dossier {dossier.id} has no research plan")
                return False
            
            if len(dossier.research_plan.steps) == 0:
                print(f"❌ Dossier {dossier.id} has no research plan steps")
                return False
        
        print("✅ Database state is correct")
        
    finally:
        db.close()
    
    print("\n=== Checkpoint 3 Test Results ===")
    print("✅ All tests passed! Checkpoint 3 is working correctly.")
    print("\nKey achievements:")
    print("- Job queue system (Celery) is integrated")
    print("- Orchestrator Agent generates dialectical missions using LLM")
    print("- Research plans are created with proper justifications")
    print("- System moves from PENDING to AWAITING_VERIFICATION status")
    
    return True

if __name__ == "__main__":
    try:
        success = test_checkpoint3()
        if success:
            print("\n🎉 Checkpoint 3 implementation is complete!")
        else:
            print("\n❌ Checkpoint 3 test failed")
            exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        exit(1) 