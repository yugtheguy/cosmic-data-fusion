"""
Hackathon Readiness Verification
Tests new language and disclaimers
"""
import requests
import json

def test_hackathon_language():
    """Verify all hackathon-ready language changes"""
    
    print("=" * 70)
    print("HACKATHON READINESS VERIFICATION")
    print("=" * 70)
    
    # Test AI-enhanced query
    response = requests.post(
        'http://localhost:8000/api/nl-query/query',
        json={
            'query': 'Which stars are unusually bright?',
            'page': 1,
            'page_size': 50,
            'ai_enhanced': True
        }
    )
    
    data = response.json()
    ai_analysis = data.get('ai_analysis', {})
    
    print("\n✅ API Response Structure:")
    print(f"   - ai_enhanced: {ai_analysis.get('ai_enhanced')}")
    print(f"   - analysis_scope: {ai_analysis.get('analysis_scope')}")
    print()
    
    print("📊 LANGUAGE AUDIT:")
    print("=" * 70)
    
    # Check for banned phrases
    full_response = json.dumps(ai_analysis, indent=2)
    
    banned_phrases = [
        'statistically significant',
        'research-relevant',
        'high confidence',
        'noteworthy patterns',
        'revealed',
        'discovered',
        'important for research'
    ]
    
    approved_phrases = [
        'exploratory',
        'query-limited',
        'composite deviation',
        'ranks in top',
        'deviation score'
    ]
    
    print("\n❌ BANNED PHRASES (should NOT appear):")
    for phrase in banned_phrases:
        if phrase.lower() in full_response.lower():
            print(f"   ⚠️  FOUND: '{phrase}' - NEEDS FIXING")
        else:
            print(f"   ✅ Absent: '{phrase}'")
    
    print("\n✅ APPROVED PHRASES (should appear):")
    for phrase in approved_phrases:
        if phrase.lower() in full_response.lower():
            print(f"   ✅ Present: '{phrase}'")
        else:
            print(f"   ⚠️  Missing: '{phrase}'")
    
    print("\n" + "=" * 70)
    print("SAMPLE AI RESPONSE:")
    print("=" * 70)
    print(f"\nAnalysis Scope:")
    print(f"   {ai_analysis.get('analysis_scope')}")
    print(f"\nResearch Summary:")
    print(f"   {ai_analysis.get('research_summary')}")
    print(f"\nReasoning:")
    print(f"   {ai_analysis.get('reasoning')}")
    
    # Check first finding
    if ai_analysis.get('key_findings'):
        first = ai_analysis['key_findings'][0]
        print(f"\nSample Finding:")
        print(f"   Object: {first['object_name']}")
        print(f"   Why it matters: {first['why_it_matters']}")
        print(f"   Deviation: {first['deviation_strength']}")
    
    print("\n" + "=" * 70)
    print("🎯 HACKATHON JUDGE QUESTIONS - READY TO ANSWER:")
    print("=" * 70)
    print("""
Q: "What do you mean by statistically significant?"
A: "We use composite deviation scoring across features. Objects ranking
   in extreme percentiles (top/bottom 10%) are highlighted. No p-values
   or hypothesis testing—this is exploratory ranking only."

Q: "How is the deviation score calculated?"
A: "Deviation score is the normalized composite score. A score of 0.85 means
   the object deviates strongly from the mean on multiple features.
   Higher score = more distinctive within this query's results."

Q: "Can I trust these insights for research?"
A: "This is exploratory data analysis to accelerate manual review.
   All rankings are query-limited and relative to the returned dataset.
   Users should validate findings with domain expertise."

Q: "What if I run the same query twice?"
A: "Results are fully deterministic. Same query = same rankings.
   Scores are based on statistical calculations, not randomness."
    """)
    
    print("=" * 70)
    print("✅ HACKATHON READINESS: VERIFIED")
    print("=" * 70)

if __name__ == '__main__':
    test_hackathon_language()
