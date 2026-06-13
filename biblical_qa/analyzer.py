"""
Complete Biblical Word Analyzer - Integrates all components.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import BaseModel
from biblical_qa.word_lookup import BiblicalWordLookup
from biblical_qa.cross_references import CrossReferenceGenerator
from biblical_qa.explainer import LingualExplainer
from typing import Dict, List, Optional

class BiblicalWordAnalyzer(BaseModel):
    """
    Complete word analysis system combining:
    1. Original language lookup (Hebrew/Greek)
    2. Morphological analysis
    3. Theological context
    4. Cross-references
    5. Accessible explanations
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.lookup_engine = BiblicalWordLookup()
        self.cross_ref_gen = CrossReferenceGenerator()
        self.explainer = LingualExplainer()
        self.set_metadata("model_type", "biblical_word_analyzer")
        self.set_metadata("components", [
            "word_lookup", "cross_reference", "explanation"
        ])

    def train(self, X, y, **kwargs):
        """
        Initialize the analyzer.
        No ML training needed - this is a lookup/retrieval system.
        """
        print("Initializing Biblical Word Analyzer...")
        self.set_metadata("initialized", True)
        self.set_metadata("num_verses_indexed", 100)

    def predict(self, X) -> Dict:
        """
        Analyze a biblical word.

        Input format: "word" in Verse:Reference Translation
        Example: "Word" in John 1:1 KJV

        Returns: Complete analysis
        """
        # Parse input
        parsed = self._parse_input(X)
        if "error" in parsed:
            return parsed

        word = parsed["word"]
        verse = parsed["verse"]
        translation = parsed["translation"]

        # Lookup word
        word_lookup = self.lookup_engine.lookup_word(word, verse, translation)
        if "error" in word_lookup:
            return word_lookup

        strongs_num = word_lookup.get("strongs_number")
        word_def = word_lookup.get("word_analysis", {})

        # Check if word was actually found
        word_found = word_def.get("strongs_definition") and word_def.get("strongs_definition") != f"Definition not found for '{word}'"

        # Generate explanations only if word was found
        if word_found:
            explanations = self.explainer.explain_word(
                strongs_definition=word_def.get("strongs_definition", ""),
                word_hebrew=word_def.get("hebrew", word_def.get("greek", "")),
                theological_notes=word_def.get("theological_notes", ""),
                context_verse=verse
            )
        else:
            # Word not found - provide helpful message
            explanations = {
                "simple_explanation": f"The English word '{word}' was not found in the Greek text of {verse}.",
                "theological_explanation": "Try searching for the actual Greek word from that verse instead.",
                "cultural_linguistic_notes": {},
                "key_takeaway": "Use the Greek/Hebrew word directly for more accurate analysis."
            }

        # Identify theme
        theme = self._identify_theme(word_def.get("theological_notes", ""))

        # Generate cross-references
        cross_refs = self.cross_ref_gen.generate_cross_references(
            strongs_num,
            original_theme=theme,
            limit=4
        )

        # Compile final output
        result = {
            "query": word_lookup["query"],
            "word_analysis": {
                "hebrew_original": word_def.get("hebrew_original", word_def.get("hebrew", word_def.get("greek", "N/A"))),
                "transliteration": word_def.get("transliteration", ""),
                "morphology": word_def.get("morphology", ""),
                "strongs_number": strongs_num,
                "strongs_definition": word_def.get("strongs_definition", ""),
                "lexicon_definition": word_def.get("lexicon_definition", ""),
            },
            "explanations": explanations,
            "verse_original_language": word_lookup.get("verse_original", {}),
            "verse_word_breakdown": self._get_verse_breakdown(word_lookup),
            "cross_references": cross_refs,
            "theological_significance": word_def.get("theological_notes", ""),
        }

        return result

    def _parse_input(self, input_str: str) -> Dict:
        """Parse input string like: "Word" in John 1:1 KJV"""
        import re

        pattern = r'"([^"]+)"\s+in\s+(\w+\s+\d+:\d+)\s+(\w+)'
        match = re.search(pattern, input_str)

        if not match:
            return {"error": f"Invalid format. Use: \"word\" in John 1:1 KJV"}

        return {
            "word": match.group(1),
            "verse": match.group(2),
            "translation": match.group(3),
        }

    def _identify_theme(self, theological_notes: str) -> Optional[str]:
        """Identify theological theme from notes."""
        themes = ["creation", "word_of_god", "trust_faith", "divine_utterance"]
        notes_lower = theological_notes.lower()

        for theme in themes:
            if any(word in notes_lower for word in theme.split("_")):
                return theme
        return None

    def _get_verse_breakdown(self, word_lookup: Dict) -> List[Dict]:
        """Get word-by-word breakdown of the verse."""
        original = word_lookup.get("verse_original", {})
        return original.get("word_breakdown", [])
