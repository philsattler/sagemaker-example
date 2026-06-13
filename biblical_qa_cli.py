#!/usr/bin/env python
"""
Biblical Word Analyzer CLI Tool

Usage:
    python biblical_qa_cli.py "word" in Book Chapter:Verse Translation
    python biblical_qa_cli.py "Word" in John 1:1 KJV
    python biblical_qa_cli.py "created" in Genesis 1:1 NIV
    python biblical_qa_cli.py "Trust" in Proverbs 3:5 ESV
"""

import sys
import os
import json
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import load_model


def print_header(text: str, char: str = "=") -> None:
    """Print a formatted header."""
    width = 80
    print(f"\n{char * width}")
    print(f"  {text}")
    print(f"{char * width}\n")


def print_section(text: str) -> None:
    """Print a formatted section."""
    print(f"\n{'─' * 80}")
    print(f"  {text}")
    print(f"{'─' * 80}\n")


def format_result(result: dict) -> None:
    """Pretty print the result."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return

    # Query info
    query = result.get("query", {})
    print_section(f"Query: \"{query.get('word')}\" in {query.get('verse')} ({query.get('translation')})")

    # Word Analysis
    word_analysis = result.get("word_analysis", {})
    print("📖 ORIGINAL WORD ANALYSIS")
    print(f"  Hebrew/Greek:     {word_analysis.get('hebrew_original')}")
    print(f"  Transliteration:  {word_analysis.get('transliteration')}")
    print(f"  Morphology:       {word_analysis.get('morphology')}")
    print(f"  Strong's Number:  {word_analysis.get('strongs_number')}")
    print(f"  Definition:       {word_analysis.get('strongs_definition')}")

    # Explanations
    explanations = result.get("explanations", {})
    print("\n💡 EXPLANATIONS")
    print(f"  Simple:\n    {explanations.get('simple_explanation')}")
    print(f"\n  Theological:\n    {explanations.get('theological_explanation')}")
    print(f"\n  Key Takeaway: {explanations.get('key_takeaway')}")

    # Verse Breakdown
    verse_original = result.get("verse_original_language", {})
    if verse_original:
        print("\n📝 VERSE IN ORIGINAL LANGUAGE")
        if "hebrew" in verse_original:
            print(f"  Hebrew:          {verse_original.get('hebrew')}")
        if "greek" in verse_original:
            print(f"  Greek:           {verse_original.get('greek')}")
        print(f"  Transliteration: {verse_original.get('transliteration')}")

        word_breakdown = verse_original.get("word_breakdown", [])
        if word_breakdown:
            print("\n  Word-by-Word:")
            for word in word_breakdown[:5]:  # Show first 5 words
                print(f"    • {word.get('word')} ({word.get('trans')}) = \"{word.get('meaning')}\"")

    # Cross References
    cross_refs = result.get("cross_references", [])
    if cross_refs:
        print(f"\n🔗 CROSS-REFERENCES ({len(cross_refs)} found)")
        for i, ref in enumerate(cross_refs[:4], 1):  # Show first 4
            print(f"\n  {i}. {ref.get('book')} {ref.get('chapter')}:{ref.get('verse')}")
            print(f"     \"{ref.get('text')[:70]}...\"")
            print(f"     Score: {ref.get('score'):.2f}")

    # Theological Significance
    sig = result.get("theological_significance")
    if sig:
        print(f"\n✝️  THEOLOGICAL SIGNIFICANCE")
        print(f"  {sig}")


def show_usage() -> None:
    """Show usage information."""
    print_header("BIBLICAL WORD ANALYZER - CLI")
    print("""
Usage:
    python biblical_qa_cli.py "word" in Book Chapter:Verse Translation

Examples:
    python biblical_qa_cli.py "Word" in John 1:1 KJV
    python biblical_qa_cli.py "created" in Genesis 1:1 NIV
    python biblical_qa_cli.py "Trust" in Proverbs 3:5 ESV
    python biblical_qa_cli.py "beginning" in Genesis 1:1 KJV

Supported Translations:
    - KJV (King James Version)
    - NIV (New International Version)
    - ESV (English Standard Version)

Format:
    "WORD"     - Word to look up (in quotes, case-insensitive)
    in         - Literal "in"
    BOOK       - Bible book name (e.g., John, Genesis, Proverbs)
    CHAPTER:VERSE - Chapter and verse numbers
    TRANSLATION   - Bible translation code (KJV, NIV, ESV)
    """)


def parse_query(args: list) -> Optional[str]:
    """Parse command line arguments into a query string."""
    if len(args) < 5:  # At least: word in Book Chapter:Verse Translation
        return None

    # Rejoin all arguments
    full_input = " ".join(args)

    # Check if it contains "in" separator
    if " in " not in full_input:
        return None

    # Extract word (first arg, may have quotes)
    word = args[0].strip('"\'')

    # Find "in" and everything after
    in_index = next((i for i, arg in enumerate(args) if arg.lower() == "in"), None)
    if in_index is None or in_index + 3 >= len(args):
        return None

    # Build query
    book = args[in_index + 1]
    chapter_verse = args[in_index + 2]
    translation = args[in_index + 3]

    query = f'"{word}" in {book} {chapter_verse} {translation}'
    return query


def main() -> int:
    """Main CLI function."""
    # Handle help
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "help"]:
        show_usage()
        return 0

    # Parse query
    query = parse_query(sys.argv[1:])
    if not query:
        print("❌ Invalid query format!")
        show_usage()
        return 1

    # Load model
    try:
        print("🔄 Loading Biblical Word Analyzer...")
        model = load_model("biblical_qa")
        model.train([], [])
        print("✅ Model ready\n")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return 1

    # Make prediction
    print(f"🔍 Analyzing: {query}\n")
    try:
        result = model.predict(query)
        format_result(result)
        print("\n" + "=" * 80 + "\n")
        return 0
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
