"""
Generate theologically relevant cross-references.
"""

from typing import List, Dict, Optional
from biblical_qa.concordance_data import get_verses_with_word, THEOLOGICAL_THEMES

class CrossReferenceGenerator:
    """
    Finds theologically relevant cross-references for a word.
    """

    THEME_SIGNIFICANCE = {
        "creation": 1.0,
        "word_of_god": 0.95,
        "divine_utterance": 0.9,
        "trust_faith": 0.85,
    }

    def generate_cross_references(
        self,
        strongs_number: str,
        original_theme: str = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Generate cross-references for a Strong's number.
        Returns empty list if Strong's data not available.
        """
        if not strongs_number or strongs_number == "N/A":
            return []

        print(f"  Generating cross-references for {strongs_number}...")

        # Get all verses with this word
        all_verses = get_verses_with_word(strongs_number)

        if not all_verses:
            return []

        # Score and rank verses
        scored_verses = [
            self._score_verse(v, strongs_number, original_theme)
            for v in all_verses
        ]

        # Sort by score
        scored_verses.sort(key=lambda x: x["score"], reverse=True)

        # Return top N
        return scored_verses[:limit]

    def _score_verse(
        self,
        verse: Dict,
        strongs_number: str,
        original_theme: str = None
    ) -> Dict:
        """Score a verse for relevance."""
        score = 0.0

        # Same word/root (most important)
        score += 1.0

        # Thematic alignment
        if original_theme and original_theme in THEOLOGICAL_THEMES:
            theme_words = THEOLOGICAL_THEMES[original_theme]
            if strongs_number in theme_words:
                theme_sig = self.THEME_SIGNIFICANCE.get(original_theme, 0.5)
                score += theme_sig * 0.5

        # Theological significance
        theological_weight = self._assess_theological_depth(verse.get("text", ""))
        score += theological_weight * 0.3

        # Add explanation
        explanation = self._generate_explanation(verse, original_theme)

        return {
            **verse,
            "score": score,
            "reason": explanation,
        }

    def _assess_theological_depth(self, text: str) -> float:
        """Assess theological significance of a verse."""
        theological_keywords = [
            "god", "lord", "jesus", "spirit", "faith", "grace", "love",
            "salvation", "covenant", "kingdom", "truth", "eternal", "holy"
        ]

        text_lower = text.lower()
        matches = sum(1 for kw in theological_keywords if kw in text_lower)

        return min(matches / len(theological_keywords), 1.0)

    def _generate_explanation(self, verse: Dict, original_theme: str = None) -> str:
        """Generate explanation for why this is a relevant cross-reference."""
        explanations = []

        # Same word/root
        explanations.append("Uses the same Hebrew/Greek word")

        # Thematic connection
        if original_theme:
            explanations.append(f"Develops theme of {original_theme}")

        # Book context
        book = verse.get("book", "")
        if "Genesis" in book:
            explanations.append("Foundational OT passage")
        elif "Psalm" in book or "Proverbs" in book:
            explanations.append("Wisdom literature perspective")
        elif book in ["Hebrews", "John", "Romans"]:
            explanations.append("Theological development in NT")

        return " • ".join(explanations)
