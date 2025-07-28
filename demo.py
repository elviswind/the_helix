#!/usr/bin/env python3
"""
Demonstration script for Checkpoint 1: The Interactive Mockup
Shows the complete flow from research initiation to dialectical results.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_checkpoint_1():
    print("🧠 Agentic Retrieval System v2.0 - Checkpoint 1 Demo")
    print("=" * 60)
    
    # Step 1: Create a research job
    print("\n1️⃣ Creating research job...")
    query = "Should we invest in renewable energy stocks?"
    
    response = requests.post(
        f"{BASE_URL}/v2/research",
        json={"query": query},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create research job: {response.status_code}")
        return
    
    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✅ Research job created: {job_id}")
    print(f"📝 Query: {query}")
    
    # Step 2: Check job status
    print("\n2️⃣ Checking job status...")
    max_attempts = 10
    for attempt in range(max_attempts):
        response = requests.get(f"{BASE_URL}/v2/research/{job_id}/status")
        
        if response.status_code != 200:
            print(f"❌ Failed to get job status: {response.status_code}")
            return
        
        status_data = response.json()
        print(f"   Status: {status_data['status']}")
        
        if status_data['status'] == 'AWAITING_VERIFICATION':
            thesis_id = status_data['thesis_dossier_id']
            antithesis_id = status_data['antithesis_dossier_id']
            print(f"✅ Research complete!")
            print(f"📈 Thesis dossier: {thesis_id}")
            print(f"📉 Antithesis dossier: {antithesis_id}")
            break
        elif attempt < max_attempts - 1:
            print("   ⏳ Waiting for research to complete...")
            time.sleep(2)
        else:
            print("❌ Research did not complete in time")
            return
    
    # Step 3: Fetch thesis dossier
    print("\n3️⃣ Fetching thesis dossier...")
    response = requests.get(f"{BASE_URL}/v2/dossiers/{thesis_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get thesis dossier: {response.status_code}")
        return
    
    thesis_data = response.json()
    print(f"✅ Thesis dossier retrieved")
    print(f"🎯 Mission: {thesis_data['mission']}")
    print(f"📊 Evidence items: {len(thesis_data['evidence_items'])}")
    print(f"📋 Summary: {thesis_data['summary_of_findings'][:100]}...")
    
    # Step 4: Fetch antithesis dossier
    print("\n4️⃣ Fetching antithesis dossier...")
    response = requests.get(f"{BASE_URL}/v2/dossiers/{antithesis_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get antithesis dossier: {response.status_code}")
        return
    
    antithesis_data = response.json()
    print(f"✅ Antithesis dossier retrieved")
    print(f"🎯 Mission: {antithesis_data['mission']}")
    print(f"📊 Evidence items: {len(antithesis_data['evidence_items'])}")
    print(f"📋 Summary: {antithesis_data['summary_of_findings'][:100]}...")
    
    # Step 5: Show dialectical comparison
    print("\n5️⃣ Dialectical Analysis Summary")
    print("=" * 60)
    print("📈 THESIS (Supporting Evidence):")
    for i, item in enumerate(thesis_data['evidence_items'], 1):
        print(f"   {i}. {item['title']} ({item['confidence']*100:.0f}% confidence)")
        print(f"      Source: {item['source']}")
    
    print("\n📉 ANTITHESIS (Contrary Evidence):")
    for i, item in enumerate(antithesis_data['evidence_items'], 1):
        print(f"   {i}. {item['title']} ({item['confidence']*100:.0f}% confidence)")
        print(f"      Source: {item['source']}")
    
    print("\n🎯 Checkpoint 1 Complete!")
    print("=" * 60)
    print("✅ Research initiation page (CP1-T101)")
    print("✅ Mock research endpoint (CP1-T102)")
    print("✅ Dialectical results page (CP1-T103)")
    print("\n🌐 Open http://localhost:8000 in your browser to see the full UI!")

if __name__ == "__main__":
    try:
        test_checkpoint_1()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running:")
        print("   python main.py")
    except Exception as e:
        print(f"❌ Error during demo: {e}") 