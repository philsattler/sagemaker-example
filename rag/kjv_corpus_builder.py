"""
Build a local KJV Bible corpus by fetching from bible-api.com and caching.
"""

import json
import requests
from pathlib import Path
from typing import Dict, List

class KJVCorpusBuilder:
    """Download and cache KJV Bible verses."""

    API_BASE = "https://bible-api.com"

    # Key books to fetch for the RAG system
    # Format: "Book": (chapter_count, verses_per_chapter_estimate)
    BOOKS = {
        "Genesis": 50,
        "Psalms": 150,
        "John": 21,
        "Romans": 16,
        "Proverbs": 31,
    }

    def __init__(self, output_path: str = "data/kjv_corpus.json"):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.corpus: Dict[str, str] = {}
        self.verses_metadata: List[Dict] = []

    def fetch_verse(self, book: str, chapter: int, verse: int) -> str:
        """Fetch a single verse from bible-api.com."""
        try:
            url = f"{self.API_BASE}/{book}+{chapter}:{verse}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("text", "").strip()
            return ""
        except Exception as e:
            print(f"  Error fetching {book} {chapter}:{verse}: {e}")
            return ""

    def build_corpus(self) -> Dict[str, str]:
        """Download all verses for configured books."""
        total_verses = 0
        failed_verses = 0

        print("Building KJV corpus from bible-api.com...")

        for book, chapters in self.BOOKS.items():
            print(f"\nFetching {book}...")
            for chapter in range(1, chapters + 1):
                # Most chapters have 20-30 verses, try up to 200 to be safe
                for verse in range(1, 200):
                    text = self.fetch_verse(book, chapter, verse)

                    if not text:
                        # Stop at first missing verse (end of chapter)
                        break

                    # Store by reference
                    ref = f"{book} {chapter}:{verse}"
                    self.corpus[ref] = text

                    # Store metadata for RAG
                    self.verses_metadata.append({
                        "book": book,
                        "chapter": chapter,
                        "verse": verse,
                        "reference": ref,
                        "text": text
                    })

                    total_verses += 1

                    # Progress indicator
                    if total_verses % 100 == 0:
                        print(f"  Downloaded {total_verses} verses...")

                # Small delay between chapters to be respectful to the API
                import time
                time.sleep(0.1)

        print(f"\n✅ Downloaded {total_verses} verses")
        return self.corpus

    def save_corpus(self) -> None:
        """Save corpus to JSON file."""
        corpus_data = {
            "metadata": {
                "translation": "KJV",
                "total_verses": len(self.corpus),
                "books": list(self.BOOKS.keys())
            },
            "verses": self.corpus,
            "verses_detailed": self.verses_metadata
        }

        with open(self.output_path, 'w') as f:
            json.dump(corpus_data, f, indent=2)

        print(f"💾 Saved to {self.output_path}")
        print(f"   File size: {self.output_path.stat().st_size / 1024 / 1024:.2f} MB")

    def load_corpus(self) -> Dict[str, str]:
        """Load existing corpus from file."""
        if not self.output_path.exists():
            raise FileNotFoundError(f"Corpus not found at {self.output_path}")

        with open(self.output_path, 'r') as f:
            data = json.load(f)

        self.corpus = data.get("verses", {})
        self.verses_metadata = data.get("verses_detailed", [])

        print(f"✅ Loaded {len(self.corpus)} verses from {self.output_path}")
        return self.corpus


if __name__ == "__main__":
    builder = KJVCorpusBuilder()

    # Check if corpus already exists
    import os
    if os.path.exists("data/kjv_corpus.json"):
        print("Corpus already exists, loading...")
        builder.load_corpus()
    else:
        print("Building new corpus...")
        builder.build_corpus()
        builder.save_corpus()

    # Show sample
    sample = list(builder.corpus.items())[:5]
    print("\nSample verses:")
    for ref, text in sample:
        print(f"  {ref}: {text[:60]}...")
