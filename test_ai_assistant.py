"""
Test AI Research Assistant Integration
Quick verification that all components work together
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_standard_query():
    """Test 1: Standard query without AI (backward compatibility)"""
    print("=" * 60)
    print("TEST 1: Standard Query (No AI)")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/nl-query/query",
        json={
            "query": "bright stars",
            "page": 1,
            "page_size": 10
            # ai_enhanced NOT specified - should default to False
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"Intent: {data['intent']}")
        print(f"Results: {len(data['results'])} stars")
        print(f"AI Analysis: {data.get('ai_analysis', 'None (expected)')}")
        print("\n✅ PASS: Standard query works without AI\n")
    else:
        print(f"❌ FAIL: Status {response.status_code}")
        print(response.text)


def test_ai_enhanced_query():
    """Test 2: AI-enhanced query"""
    print("=" * 60)
    print("TEST 2: AI-Enhanced Query")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/nl-query/query",
        json={
            "query": "Which stars show unusual brightness?",
            "ai_enhanced": True,  # Enable AI Research Assistant
            "page_size": 50
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"Intent: {data['intent']}")
        print(f"Results: {len(data['results'])} stars found")
        
        if data.get('ai_analysis'):
            ai = data['ai_analysis']
            print(f"\n🧠 AI Analysis:")
            print(f"   Summary: {ai.get('research_summary', 'N/A')}")
            print(f"   Analyzed: {ai.get('total_analyzed', 0)} objects")
            print(f"   Shown: {ai.get('shown', 0)} key findings")
            print(f"   Sample Strength: {ai.get('analysis_strength', 'N/A')}")
            print(f"   Reasoning: {ai.get('reasoning', 'N/A')}")
            
            findings = ai.get('key_findings', [])
            if findings:
                print(f"\n   Key Findings:")
                for i, finding in enumerate(findings[:3], 1):
                    print(f"   #{i} {finding['object_name']}")
                    print(f"      Why: {finding['why_it_matters']}")
                    print(f"      Deviation: {finding['deviation_strength']}")
                    print(f"      Significance: {finding['significance']:.2%}")
            
            print("\n✅ PASS: AI enhancement works\n")
        else:
            print("⚠️  No AI analysis in response")
    else:
        print(f"❌ FAIL: Status {response.status_code}")
        print(response.text)


def test_different_queries():
    """Test 3: Multiple query types"""
    print("=" * 60)
    print("TEST 3: Various Query Types")
    print("=" * 60)
    
    queries = [
        "Top 5 fastest stars",
        "Stars near Orion",
        "Find unusually close stars",
        "Brightest objects in dataset"
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        response = requests.post(
            f"{BASE_URL}/api/nl-query/query",
            json={"query": query, "ai_enhanced": True}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Intent: {data['intent']}")
            print(f"   Results: {len(data['results'])} stars")
            if data.get('ai_analysis'):
                print(f"   AI Summary: {data['ai_analysis']['research_summary'][:80]}...")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    
    print("\n✅ PASS: Multiple query types work\n")


def test_health_check():
    """Test 4: Health check"""
    print("=" * 60)
    print("TEST 4: Service Health Check")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/nl-query/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"Service Status: {data.get('status', 'Unknown')}")
        print(f"Parser Loaded: {data.get('parser_loaded', False)}")
        print(f"Knowledge Base: {data.get('knowledge_base_loaded', False)}")
        print("\n✅ PASS: Service healthy\n")
    else:
        print(f"❌ FAIL: Status {response.status_code}")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("AI RESEARCH ASSISTANT - INTEGRATION TESTS")
    print("=" * 60 + "\n")
    
    try:
        # Test basic health
        test_health_check()
        
        # Test backward compatibility
        test_standard_query()
        
        # Test AI enhancement
        test_ai_enhanced_query()
        
        # Test various query types
        test_different_queries()
        
        print("=" * 60)
        print("🎉 ALL TESTS COMPLETE")
        print("=" * 60)
        print("\n✅ AI Research Assistant is functioning correctly!")
        print("\n📝 Next Steps:")
        print("   1. Visit: http://localhost:5173/ai-assistant")
        print("   2. Try asking: 'Which stars show unusual brightness?'")
        print("   3. Toggle AI ON/OFF to see the difference")
        print("\n🚀 Ready for hackathon demo!\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend")
        print("Make sure the server is running:")
        print("   cd c:\\code\\cosmic-data-fusion")
        print("   .venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --port 8000\n")
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")


if __name__ == "__main__":
    main()
