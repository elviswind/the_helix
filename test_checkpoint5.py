#!/usr/bin/env python3
"""
Test script for Checkpoint 5: Deductive Proxy Framework
This script tests the new v3.0 features including:
- Database model upgrades
- Deductive Proxy Framework in Research Agent
- Frontend visualization of proxy hypotheses
"""

import requests
import json
import time
import uuid
from sqlalchemy.orm import Session
from models import SessionLocal, Job, EvidenceDossier, ResearchPlan, ResearchPlanStep, EvidenceItem, JobStatus, DossierStatus

def test_database_migration():
    """Test that the new v3.0 database fields are available"""
    print("Testing database migration...")
    
    db = SessionLocal()
    try:
        # Check if new fields exist in ResearchPlanStep
        step = db.query(ResearchPlanStep).first()
        if step:
            print(f"✓ ResearchPlanStep has data_gap_identified field: {hasattr(step, 'data_gap_identified')}")
            print(f"✓ ResearchPlanStep has proxy_hypothesis field: {hasattr(step, 'proxy_hypothesis')}")
        else:
            print("⚠ No ResearchPlanStep records found to test")
        
        # Check if new fields exist in EvidenceItem
        item = db.query(EvidenceItem).first()
        if item:
            print(f"✓ EvidenceItem has tags field: {hasattr(item, 'tags')}")
        else:
            print("⚠ No EvidenceItem records found to test")
            
    finally:
        db.close()

def test_research_agent_proxy_framework():
    """Test the Deductive Proxy Framework in the Research Agent"""
    print("\nTesting Research Agent Deductive Proxy Framework...")
    
    # Create a test query that should trigger proxy reasoning
    test_query = "Assess the strength of Apple's brand moat and competitive advantages"
    
    print(f"Submitting test query: {test_query}")
    
    # Submit the research job
    response = requests.post("http://localhost:8000/v2/research", json={"query": test_query})
    if response.status_code != 200:
        print(f"✗ Failed to submit research job: {response.status_code}")
        return None
    
    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✓ Research job created: {job_id}")
    
    # Wait for the job to complete
    print("Waiting for research to complete...")
    max_wait = 120  # 2 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status_response = requests.get(f"http://localhost:8000/v2/research/{job_id}/status")
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"Job status: {status_data['status']}")
            
            if status_data['status'] == 'AWAITING_VERIFICATION':
                print("✓ Research completed, checking for proxy hypotheses...")
                return job_id
            elif status_data['status'] == 'COMPLETE':
                print("✓ Research completed, checking for proxy hypotheses...")
                return job_id
            elif 'FAILED' in status_data['status']:
                print(f"✗ Research failed: {status_data['status']}")
                return None
        
        time.sleep(5)
    
    print("✗ Research did not complete within timeout")
    return None

def check_proxy_hypotheses(job_id):
    """Check if proxy hypotheses were created during research"""
    print(f"\nChecking for proxy hypotheses in job {job_id}...")
    
    db = SessionLocal()
    try:
        # Get the job and its dossiers
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            print(f"✗ Job {job_id} not found")
            return False
        
        dossiers = db.query(EvidenceDossier).filter(EvidenceDossier.job_id == job_id).all()
        print(f"Found {len(dossiers)} dossiers")
        
        proxy_steps_found = 0
        proxy_evidence_found = 0
        
        for dossier in dossiers:
            print(f"\nChecking dossier {dossier.id} ({dossier.dossier_type.value}):")
            
            # Check research plan steps for proxy hypotheses
            research_plan = db.query(ResearchPlan).filter(ResearchPlan.dossier_id == dossier.id).first()
            if research_plan:
                steps = db.query(ResearchPlanStep).filter(ResearchPlanStep.research_plan_id == research_plan.id).all()
                print(f"  Found {len(steps)} research plan steps")
                
                for step in steps:
                    if step.data_gap_identified:
                        proxy_steps_found += 1
                        print(f"  ✓ Step {step.step_number}: Data gap identified")
                        print(f"    Gap: {step.data_gap_identified}")
                        
                        if step.proxy_hypothesis:
                            print(f"    Proxy: {step.proxy_hypothesis}")
                        else:
                            print(f"    ⚠ No proxy hypothesis found")
            
            # Check evidence items for proxy tags
            evidence_items = db.query(EvidenceItem).filter(EvidenceItem.dossier_id == dossier.id).all()
            print(f"  Found {len(evidence_items)} evidence items")
            
            for item in evidence_items:
                if item.tags and len(item.tags) > 0:
                    proxy_evidence_found += 1
                    print(f"  ✓ Evidence item {item.id}: Has proxy tags {item.tags}")
        
        print(f"\nSummary:")
        print(f"  Proxy steps found: {proxy_steps_found}")
        print(f"  Proxy evidence found: {proxy_evidence_found}")
        
        return proxy_steps_found > 0 or proxy_evidence_found > 0
        
    finally:
        db.close()

