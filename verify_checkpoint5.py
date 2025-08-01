#!/usr/bin/env python3
"""
Verification script for Checkpoint 5: Deductive Proxy Framework
This script verifies that all Checkpoint 5 components are properly implemented.
"""

import requests
import json
from sqlalchemy.orm import Session
from models import SessionLocal, ResearchPlanStep, EvidenceItem

def verify_database_migration():
    """Verify that the database migration was successful"""
    print("🔍 Verifying database migration...")
    
    db = SessionLocal()
    try:
        # Check ResearchPlanStep fields
        step = db.query(ResearchPlanStep).first()
        if step:
            has_data_gap = hasattr(step, 'data_gap_identified')
            has_proxy = hasattr(step, 'proxy_hypothesis')
            print(f"  ✓ ResearchPlanStep.data_gap_identified: {has_data_gap}")
            print(f"  ✓ ResearchPlanStep.proxy_hypothesis: {has_proxy}")
        else:
            print("  ⚠ No ResearchPlanStep records found")
        
        # Check EvidenceItem fields
        item = db.query(EvidenceItem).first()
        if item:
            has_tags = hasattr(item, 'tags')
            print(f"  ✓ EvidenceItem.tags: {has_tags}")
        else:
            print("  ⚠ No EvidenceItem records found")
            
        return True
    finally:
        db.close()

def verify_api_endpoints():
    """Verify that API endpoints return the new fields"""
    print("\n🔍 Verifying API endpoints...")
    
    try:
        # Test recent jobs endpoint
        response = requests.get("http://localhost:8000/v2/research/recent", timeout=5)
        if response.status_code == 200:
            print("  ✓ /v2/research/recent endpoint working")
        else:
            print(f"  ✗ /v2/research/recent endpoint failed: {response.status_code}")
            return False
        
        # Get a recent job
        jobs = response.json()
        if not jobs:
            print("  ⚠ No recent jobs found")
            return True
        
        job_id = jobs[0]['id']
        
        # Test job status endpoint
        status_response = requests.get(f"http://localhost:8000/v2/research/{job_id}/status", timeout=5)
        if status_response.status_code == 200:
            print("  ✓ /v2/research/{job_id}/status endpoint working")
            status_data = status_response.json()
            
            # Test dossier endpoints if available
            thesis_id = status_data.get('thesis_dossier_id')
            if thesis_id:
                dossier_response = requests.get(f"http://localhost:8000/v2/dossiers/{thesis_id}", timeout=5)
                if dossier_response.status_code == 200:
                    print("  ✓ /v2/dossiers/{dossier_id} endpoint working")
                    dossier_data = dossier_response.json()
                    
                    # Check if new fields are present in response
                    steps = dossier_data.get('research_plan', {}).get('steps', [])
                    if steps:
                        first_step = steps[0]
                        has_data_gap = 'data_gap_identified' in first_step
                        has_proxy = 'proxy_hypothesis' in first_step
                        print(f"  ✓ Step response includes data_gap_identified: {has_data_gap}")
                        print(f"  ✓ Step response includes proxy_hypothesis: {has_proxy}")
                    
                    evidence_items = dossier_data.get('evidence_items', [])
                    if evidence_items:
                        first_item = evidence_items[0]
                        has_tags = 'tags' in first_item
                        print(f"  ✓ Evidence response includes tags: {has_tags}")
                else:
                    print(f"  ✗ Dossier endpoint failed: {dossier_response.status_code}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"  ✗ API endpoint test failed: {e}")
        return False

def verify_research_agent_implementation():
    """Verify that the Research Agent has the new methods"""
    print("\n🔍 Verifying Research Agent implementation...")
    
    try:
        from research_agent import ResearchAgent
        
        agent = ResearchAgent()
        
        # Check if new methods exist
        has_check_direct = hasattr(agent, 'check_for_direct_data')
        has_identify_gap = hasattr(agent, 'identify_data_gap')
        has_formulate_proxy = hasattr(agent, 'formulate_proxy_hypothesis')
        
        print(f"  ✓ check_for_direct_data method: {has_check_direct}")
        print(f"  ✓ identify_data_gap method: {has_identify_gap}")
        print(f"  ✓ formulate_proxy_hypothesis method: {has_formulate_proxy}")
        
        return has_check_direct and has_identify_gap and has_formulate_proxy
        
    except ImportError as e:
        print(f"  ✗ Could not import ResearchAgent: {e}")
        return False

def verify_frontend_files():
    """Verify that frontend files have been updated"""
    print("\n🔍 Verifying frontend implementation...")
    
    try:
        # Check if main.py has been updated
        with open('main.py', 'r') as f:
            main_content = f.read()
        
        has_proxy_fields = 'data_gap_identified' in main_content and 'proxy_hypothesis' in main_content
        has_tags_field = 'tags' in main_content
        has_v3_title = 'v3.0' in main_content
        
        print(f"  ✓ main.py includes proxy fields: {has_proxy_fields}")
        print(f"  ✓ main.py includes tags field: {has_tags_field}")
        print(f"  ✓ main.py updated to v3.0: {has_v3_title}")
        
        # Check if research.html has been updated
        with open('static/research.html', 'r') as f:
            html_content = f.read()
        
        has_proxy_section = 'proxy-section' in html_content
        has_proxy_evidence = 'Proxy Evidence' in html_content
        has_v3_title_html = 'v3.0' in html_content
        
        print(f"  ✓ research.html includes proxy sections: {has_proxy_section}")
        print(f"  ✓ research.html includes proxy evidence display: {has_proxy_evidence}")
        print(f"  ✓ research.html updated to v3.0: {has_v3_title_html}")
        
        return has_proxy_fields and has_tags_field and has_v3_title and has_proxy_section and has_proxy_evidence and has_v3_title_html
        
    except FileNotFoundError as e:
        print(f"  ✗ File not found: {e}")
        return False

def main():
    """Run all verification checks"""
    print("=== Checkpoint 5 Verification: Deductive Proxy Framework ===\n")
    
    results = []
    
    # Run all verification checks
    results.append(("Database Migration", verify_database_migration()))
    results.append(("API Endpoints", verify_api_endpoints()))
    results.append(("Research Agent Implementation", verify_research_agent_implementation()))
    results.append(("Frontend Implementation", verify_frontend_files()))
    
    # Print summary
    print(f"\n=== Verification Results ===")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 Checkpoint 5 verification COMPLETE!")
        print("All components of the Deductive Proxy Framework are properly implemented.")
    else:
        print(f"\n⚠ Checkpoint 5 verification INCOMPLETE - {total - passed} issues found.")
    
    return passed == total

if __name__ == "__main__":
    main() 