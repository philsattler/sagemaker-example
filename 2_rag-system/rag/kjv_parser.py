"""
Parse Project Gutenberg KJV Bible text into JSON corpus format.
Uses standard 66-book Bible order for unambiguous book detection.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


# Standard 66-book Bible order with common header variations
BOOKS_OT = [
    ("Genesis", ["The First Book of Moses: Called Genesis"]),
    ("Exodus", ["The Second Book of Moses: Called Exodus"]),
    ("Leviticus", ["The Third Book of Moses: Called Leviticus"]),
    ("Numbers", ["The Fourth Book of Moses: Called Numbers"]),
    ("Deuteronomy", ["The Fifth Book of Moses: Called Deuteronomy"]),
    ("Joshua", ["The Book of Joshua"]),
    ("Judges", ["The Book of Judges"]),
    ("Ruth", ["The Book of Ruth"]),
    ("1 Samuel", ["The First Book of Samuel", "1 Samuel"]),
    ("2 Samuel", ["The Second Book of Samuel", "2 Samuel"]),
    ("1 Kings", ["The First Book of the Kings", "1 Kings"]),
    ("2 Kings", ["The Second Book of the Kings", "2 Kings"]),
    ("1 Chronicles", ["The First Book of the Chronicles", "1 Chronicles"]),
    ("2 Chronicles", ["The Second Book of the Chronicles", "2 Chronicles"]),
    ("Ezra", ["The Book of Ezra"]),
    ("Nehemiah", ["The Book of Nehemiah"]),
    ("Esther", ["The Book of Esther"]),
    ("Job", ["The Book of Job"]),
    ("Psalms", ["The Book of Psalms"]),
    ("Proverbs", ["The Book of Proverbs"]),
    ("Ecclesiastes", ["Ecclesiastes"]),
    ("Song of Solomon", ["The Song of Solomon"]),
    ("Isaiah", ["The Book of the Prophet Isaiah"]),
    ("Jeremiah", ["The Book of the Prophet Jeremiah"]),
    ("Lamentations", ["Lamentations of Jeremiah"]),
    ("Ezekiel", ["The Book of the Prophet Ezekiel"]),
    ("Daniel", ["The Book of Daniel"]),
    ("Hosea", ["Hosea"]),
    ("Joel", ["Joel"]),
    ("Amos", ["Amos"]),
    ("Obadiah", ["Obadiah"]),
    ("Jonah", ["Jonah"]),
    ("Micah", ["Micah"]),
    ("Nahum", ["Nahum"]),
    ("Habakkuk", ["Habakkuk"]),
    ("Zephaniah", ["Zephaniah"]),
    ("Haggai", ["Haggai"]),
    ("Zechariah", ["Zechariah"]),
    ("Malachi", ["Malachi"]),
]

BOOKS_NT = [
    ("Matthew", ["The Gospel According to Saint Matthew"]),
    ("Mark", ["The Gospel According to Saint Mark"]),
    ("Luke", ["The Gospel According to Saint Luke"]),
    ("John", ["The Gospel According to Saint John"]),
    ("Acts", ["The Acts of the Apostles"]),
    ("Romans", ["The Epistle of Paul the Apostle to the Romans"]),
    ("1 Corinthians", ["The First Epistle of Paul the Apostle to the Corinthians"]),
    ("2 Corinthians", ["The Second Epistle of Paul the Apostle to the Corinthians"]),
    ("Galatians", ["The Epistle of Paul the Apostle to the Galatians"]),
    ("Ephesians", ["The Epistle of Paul the Apostle to the Ephesians"]),
    ("Philippians", ["The Epistle of Paul the Apostle to the Philippians"]),
    ("Colossians", ["The Epistle of Paul the Apostle to the Colossians"]),
    ("1 Thessalonians", ["The First Epistle of Paul the Apostle to the Thessalonians"]),
    ("2 Thessalonians", ["The Second Epistle of Paul the Apostle to the Thessalonians"]),
    ("1 Timothy", ["The First Epistle of Paul the Apostle to Timothy"]),
    ("2 Timothy", ["The Second Epistle of Paul the Apostle to Timothy"]),
    ("Titus", ["The Epistle of Paul the Apostle to Titus"]),
    ("Philemon", ["The Epistle of Paul the Apostle to Philemon"]),
    ("Hebrews", ["The Epistle of Paul the Apostle to the Hebrews"]),
    ("James", ["The General Epistle of James"]),
    ("1 Peter", ["The First Epistle General of Peter"]),
    ("2 Peter", ["The Second General Epistle of Peter"]),
    ("1 John", ["The First Epistle General of John"]),
    ("2 John", ["The Second Epistle General of John"]),
    ("3 John", ["The Third Epistle General of John"]),
    ("Jude", ["The General Epistle of Jude"]),
    ("Revelation", ["The Revelation of Saint John the Divine"]),
]

BOOKS = BOOKS_OT + BOOKS_NT


class KJVParserV2:
    """Parse KJV Bible text file using standard book order."""

    def __init__(self, input_path: str, output_path: str = "data/kjv_corpus_full.json"):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.corpus: Dict[str, str] = {}
        self.verses_metadata: List[Dict] = []

        # Build header → book name mapping
        self.header_to_book = {}
        for canonical_name, headers in BOOKS:
            for header in headers:
                self.header_to_book[header] = canonical_name

    def parse(self) -> int:
        """Parse the KJV text file into corpus."""
        print(f"📖 Parsing {self.input_path}...")

        with open(self.input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove Project Gutenberg header/footer
        if "*** START OF THE PROJECT GUTENBERG" in content:
            content = content.split("*** START OF THE PROJECT GUTENBERG EBOOK")[1]
        if "*** END OF THE PROJECT GUTENBERG" in content:
            content = content.split("*** END OF THE PROJECT GUTENBERG")[0]

        lines = content.split('\n')

        current_book = None
        current_verse_ref = None
        current_verse_text = []
        verse_count = 0

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                if current_verse_text and current_verse_ref and current_book:
                    self._save_verse(current_book, current_verse_ref, current_verse_text)
                    current_verse_text = []
                continue

            # Skip junk
            if "***" in line_stripped or "gutenberg" in line_stripped.lower():
                continue

            # Check if this line is a known book header
            if line_stripped in self.header_to_book:
                # Save previous verse
                if current_verse_text and current_verse_ref and current_book:
                    self._save_verse(current_book, current_verse_ref, current_verse_text)
                    current_verse_text = []

                current_book = self.header_to_book[line_stripped]
                print(f"  📚 {current_book}")
                continue

            # Match verse format: "1:1 text"
            if re.match(r'^\d+:\d+', line_stripped) and current_book:
                # Save previous verse if exists
                if current_verse_text and current_verse_ref:
                    self._save_verse(current_book, current_verse_ref, current_verse_text)

                # Parse verse reference
                match = re.match(r'^(\d+):(\d+)\s+(.*)', line_stripped)
                if match:
                    chapter, verse, text = match.groups()
                    current_verse_ref = f"{current_book} {chapter}:{verse}"
                    current_verse_text = [text]
                    verse_count += 1

            elif current_verse_text and current_book:
                # Continuation of previous verse
                if line_stripped:
                    current_verse_text.append(line_stripped)

        # Save last verse
        if current_verse_text and current_verse_ref and current_book:
            self._save_verse(current_book, current_verse_ref, current_verse_text)

        print(f"\n✅ Parsed {verse_count} verses from {len(set(v['book'] for v in self.verses_metadata))} books")
        return verse_count

    def _save_verse(self, book: str, verse_ref: str, text_lines: List[str]) -> None:
        """Save a parsed verse."""
        verse_text = " ".join(text_lines).strip()
        verse_text = " ".join(verse_text.split())

        match = re.search(r'(\d+):(\d+)', verse_ref)
        if match:
            chapter, verse = match.groups()

            self.corpus[verse_ref] = verse_text
            self.verses_metadata.append({
                "book": book,
                "chapter": int(chapter),
                "verse": int(verse),
                "reference": verse_ref,
                "text": verse_text
            })

    def save_corpus(self) -> None:
        """Save corpus to JSON file."""
        corpus_data = {
            "metadata": {
                "translation": "KJV (King James Version)",
                "source": "Project Gutenberg",
                "total_verses": len(self.corpus),
                "books": sorted(list(set(v["book"] for v in self.verses_metadata)))
            },
            "verses": self.corpus,
            "verses_detailed": self.verses_metadata
        }

        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(corpus_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved to {self.output_path}")
        file_size = self.output_path.stat().st_size / 1024 / 1024
        print(f"   File size: {file_size:.2f} MB")
        print(f"   Total verses: {len(self.corpus)}")
        print(f"   Books: {len(set(v['book'] for v in self.verses_metadata))}")

    def show_sample(self) -> None:
        """Show sample verses."""
        if not self.corpus:
            return

        print("\n📖 Sample verses from full corpus:")
        sample = list(self.corpus.items())[:5]
        for ref, text in sample:
            print(f"\n  {ref}:")
            print(f"    {text[:80]}...")


if __name__ == "__main__":
    parser = KJVParserV2("data/kjv_bible.txt")
    parser.parse()
    parser.save_corpus()
    parser.show_sample()
