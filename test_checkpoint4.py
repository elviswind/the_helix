#!/usr/bin/env python3
"""
Test script for Checkpoint 4: Parallel Agents Connecting to Data
"""

import requests
import time
import json
from sqlalchemy.orm import Session
from models import SessionLocal, Job, EvidenceDossier, ResearchPlan, ResearchPlanStep, EvidenceItem, DossierType, StepStatus

def test_mcp_server():
    """Test the mock MCP server"""
    print("Testing Mock MCP Server...")
    
    # Test manifest endpoint
    try:
        response = requests.get("http://localhost:8001/manifest")
        if response.status_code == 200:
            manifest = response.json()
            print(f"✓ MCP Server manifest retrieved successfully")
            print(f"  Available tools: {len(manifest['tools'])}")
            for tool in manifest['tools']:
                print(f"    - {tool['name']}: {tool['description']}")
        else:
            print(f"✗ Failed to get manifest: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ MCP Server not running: {e}")
        return False
    
    # Test search endpoint
    try:
        search_data = {
            "query": "growth trends",
            "tool_name": "market-data-api",
            "max_results": 5
        }
        response = requests.post("http://localhost:8001/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            print(f"✓ MCP Search successful: {results['total_count']} results")
            for result in results['results']:
                print(f"    - {result['title']} (confidence: {result['confidence']})")
        else:
            print(f"✗ Failed to search: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ MCP Search failed: {e}")
        return False
    
    return True

def test_research_agent_cognitive_loop():
    """Test the Research Agent's cognitive core loop"""
    print("\nTesting Research Agent Cognitive Core Loop...")
    
    # Test tool selection and query formulation
    from research_agent import ResearchAgent
    
    agent = ResearchAgent()
    
    # Test tool selection
    available_tools = [
        {"name": "market-data-api", "description": "Market data and trends"},
        {"name": "expert-analysis-db", "description": "Expert opinions and analysis"},
        {"name": "competitive-analysis-api", "description": "Competitive analysis"}
    ]
    
    step_description = "Analyze positive market indicators and growth trends"
    selected_tool = agent.select_tool(step_description, available_tools)
    print(f"✓ Tool selection: {selected_tool}")
    
    # Test query formulation
    query = agent.formulate_query(step_description, selected_tool)
    print(f"✓ Query formulation: {query}")
    
    return True

def test_parallel_execution():
    """Test the parallel execution of research agents"""
    print("\nTesting Parallel Research Agent Execution...")
    
    # Create a test job
    db = SessionLocal()
    try:
        # Create a simple test job
        from services import CannedResearchService
        job = CannedResearchService.create_job_with_dossiers(db, "Test parallel execution")
        
        print(f"✓ Created test job: {job.id}")
        
        # Get the dossiers
        dossiers = db.query(EvidenceDossier).filter(EvidenceDossier.job_id == job.id).all()
        print(f"✓ Found {len(dossiers)} dossiers")
        
        for dossier in dossiers:
            print(f"  - {dossier.dossier_type.value}: {dossier.id}")
        
        # Test the research agent execution
        from research_agent import ResearchAgent
        agent = ResearchAgent()
        
        # Execute research plan for one dossier
        test_dossier = dossiers[0]
        print(f"✓ Executing research plan for {test_dossier.dossier_type.value} dossier...")
        
        agent.execute_research_plan(db, test_dossier.id)
        
        # Check results
        evidence_items = db.query(EvidenceItem).filter(EvidenceItem.dossier_id == test_dossier.id).all()
        print(f"✓ Research completed: {len(evidence_items)} evidence items gathered")
        
        # Check plan steps
        research_plan = db.query(ResearchPlan).filter(ResearchPlan.dossier_id == test_dossier.id).first()
        if research_plan:
            steps = db.query(ResearchPlanStep).filter(ResearchPlanStep.research_plan_id == research_plan.id).all()
            completed_steps = [s for s in steps if s.status == StepStatus.COMPLETED]
            print(f"✓ Plan execution: {len(completed_steps)}/{len(steps)} steps completed")
            
            # Show step details
            for step in completed_steps:
                print(f"    - Step {step.step_number}: {step.description}")
                print(f"      Tool: {step.tool_used}")
                print(f"      Justification: {step.tool_selection_justification[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Parallel execution test failed: {e}")
        return False
    finally:
        db.close()

def test_full_integration():
    """Test the full integration from job creation to research completion"""
    print("\nTesting Full Integration...")
    
    # Start the research job
    try:
        response = requests.post("http://localhost:8000/v2/research", 
                               json={"query": "Test Checkpoint 4 integration"})
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data["job_id"]
            print(f"✓ Research job created: {job_id}")
        else:
            print(f"✗ Failed to create research job: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Failed to create research job: {e}")
        return False
    
    # Monitor job status
    max_wait = 60  # seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"http://localhost:8000/v2/research/{job_id}/status")
            if response.status_code == 200:
                status_data = response.json()
                print(f"Job status: {status_data['status']}")
                
                if status_data['status'] == 'AWAITING_VERIFICATION':
                    print("✓ Job completed successfully!")
                    
                    # Check dossiers
                    if status_data['thesis_dossier_id'] and status_data['antithesis_dossier_id']:
                        print(f"✓ Thesis dossier: {status_data['thesis_dossier_id']}")
                        print(f"✓ Antithesis dossier: {status_data['antithesis_dossier_id']}")
                        
                        # Get dossier details
                        for dossier_id in [status_data['thesis_dossier_id'], status_data['antithesis_dossier_id']]:
                            response = requests.get(f"http://localhost:8000/v2/dossiers/{dossier_id}")
                            if response.status_code == 200:
                                dossier_data = response.json()
                                print(f"✓ {dossier_data['dossier_id']}: {len(dossier_data['evidence_items'])} evidence items")
                                print(f"  Summary: {dossier_data['summary_of_findings'][:100]}...")
                    
                    return True
                elif status_data['status'] == 'FAILED':
                    print("✗ Job failed")
                    return False
                
            time.sleep(2)
        except Exception as e:
            print(f"Error checking status: {e}")
            time.sleep(2)
    
    print("✗ Job did not complete within expected time")
    return False

def main():
    """Run all Checkpoint 4 tests"""
    print("=" * 60)
    print("CHECKPOINT 4 TEST: Parallel Agents Connecting to Data")
    print("=" * 60)
    
    tests = [
        ("Mock MCP Server", test_mcp_server),
        ("Research Agent Cognitive Loop", test_research_agent_cognitive_loop),
        ("Parallel Execution", test_parallel_execution),
        ("Full Integration", test_full_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 CHECKPOINT 4 COMPLETED SUCCESSFULLY!")
    else:
        print("❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main() 