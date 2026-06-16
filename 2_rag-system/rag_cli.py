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

Ask questions about the KJV Bible (23,120 verses).

Usage:
    python rag_cli.py "Your question here?" [--k 5]

Options:
    --k N       Return N results (default: 3)

Examples:
    python rag_cli.py "What does the Bible say about trust?"
    python rag_cli.py "Tell me about creation"
    python rag_cli.py "What does it say about love?" --k 5
    python rag_cli.py "Show me verses about faith"

The system will retrieve relevant passages from the KJV corpus
and display them with relevance scores.
        """)
        return 0

    # Parse arguments
    args = sys.argv[1:]
    k = 3

    # Extract k value if provided
    for i, arg in enumerate(args):
        if arg == "--k" and i + 1 < len(args):
            try:
                k = int(args[i + 1])
                args.remove("--k")
                args.remove(str(k))
            except (ValueError, IndexError):
                pass

    # Build question from remaining args
    question = " ".join([arg for arg in args if not arg.startswith("--")])

    # Initialize RAG (uses full corpus by default)
    print(f"\n🔄 Loading RAG system (KJV corpus - 23,120 verses)...")
    rag = SimpleRAG()

    # Answer question
    print(f"\n🤔 Processing: {question}\n")
    results = rag.answer_question(question, k=k)

    # Display results
    rag.print_results(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
