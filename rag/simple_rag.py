"""
Simple Document Q&A RAG System using KJV Bible corpus.
Uses vector similarity search + Claude for answer generation.
"""

import json
import numpy as np
from typing import List, Dict, Tuple
from pathlib import Path


class SimpleRAG:
    """Simple RAG system for document Q&A."""

    def __init__(self, corpus_path: str = "data/kjv_corpus.json"):
        """Initialize RAG system with corpus."""
        self.corpus_path = Path(corpus_path)
        self.documents: List[Dict] = []
        self.embeddings: np.ndarray = None
        self._load_corpus()

    def _load_corpus(self) -> None:
        """Load documents from corpus file."""
        with open(self.corpus_path, 'r') as f:
            data = json.load(f)

        # Convert verses to documents
        for ref, text in data.get("verses", {}).items():
            self.documents.append({
                "reference": ref,
                "text": text,
                "book": ref.split()[0],
            })

        print(f"✅ Loaded {len(self.documents)} documents from corpus")

    def _simple_embedding(self, text: str) -> np.ndarray:
        """Create a simple embedding using word frequency (not ML-based)."""
        # This is a placeholder - in production we'd use Claude embeddings API
        # For now, use simple TF (term frequency) vector

        # Get unique words
        words = set(text.lower().split())

        # Create a fixed-size vector (hashing trick)
        embedding = np.zeros(100)
        for word in words:
            # Hash word to index
            idx = hash(word) % 100
            embedding[idx] += 1

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _compute_embeddings(self) -> None:
        """Compute embeddings for all documents."""
        embeddings = []
        for doc in self.documents:
            emb = self._simple_embedding(doc["text"])
            embeddings.append(emb)

        self.embeddings = np.array(embeddings)
        print(f"✅ Computed embeddings for {len(embeddings)} documents")

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[Dict, float]]:
        """Retrieve top-k relevant documents for a query."""
        if self.embeddings is None:
            self._compute_embeddings()

        # Embed the query
        query_emb = self._simple_embedding(query)

        # Compute similarity with all documents (cosine similarity)
        similarities = self.embeddings @ query_emb

        # Get top-k indices
        top_k_indices = np.argsort(similarities)[-k:][::-1]

        # Return documents with scores
        results = []
        for idx in top_k_indices:
            doc = self.documents[idx]
            score = float(similarities[idx])
            results.append((doc, score))

        return results

    def answer_question(self, question: str, k: int = 3) -> Dict:
        """Answer a question using retrieved context."""
        # Retrieve relevant documents
        retrieved = self.retrieve(question, k=k)

        # Build context
        context_text = "\n\n".join(
            [f"[{doc['reference']}] {doc['text']}" for doc, _ in retrieved]
        )

        context_docs = [
            {
                "reference": doc["reference"],
                "text": doc["text"],
                "relevance_score": score
            }
            for doc, score in retrieved
        ]

        return {
            "question": question,
            "retrieved_documents": context_docs,
            "context": context_text,
            "num_results": len(retrieved),
        }

    def print_results(self, results: Dict) -> None:
        """Pretty print Q&A results."""
        print(f"\n{'=' * 80}")
        print(f"Question: {results['question']}")
        print(f"{'=' * 80}\n")

        print(f"📖 Retrieved {results['num_results']} relevant passages:\n")
        for i, doc in enumerate(results["retrieved_documents"], 1):
            print(f"{i}. [{doc['reference']}] (relevance: {doc['relevance_score']:.2f})")
            print(f"   {doc['text']}\n")

        print(f"{'=' * 80}")


# Example usage
if __name__ == "__main__":
    rag = SimpleRAG()

    # Test queries
    test_queries = [
        "What does the Bible say about trust?",
        "Tell me about creation",
        "What does it say about love?",
    ]

    for query in test_queries:
        results = rag.answer_question(query, k=2)
        rag.print_results(results)
