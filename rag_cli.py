#!/usr/bin/env python3
"""
Simple CLI for KJV Bible Document Q&A RAG System.

Usage:
    python rag_cli.py "What does the Bible say about trust?"
    python rag_cli.py "Tell me about creation"
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag.simple_rag import SimpleRAG


def main():
    """Main CLI function."""
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "help"]:
        print("""
╔════════════════════════════════════════════════════════════════╗
║          KJV Bible Document Q&A RAG System                     ║
╚════════════════════════════════════════════════════════════════╝

Ask questions about the KJV Bible corpus.

Usage:
    python rag_cli.py "Your question here?"

Examples:
    python rag_cli.py "What does the Bible say about trust?"
    python rag_cli.py "Tell me about creation"
    python rag_cli.py "What does it say about love?"
    python rag_cli.py "Show me verses about faith"

The system will retrieve relevant passages from the KJV corpus
and display them with relevance scores.
        """)
        return 0

    question = " ".join(sys.argv[1:])

    # Initialize RAG
    print("\n🔄 Loading RAG system...")
    rag = SimpleRAG()

    # Answer question
    print(f"\n🤔 Processing: {question}\n")
    results = rag.answer_question(question, k=3)

    # Display results
    rag.print_results(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
