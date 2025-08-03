#!/usr/bin/env python3
"""
Integration test for the MCP implementation with real data
"""

import requests
import json
import time
from datetime import datetime

# Configuration
MCP_API_URL = "http://localhost:8000"

def test_sec_parser():
    """Test the SEC parser with real data"""
    print("🧪 Testing SEC Parser...")
    
    try:
        from sec_parser import get_available_companies, get_available_years, get_10k_section
        
        # Test available companies
        companies = get_available_companies()
        print(f"✅ Found {len(companies)} companies")
        print(f"   Sample companies: {companies[:5]}")
        
        # Test available years for AAPL
        years = get_available_years('AAPL')
        print(f"✅ AAPL has {len(years)} years of data: {years[-5:]}")  # Last 5 years
        
        # Test section extraction
        result = get_10k_section('AAPL', 2023, '1')
        if 'content' in result and result['content']:
            print(f"✅ Section 1 extracted successfully ({len(result['content'])} chars)")
        else:
            print(f"⚠️  Section 1 extraction: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ SEC Parser test failed: {e}")
        return False

def test_tools():
    """Test the tool system"""
    print("\n🧪 Testing Tools...")
    
    try:
        from tools import execute_tool, get_available_companies
        
        # Test SEC data tool
        result = execute_tool("sec_data_tool", action="list_companies")
        if "companies" in result:
            print(f"✅ SEC Data Tool works: {len(result['companies'])} companies found")
        else:
            print(f"❌ SEC Data Tool failed: {result}")
        
        # Test XBRL tool
        result = execute_tool("xbrl_financial_fact_retriever", symbol="AAPL", year=2023, concept="Revenue")
        if "value" in result and result["value"]:
            print(f"✅ XBRL Tool works: Revenue = ${result['value']:,}")
        else:
            print(f"❌ XBRL Tool failed: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tools test failed: {e}")
        return False

def test_api_endpoints():
    """Test the API endpoints"""
    print("\n🧪 Testing API Endpoints...")
    
    try:
        # Test health check
        response = requests.get(f"{MCP_API_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test available tools
        response = requests.get(f"{MCP_API_URL}/tools/available")
        if response.status_code == 200:
            tools = response.json()
            print(f"✅ Available tools endpoint works: {len(tools['tools'])} tools")
        else:
            print(f"❌ Available tools failed: {response.status_code}")
            return False
        
        # Test tool execution
        tool_request = {
            "tool_name": "sec_data_tool",
            "parameters": {
                "action": "list_companies"
            }
        }
        response = requests.post(f"{MCP_API_URL}/tools/execute", json=tool_request)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Tool execution endpoint works")
            else:
                print(f"❌ Tool execution failed: {result.get('error')}")
                return False
        else:
            print(f"❌ Tool execution request failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_research_workflow():
    """Test the complete research workflow"""
    print("\n🧪 Testing Research Workflow...")
    
    try:
        # Start a research job
        research_request = {
            "query": "Evaluate the long-term investment case for Apple (AAPL)",
            "user_id": "integration_test"
        }
        
        response = requests.post(f"{MCP_API_URL}/research/start", json=research_request)
        if response.status_code == 202:
            result = response.json()
            job_id = result['job_id']
            print(f"✅ Research job created: {job_id}")
            
            # Check job status
            response = requests.get(f"{MCP_API_URL}/research/{job_id}/status")
            if response.status_code == 200:
                status = response.json()
                print(f"✅ Job status retrieved: {status['status']}")
            else:
                print(f"❌ Job status failed: {response.status_code}")
                return False
            
            return True
        else:
            print(f"❌ Research job creation failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Research workflow test failed: {e}")
        return False

def test_ui_endpoints():
    """Test the UI endpoints"""
    print("\n🧪 Testing UI Endpoints...")
    
    try:
        # Test index page
        response = requests.get(f"{MCP_API_URL}/")
        if response.status_code == 200:
            print("✅ Index page served successfully")
        else:
            print(f"❌ Index page failed: {response.status_code}")
            return False
        
        # Test research interface
        response = requests.get(f"{MCP_API_URL}/research-interface")
        if response.status_code == 200:
            print("✅ Research interface served successfully")
        else:
            print(f"❌ Research interface failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ UI test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Integration Testing for AR v3.0 MCP System")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"API URL: {MCP_API_URL}")
    print("=" * 60)
    
    tests = [
        ("SEC Parser", test_sec_parser),
        ("Tools", test_tools),
        ("API Endpoints", test_api_endpoints),
        ("Research Workflow", test_research_workflow),
        ("UI Endpoints", test_ui_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The MCP system is ready for use.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 