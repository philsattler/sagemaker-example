"""
Morphological Lexicon Builder - loads SBLGNT morphological data.
Provides Hebrew/Greek word analysis without Strong's dependency.
"""

import os
import csv
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

class MorphologicalLexicon:
    """
    Loads and indexes morphological data from SBLGNT (Greek NT).
    Each word entry contains: surface form, lemma, POS, morphology, transliteration.
    """

    def __init__(self):
        """Initialize and load lexicon data."""
        self.greek_lemmas: Dict[str, Dict] = {}  # lemma -> {pos, morphology, surface_forms}
        self.greek_index: Dict[str, List[str]] = defaultdict(list)  # surface form -> [lemmas]
        self.verses: Dict[str, List[Dict]] = defaultdict(list)  # verse ref -> [word data]
        self._load_greek_data()

    def _load_greek_data(self):
        """Load Greek NT morphological data from SBLGNT."""
        # Comprehensive sample data from various verses
        # In production, this would be dynamically loaded from SBLGNT repository
        # https://raw.githubusercontent.com/morphgnt/sblgnt/master/[book]-morphgnt.txt
        sample_entries = [
            # John 1:1 (λόγος, Word)
            {"verse": "John 1:1", "surface": "Ἐν", "lemma": "ἐν", "pos": "preposition", "morphology": "---", "transliteration": "en", "definition": "in, within, at, among"},
            {"verse": "John 1:1", "surface": "λόγος", "lemma": "λόγος", "pos": "noun", "morphology": "nominative, singular, masculine", "transliteration": "logos", "definition": "word, speech, discourse, utterance, reason"},
            {"verse": "John 1:1", "surface": "Word", "lemma": "λόγος", "pos": "noun", "morphology": "nominative, singular, masculine", "transliteration": "logos", "definition": "word, speech, discourse, utterance, reason"},
            {"verse": "John 1:1", "surface": "ἦν", "lemma": "εἰμί", "pos": "verb", "morphology": "imperfect, active, indicative, 3rd person, singular", "transliteration": "en", "definition": "to be, to exist, to happen"},

            # Genesis 1:1 (created, bara)
            {"verse": "Genesis 1:1", "surface": "created", "lemma": "בָּרָא", "pos": "verb", "morphology": "qal, perfect", "transliteration": "bara", "definition": "to create, to shape, to form (divine creation)"},
            {"verse": "Genesis 1:1", "surface": "בָּרָא", "lemma": "בָּרָא", "pos": "verb", "morphology": "qal, perfect, 3rd person, masculine, singular", "transliteration": "bara", "definition": "to create, to shape, to form (divine creation)"},
            {"verse": "Genesis 1:1", "surface": "beginning", "lemma": "רֵאשִׁית", "pos": "noun", "morphology": "construct, feminine, singular", "transliteration": "bereshit", "definition": "beginning, first, head"},
            {"verse": "Genesis 1:1", "surface": "בְרֵאשִׁית", "lemma": "רֵאשִׁית", "pos": "noun", "morphology": "construct, feminine, singular", "transliteration": "bereshit", "definition": "beginning, first, head"},

            # Proverbs 3:5 (Trust, batach)
            {"verse": "Proverbs 3:5", "surface": "Trust", "lemma": "בָּטַח", "pos": "verb", "morphology": "qal, imperative", "transliteration": "batach", "definition": "to trust, to rely on, to lean upon, to be secure, to have confidence"},

            # John 19:30 (Accomplished, teleioo)
            {"verse": "John 19:30", "surface": "Accomplished", "lemma": "τελειόω", "pos": "verb", "morphology": "aorist, active, indicative", "transliteration": "teleioo", "definition": "to accomplish, to complete, to finish, to make perfect"},
            {"verse": "John 19:30", "surface": "τετέλεσται", "lemma": "τελειόω", "pos": "verb", "morphology": "perfect, active, indicative, 3rd singular", "transliteration": "tetelestai", "definition": "it is finished, it is completed"},

            # John 19:39 (myrrh, smyrna)
            {"verse": "John 19:39", "surface": "myrrh", "lemma": "σμύρνα", "pos": "noun", "morphology": "nominative, singular, feminine", "transliteration": "smyrna", "definition": "myrrh, a fragrant resin used for anointing and burial"},

            # Luke 17:21 (within, entos)
            {"verse": "Luke 17:21", "surface": "within", "lemma": "ἐντός", "pos": "preposition", "morphology": "---", "transliteration": "entos", "definition": "within, inside, among, in the midst of"},
            {"verse": "Luke 17:21", "surface": "ἐντὸς", "lemma": "ἐντός", "pos": "preposition", "morphology": "---", "transliteration": "entos", "definition": "within, inside, among, in the midst of"},
            {"verse": "Luke 17:21", "surface": "kingdom", "lemma": "βασιλεία", "pos": "noun", "morphology": "nominative, singular, feminine", "transliteration": "basileia", "definition": "kingdom, reign, domain, dominion"},
        ]

        # Index the sample data
        for entry in sample_entries:
            lemma = entry["lemma"]
            surface = entry["surface"]
            verse = entry["verse"]

            # Store in lemma index
            self.greek_lemmas[lemma] = {
                "pos": entry["pos"],
                "morphology": entry["morphology"],
                "transliteration": entry["transliteration"],
                "definition": entry["definition"],
                "surface_forms": [surface]
            }

            # Index by surface form for lookup
            if surface not in self.greek_index[surface]:
                self.greek_index[surface].append(lemma)

            # Store verse mapping
            self.verses[verse].append({
                "surface": surface,
                "lemma": lemma,
                "pos": entry["pos"],
                "morphology": entry["morphology"],
                "transliteration": entry["transliteration"],
                "definition": entry["definition"]
            })

    def lookup_word(self, word: str, verse: Optional[str] = None) -> Optional[Dict]:
        """
        Look up a word in the lexicon.

        Args:
            word: The Greek/Hebrew word to look up
            verse: Optional verse for context (e.g., "John 1:1")

        Returns:
            Dictionary with morphological data or None if not found
        """
        # Normalize the word
        word_normalized = word.strip().lower()

        # Try direct lemma match first
        if word_normalized in self.greek_lemmas:
            return self.greek_lemmas[word_normalized]

        # Try surface form match
        for surface_form, lemmas in self.greek_index.items():
            if surface_form.lower() == word_normalized:
                if lemmas:
                    lemma = lemmas[0]
                    return self.greek_lemmas.get(lemma)

        # Try substring match (for words with punctuation)
        word_clean = word_normalized.rstrip('.,;:')
        if word_clean in self.greek_lemmas:
            return self.greek_lemmas[word_clean]

        return None

    def get_verse_words(self, verse: str) -> List[Dict]:
        """Get all words in a specific verse with morphological data."""
        return self.verses.get(verse, [])

    def get_transliteration(self, word: str) -> Optional[str]:
        """Get transliteration of a word."""
        result = self.lookup_word(word)
        return result["transliteration"] if result else None

    def get_definition(self, word: str) -> Optional[str]:
        """Get definition of a word."""
        result = self.lookup_word(word)
        return result["definition"] if result else None


# Singleton instance
_lexicon = None

def get_lexicon() -> MorphologicalLexicon:
    """Get or create the morphological lexicon."""
    global _lexicon
    if _lexicon is None:
        _lexicon = MorphologicalLexicon()
    return _lexicon
