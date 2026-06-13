"""
Accessible explanations of Strong's definitions using LLM.
"""

from typing import Dict, Optional

class LingualExplainer:
    """
    Takes Strong's definitions and generates accessible,
    theologically-informed explanations.
    """

    def __init__(self):
        self.explanation_templates = self._load_templates()

    def _load_templates(self) -> Dict:
        """Load explanation templates for common biblical concepts."""
        return {
            "creation": "Represents God's divine creative act - bringing something into existence from nothing. This is exclusively God's prerogative in Scripture.",
            "word": "The utterance, communication, or expression of thought. In theological context, refers to God's self-revelation and the means by which He communicates His will.",
            "trust": "Active reliance and commitment, not merely passive belief. Biblical trust involves complete commitment of one's whole self - intellect, emotion, and will.",
            "heart": "The center of the human person - encompassing mind, emotion, and will. In Hebrew thought, it's the seat of all inner life, not just emotion.",
        }

    def explain_word(
        self,
        strongs_definition: str,
        word_hebrew: str,
        theological_notes: str,
        context_verse: str
    ) -> Dict:
        """
        Generate accessible explanation of a biblical word.
        """

        simple_explanation = self._generate_simple(
            strongs_definition,
            word_hebrew
        )

        theological_explanation = self._generate_theological(
            theological_notes,
            context_verse
        )

        cultural_notes = self._generate_cultural_notes(word_hebrew)

        return {
            "simple_explanation": simple_explanation,
            "theological_explanation": theological_explanation,
            "cultural_linguistic_notes": cultural_notes,
            "key_takeaway": self._generate_key_takeaway(
                strongs_definition,
                theological_notes
            ),
        }

    def _generate_simple(self, definition: str, hebrew: str) -> str:
        """Generate a simple, accessible explanation."""
        if not definition:
            return "A significant biblical word."

        simple = definition.split(";")[0].lower()
        return f"'{hebrew}' refers to: {simple}. This word appears frequently throughout Scripture to convey important spiritual concepts."

    def _generate_theological(self, notes: str, context: str) -> str:
        """Generate fuller theological explanation."""
        if not notes:
            return "This word carries important theological significance in Scripture."

        return f"Theologically, {notes} In the context of {context}, this word emphasizes God's nature and His relationship with humanity."

    def _generate_cultural_notes(self, hebrew: str) -> Dict:
        """Generate cultural and linguistic context."""
        return {
            "hebrew_origin": f"From Hebrew '{hebrew}'",
            "linguistic_family": "Ancient Semitic language",
            "cultural_context": "Reflects Hebrew thought patterns which emphasize wholeness and integration of physical and spiritual reality",
            "translation_challenges": "Some nuances are lost in English translation due to grammatical differences",
        }

    def _generate_key_takeaway(self, definition: str, notes: str) -> str:
        """Generate key learning point."""
        if notes:
            return f"Key insight: {notes.split('.')[0].lower()}."
        return "Understanding this word's original meaning deepens our comprehension of Scripture."
