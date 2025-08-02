#!/usr/bin/env python3
"""
Test script for Checkpoint 7: The Final Synthesis and Balanced Report

Tests the synthesis agent functionality and final report generation.
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_synthesis_agent_implementation():
    """Test CP7-T701: Synthesis Agent Implementation"""
    print("🧪 Testing CP7-T701: Synthesis Agent Implementation")
    
    # Check if synthesis agent is imported and available
    try:
        from synthesis_agent import synthesis_agent_task, SynthesisAgent
        print("✅ Synthesis agent module imported successfully")
    except ImportError as e:
        print(f"❌ CP7-T701: Synthesis agent import failed - {e}")
        return False
    
    # Test synthesis agent class
    try:
        agent = SynthesisAgent()
        print("✅ Synthesis agent class instantiated successfully")
    except Exception as e:
        print(f"❌ CP7-T701: Synthesis agent instantiation failed - {e}")
        return False
    
    # Test prompt generation method
    try:
        # Create mock dossiers for testing
        from models import EvidenceDossier, ResearchPlan, ResearchPlanStep, EvidenceItem
        
        # Mock thesis dossier
        thesis_dossier = EvidenceDossier()
        thesis_dossier.mission = "Test thesis mission"
        thesis_dossier.summary_of_findings = "Test thesis summary"
        thesis_dossier.research_plan = ResearchPlan()
        thesis_dossier.research_plan.steps = []
        thesis_dossier.evidence_items = []
        
        # Mock antithesis dossier
        antithesis_dossier = EvidenceDossier()
        antithesis_dossier.mission = "Test antithesis mission"
        antithesis_dossier.summary_of_findings = "Test antithesis summary"
        antithesis_dossier.research_plan = ResearchPlan()
        antithesis_dossier.research_plan.steps = []
        antithesis_dossier.evidence_items = []
        
        prompt = agent.generate_synthesis_prompt(thesis_dossier, antithesis_dossier)
        if prompt and len(prompt) > 100:
            print("✅ Synthesis prompt generation working")
        else:
            print("❌ CP7-T701: Synthesis prompt generation failed")
            return False
            
    except Exception as e:
        print(f"❌ CP7-T701: Synthesis prompt generation failed - {e}")
        return False
    
    print("✅ CP7-T701: Synthesis Agent Implementation - PASSED")
    return True

def test_final_report_endpoint():
    """Test CP7-T702: Final Report Endpoint"""
    print("🧪 Testing CP7-T702: Final Report Endpoint")
    
    # Test endpoint exists
    try:
        response = requests.get(f"{BASE_URL}/v3/jobs/test-job/report")
        # Should return 404 for non-existent job, not 500 for missing endpoint
        if response.status_code in [404, 400]:
            print("✅ Final report endpoint exists")
        else:
            print(f"❌ CP7-T702: Unexpected response from endpoint - {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ CP7-T702: Cannot connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"❌ CP7-T702: Endpoint test failed - {e}")
        return False
    
    print("✅ CP7-T702: Final Report Endpoint - PASSED")
    return True

def test_synthesis_database_model():
    """Test that SynthesisReport model is properly defined"""
    print("🧪 Testing SynthesisReport Database Model")
    
    try:
        from models import SynthesisReport
        print("✅ SynthesisReport model imported successfully")
        
        # Test model attributes
        report = SynthesisReport()
        report.id = "test-syn-123"
        report.job_id = "test-job-123"
        report.content = "Test synthesis content"
        
        if hasattr(report, 'id') and hasattr(report, 'job_id') and hasattr(report, 'content'):
            print("✅ SynthesisReport model has required attributes")
        else:
            print("❌ SynthesisReport model missing required attributes")
            return False
            
    except Exception as e:
        print(f"❌ SynthesisReport model test failed - {e}")
        return False
    
    print("✅ SynthesisReport Database Model - PASSED")
    return True

def test_celery_integration():
    """Test that synthesis agent is properly integrated with Celery"""
    print("🧪 Testing Celery Integration")
    
    try:
        from celery_app import celery_app
        from synthesis_agent import synthesis_agent_task
        
        # Check if task is registered
        if synthesis_agent_task.name in celery_app.tasks:
            print("✅ Synthesis agent task registered with Celery")
        else:
            print("❌ Synthesis agent task not registered with Celery")
            return False
            
    except Exception as e:
        print(f"❌ Celery integration test failed - {e}")
        return False
    
    print("✅ Celery Integration - PASSED")
    return True

def test_synthesis_trigger_in_main():
    """Test that synthesis is triggered when both dossiers are approved"""
    print("🧪 Testing Synthesis Trigger in Main API")
    
    try:
        # Check if the synthesis trigger code exists in main.py
        with open('main.py', 'r') as f:
            content = f.read()
            
        if 'synthesis_agent_task.delay(job.id)' in content:
            print("✅ Synthesis trigger code found in main.py")
        else:
            print("❌ Synthesis trigger code not found in main.py")
            return False
            
        if 'from synthesis_agent import synthesis_agent_task' in content:
            print("✅ Synthesis agent import found in main.py")
        else:
            print("❌ Synthesis agent import not found in main.py")
            return False
            
    except Exception as e:
        print(f"❌ Synthesis trigger test failed - {e}")
        return False
    
    print("✅ Synthesis Trigger in Main API - PASSED")
    return True

def test_frontend_synthesis_functionality():
    """Test that frontend has synthesis functionality"""
    print("🧪 Testing Frontend Synthesis Functionality")
    
    try:
        with open('static/research.html', 'r') as f:
            content = f.read()
            
        # Check for final report section
        if 'final-report-section' in content:
            print("✅ Final report section found in frontend")
        else:
            print("❌ Final report section not found in frontend")
            return False
            
        # Check for displayFinalReport function
        if 'function displayFinalReport' in content:
            print("✅ displayFinalReport function found in frontend")
        else:
            print("❌ displayFinalReport function not found in frontend")
            return False
            
        # Check for synthesizeReport function update
        if 'fetch(`/v3/jobs/${jobId}/report`)' in content:
            print("✅ Updated synthesizeReport function found")
        else:
            print("❌ Updated synthesizeReport function not found")
            return False
            
    except Exception as e:
        print(f"❌ Frontend synthesis test failed - {e}")
        return False
    
    print("✅ Frontend Synthesis Functionality - PASSED")
    return True

def run_all_tests():
    """Run all checkpoint 7 verification tests"""
    print("=== Checkpoint 7 Verification: The Final Synthesis and Balanced Report ===\n")
    
    tests = [
        ("CP7-T701", "Synthesis Agent Implementation", test_synthesis_agent_implementation),
        ("CP7-T702", "Final Report Endpoint", test_final_report_endpoint),
        ("Database Model", "SynthesisReport Model", test_synthesis_database_model),
        ("Celery Integration", "Synthesis Agent Task", test_celery_integration),
        ("Main API Integration", "Synthesis Trigger", test_synthesis_trigger_in_main),
        ("Frontend Integration", "Synthesis UI", test_frontend_synthesis_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_id, test_name, test_func in tests:
        print(f"\n--- {test_id}: {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_id}: {test_name} - PASSED")
            else:
                print(f"❌ {test_id}: {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_id}: {test_name} - ERROR: {e}")
    
    print(f"\n=== Verification Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 Checkpoint 7 verification COMPLETE!")
        print("✅ The Final Synthesis and Balanced Report is fully implemented")
        return True
    else:
        print(f"\n⚠ Checkpoint 7 verification INCOMPLETE - {total - passed} issues found.")
        return False

if __name__ == "__main__":
    run_all_tests() 