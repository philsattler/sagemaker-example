# 📚 Bible Q&A RAG System

Retrieval-Augmented Generation (RAG) system for answering questions about the King James Version Bible using hybrid search (BM25 + semantic embeddings).

## How It Works

```
User Query
    ↓
Semantic Embedding (SentenceTransformers)
    ↓
BM25 Keyword Search
    ↓
Hybrid Scoring (avg of both)
    ↓
Top-k Relevant Verses
    ↓
Display Results with Relevance Scores
```

## Quick Start

```bash
# Ask a question
python rag_cli.py "What does the Bible say about faith?"

# Get more results
python rag_cli.py "Tell me about creation" --k 5

# Help
python rag_cli.py --help
```

## Key Features

- **23,673 verses** from KJV Bible
- **Hybrid retrieval**: combines semantic + keyword search
- **Fast**: ~100ms per query
- **No API needed**: everything runs locally
- **Extensible**: easy to add other documents

## Architecture

**Initialization (first load)**:
1. Load KJV corpus from `data/kjv_corpus_full.json`
2. Initialize SentenceTransformer model (384-dim embeddings)
3. Build BM25 keyword index
4. Cache embeddings for fast loading

**Query Processing**:
1. Embed query with SentenceTransformer
2. Compute cosine similarity with all verses
3. Compute BM25 scores
4. Average both scores
5. Return top-k ranked verses

## Performance

| Metric | Value |
|--------|-------|
| Total verses | 23,673 |
| Embedding dimension | 384 |
| Query time | ~100ms |
| Cache size | 11MB |
| Embedding model | all-MiniLM-L6-v2 |

## Files

- `rag_cli.py` - Command-line interface
- `rag/simple_rag.py` - Core RAG system
- `rag/my_simple_rag.py` - Variant with separate scoring
- `rag/kjv_parser.py` - Parser for KJV text files
- `data/kjv_bible.txt` - Source KJV text (Project Gutenberg)
- `data/kjv_corpus_full.json` - Structured corpus with embeddings

## Concepts

- **RAG**: Retrieve relevant documents, then generate answers
- **Semantic Similarity**: Meaning-based search using embeddings
- **BM25**: Keyword-based ranking (inverse document frequency)
- **Hybrid Search**: Combine both methods for best coverage

## See Also

- [Full architecture guide](ARCHITECTURE.md)
- [SageMaker MLOps](../1_sagemaker-mlops/)
- [Spark Learning](../3_spark-learning/)