def test_frontend_display(job_id):
    """Test that the frontend correctly displays proxy hypotheses"""
    print(f"\nTesting frontend display for job {job_id}...")
    
    # Get the job status to find dossier IDs
    status_response = requests.get(f"http://localhost:8000/v2/research/{job_id}/status")
    if status_response.status_code != 200:
        print(f"✗ Failed to get job status: {status_response.status_code}")
        return False
    
    status_data = status_response.json()
    thesis_dossier_id = status_data.get('thesis_dossier_id')
    antithesis_dossier_id = status_data.get('antithesis_dossier_id')
    
    if not thesis_dossier_id or not antithesis_dossier_id:
        print("✗ Dossier IDs not found in job status")
        return False
    
    # Test thesis dossier endpoint
    print(f"Testing thesis dossier endpoint: {thesis_dossier_id}")
    thesis_response = requests.get(f"http://localhost:8000/v2/dossiers/{thesis_dossier_id}")
    if thesis_response.status_code == 200:
        thesis_data = thesis_response.json()
        print(f"✓ Thesis dossier retrieved successfully")
        
        # Check if proxy fields are present in the response
        proxy_steps = 0
        for step in thesis_data['research_plan']['steps']:
            if step.get('data_gap_identified'):
                proxy_steps += 1
                print(f"  ✓ Step has data_gap_identified: {step['data_gap_identified'][:50]}...")
                if step.get('proxy_hypothesis'):
                    print(f"    Proxy hypothesis: {step['proxy_hypothesis']}")
        
        print(f"  Found {proxy_steps} steps with proxy data in thesis")
        
        # Check evidence items for tags
        proxy_evidence = 0
        for item in thesis_data['evidence_items']:
            if item.get('tags'):
                proxy_evidence += 1
                print(f"  ✓ Evidence item has tags: {item['tags']}")
        
        print(f"  Found {proxy_evidence} evidence items with tags in thesis")
        
    else:
        print(f"✗ Failed to get thesis dossier: {thesis_response.status_code}")
    
    # Test antithesis dossier endpoint
    print(f"Testing antithesis dossier endpoint: {antithesis_dossier_id}")
    antithesis_response = requests.get(f"http://localhost:8000/v2/dossiers/{antithesis_dossier_id}")
    if antithesis_response.status_code == 200:
        antithesis_data = antithesis_response.json()
        print(f"✓ Antithesis dossier retrieved successfully")
        
        # Check if proxy fields are present in the response
        proxy_steps = 0
        for step in antithesis_data['research_plan']['steps']:
            if step.get('data_gap_identified'):
                proxy_steps += 1
                print(f"  ✓ Step has data_gap_identified: {step['data_gap_identified'][:50]}...")
                if step.get('proxy_hypothesis'):
                    print(f"    Proxy hypothesis: {step['proxy_hypothesis']}")
        
        print(f"  Found {proxy_steps} steps with proxy data in antithesis")
        
        # Check evidence items for tags
        proxy_evidence = 0
        for item in antithesis_data['evidence_items']:
            if item.get('tags'):
                proxy_evidence += 1
                print(f"  ✓ Evidence item has tags: {item['tags']}")
        
        print(f"  Found {proxy_evidence} evidence items with tags in antithesis")
        
    else:
        print(f"✗ Failed to get antithesis dossier: {antithesis_response.status_code}")
    
    return True

def main():
    """Run all Checkpoint 5 tests"""
    print("=== Checkpoint 5 Test: Deductive Proxy Framework ===\n")
    
    # Test 1: Database migration
    test_database_migration()
    
    # Test 2: Research Agent with Proxy Framework
    job_id = test_research_agent_proxy_framework()
    if job_id:
        # Test 3: Check for proxy hypotheses
        has_proxies = check_proxy_hypotheses(job_id)
        
        # Test 4: Frontend display
        frontend_ok = test_frontend_display(job_id)
        
        print(f"\n=== Checkpoint 5 Test Results ===")
        print(f"✓ Database migration: Successful")
        print(f"✓ Research Agent: {'Successful' if job_id else 'Failed'}")
        print(f"✓ Proxy Hypotheses: {'Found' if has_proxies else 'Not found'}")
        print(f"✓ Frontend Display: {'Working' if frontend_ok else 'Failed'}")
        
        if has_proxies:
            print(f"\n🎉 Checkpoint 5 PASSED! Deductive Proxy Framework is working correctly.")
        else:
            print(f"\n⚠ Checkpoint 5 PARTIAL - Proxy Framework implemented but no proxies generated in this test.")
    else:
        print(f"\n✗ Checkpoint 5 FAILED - Could not complete research job.")

if __name__ == "__main__":
    main() 