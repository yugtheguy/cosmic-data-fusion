"""Quick test of refined NL parser"""
from app.services.nl_query_service import NLQueryParser

parser = NLQueryParser()

test_queries = [
    "Show me bright stars near Orion",
    "Fast moving stars",
    "Top 10 fastest stars",
    "Luminous stars in Cassiopeia",  # Test synonym
    "Swift stars",  # Test synonym
    "Give me 5 stars"  # Test new pattern
]

print("Testing Refined NL Parser")
print("=" * 60)

for query in test_queries:
    result = parser.parse(query)
    print(f"\nQuery: {query}")
    print(f"  Intent: {result['intent']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Explanation: {result['explanation']}")
    if result['filters']:
        print(f"  Filters: {list(result['filters'].keys())}")

print("\n" + "=" * 60)
print("Refinement test complete!")
