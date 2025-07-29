#!/usr/bin/env python3
"""
Verification script for Checkpoint 4: Parallel Agents Connecting to Data
"""

import sys
import importlib
from pathlib import Path

def check_imports():
    """Check that all required modules can be imported"""
    print("Checking imports...")
    
    required_modules = [
        'mcp_server',
        'research_agent', 
        'orchestrator_agent',
        'celery_app'
    ]
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            return False
    
    return True

def check_files():
    """Check that all required files exist"""
    print("\nChecking files...")
    
    required_files = [
        'mcp_server.py',
        'start_mcp_server.py',
        'test_checkpoint4.py',
        'demo_checkpoint4.py',
        'CHECKPOINT4_README.md'
    ]
    
    for file in required_files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - missing")
            return False
    
    return True

def check_cp4_t401():
    """Check CP4-T401: Mock MCP Server implementation"""
    print("\nChecking CP4-T401: Mock MCP Server...")
    
    try:
        from mcp_server import app
        
        # Check that the app has the required endpoints
        routes = [route.path for route in app.routes]
        required_routes = ['/manifest', '/search', '/health']
        
        for route in required_routes:
            if route in routes:
                print(f"✓ {route} endpoint")
            else:
                print(f"✗ {route} endpoint - missing")
                return False
        
        # Check that mock data exists
        from mcp_server import mock_data
        if len(mock_data) >= 4:  # Should have at least 4 data sources
            print(f"✓ Mock data sources: {len(mock_data)}")
        else:
            print(f"✗ Insufficient mock data sources: {len(mock_data)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ MCP Server check failed: {e}")
        return False

def check_cp4_t402():
    """Check CP4-T402: Research Agent cognitive core loop"""
    print("\nChecking CP4-T402: Research Agent Cognitive Core Loop...")
    
    try:
        from research_agent import ResearchAgent, MCPClient, LLMClient
        
        # Check that ResearchAgent has required methods
        agent = ResearchAgent()
        required_methods = ['select_tool', 'formulate_query', 'execute_step', 'execute_research_plan']
        
        for method in required_methods:
            if hasattr(agent, method):
                print(f"✓ {method} method")
            else:
                print(f"✗ {method} method - missing")
                return False
        
        # Check that MCPClient has required methods
        mcp_client = MCPClient()
        if hasattr(mcp_client, 'get_manifest') and hasattr(mcp_client, 'search'):
            print("✓ MCPClient methods")
        else:
            print("✗ MCPClient methods - missing")
            return False
        
        # Check that LLMClient has required methods
        llm_client = LLMClient()
        if hasattr(llm_client, 'generate'):
            print("✓ LLMClient methods")
        else:
            print("✗ LLMClient methods - missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Research Agent check failed: {e}")
        return False

def check_cp4_t403():
    """Check CP4-T403: Parallel research job execution"""
    print("\nChecking CP4-T403: Parallel Research Job Execution...")
    
    try:
        from orchestrator_agent import orchestrator_task
        from research_agent import research_agent_task
        
        # Check that both tasks exist
        if orchestrator_task:
            print("✓ Orchestrator task")
        else:
            print("✗ Orchestrator task - missing")
            return False
        
        if research_agent_task:
            print("✓ Research agent task")
        else:
            print("✗ Research agent task - missing")
            return False
        
        # Check that orchestrator imports research agent task
        import orchestrator_agent
        if hasattr(orchestrator_agent, 'research_agent_task'):
            print("✓ Research agent task imported in orchestrator")
        else:
            print("✗ Research agent task not imported in orchestrator")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Parallel execution check failed: {e}")
        return False

def check_database_models():
    """Check that database models support the new functionality"""
    print("\nChecking database models...")
    
    try:
        from models import ResearchPlanStep, EvidenceItem
        
        # Check that ResearchPlanStep has the new fields
        step_fields = ['tool_used', 'tool_selection_justification', 'tool_query_rationale']
        for field in step_fields:
            if hasattr(ResearchPlanStep, field):
                print(f"✓ ResearchPlanStep.{field}")
            else:
                print(f"✗ ResearchPlanStep.{field} - missing")
                return False
        
        # Check that EvidenceItem exists
        if EvidenceItem:
            print("✓ EvidenceItem model")
        else:
            print("✗ EvidenceItem model - missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Database models check failed: {e}")
        return False

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("CHECKPOINT 4 VERIFICATION")
    print("=" * 60)
    
    checks = [
        ("File Structure", check_files),
        ("Module Imports", check_imports),
        ("Database Models", check_database_models),
        ("CP4-T401: Mock MCP Server", check_cp4_t401),
        ("CP4-T402: Research Agent Cognitive Loop", check_cp4_t402),
        ("CP4-T403: Parallel Execution", check_cp4_t403),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"✗ Check failed with exception: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 CHECKPOINT 4 VERIFICATION COMPLETE!")
        print("All requirements have been met:")
        print("  ✅ CP4-T401: Mock MCP Server implemented")
        print("  ✅ CP4-T402: Research Agent cognitive core loop implemented")
        print("  ✅ CP4-T403: Parallel research job execution implemented")
        print("\nThe system is ready for Checkpoint 5!")
        return True
    else:
        print("\n❌ Some checks failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 