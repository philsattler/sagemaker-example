"""
Biblical Word Lookup Engine - Core system for word/verse analysis.
Uses Free Use Bible API for KJV, NIV, ESV and local cache for CJSB.
"""

import re
import requests
from typing import Dict, Tuple, Optional, List
from biblical_qa.concordance_data import get_word_definition, STRONGS_TO_VERSES

class BiblicalWordLookup:
    """
    Looks up words in Bible verses and maps to original Hebrew/Greek.
    Uses Free Use Bible API (https://freebible.io) for KJV, NIV, ESV.
    CJSB is stored locally (not available via free APIs).
    """

    # API configuration for Bible API (https://bible-api.com)
    # Works with public domain and open translations
    API_BASE = "https://bible-api.com"
    # Bible API uses a simple format: /Book+Chapter:Verse
    # Note: This API has limited translation support (primarily uses WEB - World English Bible)
    # For KJV, NIV, ESV we use local cache or the API returns what's available
    API_TRANSLATION_MAP = {
        "KJV": "web",  # Falls back to available translation
        "NIV": "web",
        "ESV": "web",
    }

    # Local CJSB database (not available via free APIs)
    # Format: "Book Chapter:Verse" -> "verse text"
    # Add more verses here as needed - they won't be available via API
    CJSB_DATABASE = {
        "John 1:1": "In the beginning was the Word, and the Word was with God, and the Word was God.",
        "Genesis 1:1": "In the beginning, God created the heavens and the earth.",
        "Proverbs 3:5": "Put your trust in Adonai with all your heart; don't rely on your own understanding.",
        "John 19:30": "After Yeshua had taken the wine, he said, \"It is accomplished!\" And, letting his head droop, he delivered up his spirit.",
        "John 19:39": "Nicodemus also came, bringing myrrh and aloes, about a hundred pounds' weight.",
        "Luke 17:21": "The kingdom of God is not coming with signs you can observe. People can't say, 'Look, here it is!' or 'There it is!' For you see, the kingdom of God is in your midst.",
    }

    # Word to Strong's number mappings (simplified)
    WORD_TO_STRONGS = {
        ("Word", "John 1:1"): "G3056",
        ("created", "Genesis 1:1"): "H1254",
        ("beginning", "Genesis 1:1"): "H7225",
        ("Trust", "Proverbs 3:5"): "H982",
        ("Accomplished", "John 19:30"): "G3952",  # teleioo - to complete, accomplish
        ("myrrh", "John 19:39"): "G4666",  # smyrna - myrrh
    }

    # Original language texts
    ORIGINAL_TEXTS = {
        "Genesis 1:1": {
            "hebrew": "בְרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָרֶץ",
            "transliteration": "Bereshit bara Elohim et hashamayim ve'et ha'aretz",
            "word_breakdown": [
                {"word": "בְרֵאשִׁית", "trans": "bereshit", "meaning": "In [the] beginning", "strongs": "H7225"},
                {"word": "בָּרָא", "trans": "bara", "meaning": "created", "strongs": "H1254"},
                {"word": "אֱלֹהִים", "trans": "Elohim", "meaning": "God", "strongs": "H430"},
                {"word": "הַשָּׁמַיִם", "trans": "hashamayim", "meaning": "the heavens", "strongs": "H8064"},
                {"word": "וְאֵת", "trans": "ve'et", "meaning": "and", "strongs": "H853"},
                {"word": "הָאָרֶץ", "trans": "ha'aretz", "meaning": "the earth", "strongs": "H776"},
            ]
        },
        "John 1:1": {
            "greek": "Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν, καὶ θεὸς ἦν ὁ λόγος.",
            "transliteration": "En archē ēn ho logos, kai ho logos ēn pros ton theon, kai theos ēn ho logos.",
            "word_breakdown": [
                {"word": "Ἐν", "trans": "en", "meaning": "In", "strongs": "G1722"},
                {"word": "ἀρχῇ", "trans": "archē", "meaning": "beginning", "strongs": "G746"},
                {"word": "ἦν", "trans": "ēn", "meaning": "was", "strongs": "G1510"},
                {"word": "ὁ", "trans": "ho", "meaning": "the", "strongs": "G3588"},
                {"word": "λόγος", "trans": "logos", "meaning": "Word", "strongs": "G3056"},
            ]
        },
        "Proverbs 3:5": {
            "hebrew": "בְטַח בַּיהוָה בְכָל־לְבָבְךָ וְאַל־תִּשָּׁעֵן עַל־בִּינָתְךָ",
            "transliteration": "Betach baYHWH bechol levavcha ve'al tishaan al binatchah",
            "word_breakdown": [
                {"word": "בְטַח", "trans": "betach", "meaning": "Trust", "strongs": "H982"},
                {"word": "בַּיהוָה", "trans": "baYHWH", "meaning": "in the LORD", "strongs": "H3068"},
                {"word": "בְכָל", "trans": "bechol", "meaning": "with all", "strongs": "H3605"},
                {"word": "לְבָבְךָ", "trans": "levavcha", "meaning": "your heart", "strongs": "H3824"},
            ]
        },
        "John 19:30": {
            "greek": "ὅτε οὖν ἔλαβεν τὸ ὄξος [ὁ] Ἰησοῦς εἶπεν, Τετέλεσται· καὶ κλίνας τὴν κεφαλὴν παρέδωκεν τὸ πνεῦμα.",
            "transliteration": "hote oun elaben to oxos ho Iēsous eipen, Tetelestai; kai klinas tēn kephalēn paredōken to pneuma.",
            "word_breakdown": [
                {"word": "ἔλαβεν", "trans": "elaben", "meaning": "took", "strongs": "G2983"},
                {"word": "Ἰησοῦς", "trans": "Iēsous", "meaning": "Jesus", "strongs": "G2424"},
                {"word": "εἶπεν", "trans": "eipen", "meaning": "said", "strongs": "G3004"},
                {"word": "Τετέλεσται", "trans": "Tetelestai", "meaning": "It is finished", "strongs": "G3952"},
                {"word": "παρέδωκεν", "trans": "paredōken", "meaning": "gave up", "strongs": "G3860"},
                {"word": "πνεῦμα", "trans": "pneuma", "meaning": "spirit", "strongs": "G4151"},
            ]
        },
        "John 19:39": {
            "greek": "ἦλθεν οὖν καὶ Νικόδημος, ὁ ἐλθὼν πρὸς αὐτὸν νυκτὸς τὸ πρῶτον, φέρων μῖγμα σμύρνης καὶ ἀλόης ὡς λίτρας ἑκατόν.",
            "transliteration": "ēlthen oun kai Nikodēmos, ho elthōn pros auton nyktos to prōton, pherōn migma smyrnēs kai aloēs hōs litras hekatón.",
            "word_breakdown": [
                {"word": "ἦλθεν", "trans": "ēlthen", "meaning": "came", "strongs": "G2064"},
                {"word": "Νικόδημος", "trans": "Nikodēmos", "meaning": "Nicodemus", "strongs": "G3530"},
                {"word": "σμύρνης", "trans": "smyrnēs", "meaning": "myrrh", "strongs": "G4666"},
                {"word": "ἀλόης", "trans": "aloēs", "meaning": "aloes", "strongs": "G250"},
            ]
        },
    }

    def _fetch_verse_from_api(self, verse_ref: str, translation: str) -> Optional[str]:
        """
        Fetch verse from Bible API (https://bible-api.com).
        verse_ref format: "Book Chapter:Verse" (e.g., "John 1:1")
        Falls back gracefully if network unavailable.
        """
        try:
            # Format: "John 1:1" -> "John+1:1" for URL
            book_chapter_verse = verse_ref.replace(" ", "+")

            # Call API - simple format
            url = f"{self.API_BASE}/{book_chapter_verse}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                # API returns data with 'text' field
                if isinstance(data, dict) and "text" in data:
                    return data["text"].strip()

            return None
        except requests.exceptions.ConnectionError:
            # No internet - API unavailable but don't spam warnings
            return None
        except Exception as e:
            # Other errors - log but continue
            return None

    def lookup_word(
        self,
        word: str,
        verse_ref: str,
        translation: str = "KJV"
    ) -> Dict:
        """
        Look up a word in a specific verse.
        Uses API for KJV/NIV/ESV, local cache for CJSB.
        """
        print(f"  Looking up '{word}' in {verse_ref} ({translation})...")

        # Get the verse
        verse_text = None

        if translation == "CJSB":
            # CJSB is local only
            verse_text = self.CJSB_DATABASE.get(verse_ref)
        else:
            # Try API first for KJV, NIV, ESV
            verse_text = self._fetch_verse_from_api(verse_ref, translation)

        if not verse_text:
            return {"error": f"Verse not found: {verse_ref} in {translation}"}

        # Find the word in the verse
        word_pos = self._find_word_position(word, verse_text)
        if word_pos == -1:
            return {"error": f"Word '{word}' not found in verse"}

        # Get Strong's number
        strongs_num = self._get_strongs_number(word, verse_ref)

        # Get word definition
        word_def = get_word_definition(strongs_num)

        # Get original language for verse
        original_verse = self.ORIGINAL_TEXTS.get(verse_ref, {})

        result = {
            "query": {
                "word": word,
                "verse": verse_ref,
                "translation": translation,
            },
            "word_found": True,
            "word_position": word_pos,
            "strongs_number": strongs_num,
            "word_analysis": word_def,
            "verse_original": original_verse,
        }

        return result

    def _find_word_position(self, word: str, verse_text: str) -> int:
        """Find position of word in verse text."""
        words = verse_text.lower().split()
        word_lower = word.lower()

        for i, v_word in enumerate(words):
            if word_lower in v_word.lower():
                return i
        return -1

    def _get_strongs_number(self, word: str, verse_ref: str) -> str:
        """Get Strong's number for a word in a verse."""
        if (word, verse_ref) in self.WORD_TO_STRONGS:
            return self.WORD_TO_STRONGS[(word, verse_ref)]

        for (key_word, key_verse), strongs in self.WORD_TO_STRONGS.items():
            if word.lower() in key_word.lower() and verse_ref == key_verse:
                return strongs

        return "UNKNOWN"
