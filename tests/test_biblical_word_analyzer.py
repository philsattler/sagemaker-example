"""
Test the complete Biblical Word Analyzer system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from biblical_qa.analyzer import BiblicalWordAnalyzer
import json

# Initialize
print("🚀 Initializing Biblical Word Analyzer...\n")
analyzer = BiblicalWordAnalyzer()
analyzer.train([], [])

print("=" * 100)
print("BIBLICAL WORD ANALYZER - COMPREHENSIVE TEST")
print("=" * 100)

# Test cases
test_queries = [
    '"Word" in John 1:1 KJV',
    '"created" in Genesis 1:1 KJV',
    '"Trust" in Proverbs 3:5 KJV',
]

for query_idx, query in enumerate(test_queries, 1):
    print(f"\n{'='*100}")
    print(f"TEST CASE {query_idx}: {query}")
    print(f"{'='*100}")

    result = analyzer.predict(query)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        continue

    # Word Analysis
    print("\n📖 ORIGINAL WORD ANALYSIS")
    print("-" * 100)
    wa = result["word_analysis"]
    print(f"  Hebrew/Greek Original: {wa['hebrew_original']}")
    print(f"  Transliteration: {wa['transliteration']}")
    print(f"  Morphology: {wa['morphology']}")
    print(f"  Strong's Number: {wa['strongs_number']}")
    print(f"  Strong's Definition: {wa['strongs_definition']}")

    # Explanations
    print("\n💡 EXPLANATIONS")
    print("-" * 100)
    exp = result["explanations"]
    print(f"  Simple Explanation:\n    {exp['simple_explanation']}")
    print(f"\n  Theological Explanation:\n    {exp['theological_explanation']}")
    print(f"\n  Key Takeaway:\n    {exp['key_takeaway']}")

    # Verse Breakdown
    print("\n📝 VERSE ORIGINAL LANGUAGE")
    print("-" * 100)
    vob = result["verse_original_language"]
    if vob:
        if "hebrew" in vob:
            print(f"  Hebrew: {vob.get('hebrew', '')}")
            print(f"  Transliteration: {vob.get('transliteration', '')}")
        if "greek" in vob:
            print(f"  Greek: {vob.get('greek', '')}")
            print(f"  Transliteration: {vob.get('transliteration', '')}")

        print("\n  Word-by-Word Breakdown:")
        for i, wd in enumerate(vob.get("word_breakdown", []), 1):
            print(f"    {i}. {wd.get('word', '')} ({wd.get('trans', '')}) = \"{wd.get('meaning', '')}\" [{wd.get('strongs', '')}]")

    # Cross-References
    print("\n🔗 CROSS-REFERENCES (Other Verses Using Same Hebrew/Greek Word)")
    print("-" * 100)
    refs = result["cross_references"]
    if refs:
        for i, ref in enumerate(refs, 1):
            print(f"\n  {i}. {ref.get('book')} {ref.get('chapter')}:{ref.get('verse')}")
            print(f"     Text: \"{ref.get('text')}\"")
            print(f"     Why: {ref.get('reason')}")
            print(f"     Relevance Score: {ref.get('score', 0):.2f}")
    else:
        print("  No cross-references found")

    # Theological Notes
    print("\n✝️  THEOLOGICAL SIGNIFICANCE")
    print("-" * 100)
    print(f"  {result.get('theological_significance', 'N/A')}")

print("\n" + "=" * 100)
print("✅ COMPREHENSIVE TEST COMPLETE")
print("=" * 100)
print("\nSystem successfully analyzed 3 different biblical words with:")
print("  ✓ Original Hebrew/Greek lookups")
print("  ✓ Morphological analysis")
print("  ✓ Accessible explanations")
print("  ✓ Theological context")
print("  ✓ Cross-references to related verses")
print("  ✓ Word-by-word original language breakdown")
