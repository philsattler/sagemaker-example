"""
Strong's Concordance & Hebrew Lexicon Database.

This uses freely available Open BDB (Brown-Driver-Briggs) lexicon data.
"""

# Key Hebrew words we'll use for MVP
HEBREW_LEXICON = {
    # Genesis 1:1
    "H7225": {
        "hebrew": "רֵאשִׁית",
        "transliteration": "reshit",
        "morphology": "noun, feminine, singular",
        "strongs_definition": "Beginning, first, head, top, principal",
        "theological_notes": "Represents primacy and foundation. In Genesis, indicates God's starting point of creation.",
        "root": "H7218",
        "frequency": 51,
    },
    "H1254": {
        "hebrew": "בָּרָא",
        "transliteration": "bara",
        "morphology": "verb, qal perfect, masculine singular",
        "strongs_definition": "To create, shape, form (divine creative act)",
        "theological_notes": "Used exclusively for God's creative action. Implies something brought into existence from nothing (creatio ex nihilo). Never used for human creation.",
        "root": "H1254",
        "frequency": 48,
    },
    "H8064": {
        "hebrew": "שָׁמַיִם",
        "transliteration": "shamayim",
        "morphology": "noun, masculine, plural",
        "strongs_definition": "Heavens, sky, the upper regions",
        "theological_notes": "Always plural in Hebrew, suggesting the vastness and majesty of creation. Represents God's realm.",
        "root": "H8064",
        "frequency": 421,
    },
    "H776": {
        "hebrew": "אֶרֶץ",
        "transliteration": "eretz",
        "morphology": "noun, feminine, singular",
        "strongs_definition": "Earth, land, ground, soil",
        "theological_notes": "The material creation, the domain of humanity. Emphasizes God's sovereignty over the physical world.",
        "root": "H776",
        "frequency": 2505,
    },
    # John 1:1
    "G3056": {
        "greek": "λόγος",
        "transliteration": "logos",
        "morphology": "noun, masculine, singular, nominative",
        "strongs_definition": "A word; utterance; the Divine Reason, the Word (Jesus Christ)",
        "theological_notes": "Greek philosophical term adopted by John. Represents God's self-expression, divine reason, and ultimate revelation. Central to Johannine theology.",
        "root": "G3056",
        "frequency": 330,
    },
    "G5342": {
        "greek": "φέρω",
        "transliteration": "phero",
        "morphology": "verb, present active",
        "strongs_definition": "To carry, bear, bring forth",
        "theological_notes": "Often used of spiritual bearing or testimony. In John 1:16, 'grace upon grace' suggests an overflowing abundance.",
        "root": "G5342",
        "frequency": 66,
    },
    # Proverbs 3:5
    "H3820": {
        "hebrew": "לֵב",
        "transliteration": "lev",
        "morphology": "noun, masculine, singular",
        "strongs_definition": "Heart, mind, will, inner self",
        "theological_notes": "In Hebrew thought, the heart is the center of intellect, emotion, and will - not just emotion. Complete devotion involves all faculties.",
        "root": "H3820",
        "frequency": 853,
    },
    "H982": {
        "hebrew": "בָּטַח",
        "transliteration": "batach",
        "morphology": "verb, qal imperative, masculine singular",
        "strongs_definition": "To trust, rely on, lean upon, be secure",
        "theological_notes": "Active trust that involves commitment and reliance. Biblical trust includes action, not just passive belief.",
        "root": "H982",
        "frequency": 120,
    },
}

# Thematic mappings for cross-references
THEOLOGICAL_THEMES = {
    "creation": ["H1254", "H7225", "H8064", "H776"],
    "word_of_god": ["H1697", "G3056"],
    "divine_utterance": ["H1697", "H7121", "G3056", "G4487"],
    "trust_faith": ["H982", "H539", "G4100"],
    "beginning_first": ["H7225", "H8462"],
}

# Strong's number to verse mapping (simplified)
STRONGS_TO_VERSES = {
    "H1254": [
        {"book": "Genesis", "chapter": 1, "verse": 1, "text": "In the beginning God created the heaven and the earth"},
        {"book": "Genesis", "chapter": 1, "verse": 21, "text": "And God created great whales, and every living creature that moveth"},
        {"book": "Genesis", "chapter": 1, "verse": 27, "text": "So God created man in his own image, in the image of God created he him"},
        {"book": "Isaiah", "chapter": 45, "verse": 7, "text": "I form the light, and create darkness"},
        {"book": "Psalm", "chapter": 51, "verse": 10, "text": "Create in me a clean heart, O God"},
    ],
    "G3056": [
        {"book": "John", "chapter": 1, "verse": 14, "text": "And the Word was made flesh, and dwelt among us"},
        {"book": "Hebrews", "chapter": 1, "verse": 3, "text": "Who being the brightness of his glory, and the express image of his person, and upholding all things by the word of his power"},
        {"book": "Revelation", "chapter": 19, "verse": 13, "text": "And he was clothed with a vesture dipped in blood: and his name is called The Word of God"},
    ],
    "H982": [
        {"book": "Proverbs", "chapter": 3, "verse": 5, "text": "Trust in the LORD with all thine heart; and lean not unto thine own understanding"},
        {"book": "Psalm", "chapter": 37, "verse": 3, "text": "Trust in the LORD, and do good; so shalt thou dwell in the land"},
        {"book": "Isaiah", "chapter": 26, "verse": 3, "text": "Thou wilt keep him in perfect peace, whose mind is stayed on thee: because he trusteth in thee"},
    ],
}

def get_word_definition(strongs_number: str) -> dict:
    """Get definition for a Strong's number."""
    return HEBREW_LEXICON.get(strongs_number, {})

def get_verses_with_word(strongs_number: str) -> list:
    """Get all verses using a specific Strong's number word."""
    return STRONGS_TO_VERSES.get(strongs_number, [])

def get_theme_words(theme: str) -> list:
    """Get Strong's numbers for a theological theme."""
    return THEOLOGICAL_THEMES.get(theme, [])
