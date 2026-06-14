"""
Simple Document Q&A RAG System using KJV Bible corpus.
Uses SentenceTransformers for semantic embeddings + vector similarity search.
"""

import json
import numpy as np
from typing import List, Dict, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer


class SimpleRAG:
    """Simple RAG system for document Q&A using semantic embeddings."""

    def __init__(self, corpus_path: str = "data/kjv_corpus.json"):
        """Initialize RAG system with corpus and embeddings model."""
        self.corpus_path = Path(corpus_path)
        self.documents: List[Dict] = []
        self.embeddings: np.ndarray = None

        # Initialize SentenceTransformers model (semantic embeddings)
        print("🤖 Loading SentenceTransformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Model loaded (384-dimensional semantic embeddings)")

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

    def _embed_text(self, text: str) -> np.ndarray:
        """Create semantic embedding using SentenceTransformer."""
        return self.model.encode(text, convert_to_numpy=True)

    def _compute_embeddings(self) -> None:
        """Compute semantic embeddings for all documents using SentenceTransformer."""
        texts = [doc["text"] for doc in self.documents]

        # Batch encode for efficiency
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

        self.embeddings = np.array(embeddings)
        print(f"✅ Computed {len(embeddings)} semantic embeddings (384-dim)")

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[Dict, float]]:
        """Retrieve top-k semantically relevant documents for a query."""
        if self.embeddings is None:
            self._compute_embeddings()

        # Embed the query semantically
        query_emb = self._embed_text(query)

        # Compute cosine similarity with all documents
        # Normalize for cosine similarity
        query_emb_norm = query_emb / np.linalg.norm(query_emb)
        embeddings_norm = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)

        similarities = embeddings_norm @ query_emb_norm

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
