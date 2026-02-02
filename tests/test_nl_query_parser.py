"""
Unit tests for NL Query Parser
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.nl_query_service import NLQueryParser


def test_parser():
    """Test the NL Query Parser with various queries"""
    parser = NLQueryParser()
    
    test_cases = [
        {
            'query': 'Show me bright stars near Orion',
            'expected_intent': 'SEARCH',
            'expected_entities': ['constellations', 'brightness']
        },
        {
            'query': 'Fast moving stars',
            'expected_intent': 'SEARCH',
            'expected_entities': ['motion']
        },
        {
            'query': 'What did the sky look like in ancient Egypt?',
            'expected_intent': 'TIME_QUERY',
            'expected_entities': ['time']
        },
        {
            'query': 'Top 10 fastest stars',
            'expected_intent': 'SEARCH',
            'expected_entities': ['motion', 'count']
        },
        {
            'query': 'Compare Vega and Sirius',
            'expected_intent': 'COMPARE',
            'expected_entities': ['comparison']
        },
        {
            'query': 'How many stars are brighter than magnitude 3?',
            'expected_intent': 'COUNT',
            'expected_entities': ['count']
        },
        {
            'query': 'Stars visible from Mumbai',
            'expected_intent': 'SEARCH',
            'expected_entities': ['location']
        },
        {
            'query': 'Show me the Big Dipper 5000 years ago',
            'expected_intent': 'TIME_QUERY',
            'expected_entities': ['constellations', 'time']
        },
        {
            'query': 'Bright fast stars in Orion in 2000 BC',
            'expected_intent': 'TIME_QUERY',
            'expected_entities': ['brightness', 'motion', 'constellations', 'time']
        },
        {
            'query': 'Stars near Polaris',
            'expected_intent': 'SEARCH',
            'expected_entities': []  # Polaris is a star name, not a constellation
        }
    ]
    
    print("=" * 70)
    print("NL QUERY PARSER TEST RESULTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: \"{test['query']}\"")
        print("-" * 70)
        
        result = parser.parse(test['query'])
        
        # Check intent
        intent_match = result['intent'] == test['expected_intent']
        print(f"  Intent: {result['intent']} {'✓' if intent_match else '✗ Expected: ' + test['expected_intent']}")
        
        # Check entities
        found_entities = [k for k, v in result['entities'].items() if v]
        print(f"  Entities found: {', '.join(found_entities) if found_entities else 'None'}")
        
        # Check filters
        if result['filters']:
            print(f"  Filters: {result['filters']}")
        
        # Show explanation
        print(f"  Explanation: {result['explanation']}")
        
        # Show confidence
        print(f"  Confidence: {result['confidence']:.2f}")
        
        # Show suggestions
        if result['suggestions']:
            print(f"  Suggestions: {result['suggestions']}")
        
        # Determine pass/fail
        if intent_match:
            passed += 1
            print("  Status: ✓ PASS")
        else:
            failed += 1
            print("  Status: ✗ FAIL")
    
    print("\n" + "=" * 70)
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed ({passed/len(test_cases)*100:.0f}%)")
    print("=" * 70)
    
    return passed == len(test_cases)


if __name__ == '__main__':
    success = test_parser()
    sys.exit(0 if success else 1)
