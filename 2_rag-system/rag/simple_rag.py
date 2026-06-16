"""
Simple Document Q&A RAG System using KJV Bible corpus.
Hybrid retrieval: combines BM25 (keyword) + semantic embeddings.
"""

import json
import numpy as np
from typing import List, Dict, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi


class SimpleRAG:
    """Simple RAG system for document Q&A using semantic embeddings."""

    def __init__(self, corpus_path: str = "data/kjv_corpus_full.json"):
        """Initialize RAG system with corpus and embeddings model."""
        self.corpus_path = Path(corpus_path)
        self.documents: List[Dict] = []
        self.embeddings: np.ndarray = None
        self.bm25: BM25Okapi = None

        # Initialize SentenceTransformers model (semantic embeddings)
        print("🤖 Loading SentenceTransformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Model loaded (384-dimensional semantic embeddings)")

        self._load_corpus()
        self._initialize_bm25()

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

    def _initialize_bm25(self) -> None:
        """Initialize BM25 for keyword-based retrieval."""
        texts = [doc["text"] for doc in self.documents]
        # Tokenize by splitting on whitespace and lowercasing
        tokenized_texts = [text.lower().split() for text in texts]
        self.bm25 = BM25Okapi(tokenized_texts)
        print("✅ BM25 index built for hybrid retrieval")

    def _embed_text(self, text: str) -> np.ndarray:
        """Create semantic embedding using SentenceTransformer."""
        return self.model.encode(text, convert_to_numpy=True)

    def _compute_embeddings(self) -> None:
        """Compute semantic embeddings for all documents using SentenceTransformer."""
        embeddings_cache = Path("data/.embeddings_cache.npy")

        # Try to load from cache first
        if embeddings_cache.exists():
            print("📦 Loading cached embeddings...")
            self.embeddings = np.load(embeddings_cache)
            print(f"✅ Loaded {len(self.embeddings)} cached embeddings (384-dim)")
            return

        texts = [doc["text"] for doc in self.documents]

        # Batch encode for efficiency
        print("🔄 Computing embeddings (this may take a moment)...")
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

        self.embeddings = np.array(embeddings)

        # Cache for future runs
        embeddings_cache.parent.mkdir(exist_ok=True)
        np.save(embeddings_cache, self.embeddings)

        print(f"✅ Computed {len(embeddings)} semantic embeddings (384-dim)")
        print(f"💾 Cached to {embeddings_cache}")

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[Dict, float]]:
        """Retrieve top-k documents using hybrid BM25 + semantic search."""
        if self.embeddings is None:
            self._compute_embeddings()

        # Semantic scores (cosine similarity)
        query_emb = self._embed_text(query)
        query_emb_norm = query_emb / np.linalg.norm(query_emb)
        embeddings_norm = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        semantic_scores = embeddings_norm @ query_emb_norm

        # Normalize semantic scores to [0, 1]
        semantic_scores = (semantic_scores + 1) / 2

        # BM25 scores (keyword-based)
        query_tokens = query.lower().split()
        bm25_scores = np.array(self.bm25.get_scores(query_tokens))

        # Normalize BM25 scores to [0, 1]
        if bm25_scores.max() > 0:
            bm25_scores = bm25_scores / bm25_scores.max()

        # Hybrid score: average of both (equal weight)
        hybrid_scores = (semantic_scores + bm25_scores) / 2

        # Get top-k indices
        top_k_indices = np.argsort(hybrid_scores)[-k:][::-1]

        # Return documents with hybrid scores
        results = []
        for idx in top_k_indices:
            doc = self.documents[idx]
            score = float(hybrid_scores[idx])
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
