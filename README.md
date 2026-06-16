# 🏗️ Python Data Engineering Projects

A collection of three independent but interconnected projects demonstrating modern data engineering, machine learning, and distributed computing concepts.

## 📂 Projects

### 1️⃣ [SageMaker MLOps Pipeline](./1_sagemaker-mlops/)
End-to-end machine learning pipeline using AWS SageMaker for training and inference. Demonstrates model orchestration, containerization, and cloud deployment.

**Use this to learn about:**
- AWS SageMaker training jobs
- Docker containerization
- Model versioning and registry
- Endpoint management
- Infrastructure as Code (IAC)

**Get started:**
```bash
cd 1_sagemaker-mlops
python agent.py --model xgbregressor
```

---

### 2️⃣ [Bible Q&A RAG System](./2_rag-system/)
Retrieval-Augmented Generation system for semantic search over the KJV Bible. Combines BM25 keyword search with neural embeddings for intelligent document retrieval.

**Use this to learn about:**
- Vector embeddings (SentenceTransformers)
- Hybrid search (semantic + keyword)
- RAG architecture
- Information retrieval
- Semantic similarity

**Get started:**
```bash
cd 2_rag-system
python rag_cli.py "What does the Bible say about faith?"
```

---

### 3️⃣ [Spark Learning: Distributed Computing](./3_spark-learning/)
Self-paced tutorial for learning Apache Spark and distributed computing fundamentals. Process large datasets across multiple CPU cores with the same code that scales to cloud clusters.

**Use this to learn about:**
- Apache Spark architecture
- Partitioning and parallelization
- MapReduce pattern
- Lazy evaluation
- Scaling from laptop to cloud

**Get started:**
```bash
cd 3_spark-learning
# Follow YOUR_LEARNING_STRUCTURE.md and QUICK_START.md
spark-submit spark_embedding_simple.py
```

---

## 🗂️ Repository Structure

```
.
├── README.md                    # This file
├── pyproject.toml              # Python dependencies (uv)
├── docs/                        # Shared documentation
│   ├── CLAUDE.md               # Project instructions
│   └── ARCHITECTURE.md         # System design
│
├── 1_sagemaker-mlops/          # AWS ML Pipeline
│   ├── README.md
│   ├── agent.py
│   ├── controller.py
│   ├── models/
│   ├── training/
│   ├── inference/
│   └── .github/workflows/
│
├── 2_rag-system/               # Bible Q&A RAG
│   ├── README.md
│   ├── rag_cli.py
│   ├── rag/
│   ├── data/
│   └── ARCHITECTURE.md
│
├── 3_spark-learning/           # Distributed Computing
│   ├── README.md
│   ├── spark_embedding_simple.py
│   ├── convert_parquet_to_csv.py
│   ├── analyze_results.py
│   ├── QUICK_START.md
│   ├── SPARK_LEARNING_MAP.md
│   └── data/
│
├── docker/                      # Shared Docker image
│   └── Dockerfile
│
└── tests/                       # Shared tests
```

---

## 🚀 Quick Navigation

| Project | Learn | Time | Difficulty |
|---------|-------|------|-----------|
| **SageMaker** | AWS cloud ML | 2-4 hours | Intermediate |
| **RAG System** | Semantic search | 1-2 hours | Beginner-Intermediate |
| **Spark** | Distributed computing | 2-3 hours | Intermediate-Advanced |

---

## 🛠️ Setup

### Prerequisites
- Python 3.13+
- `uv` package manager
- AWS credentials (for SageMaker only)
- Java (for Spark)

### Install Dependencies
```bash
uv sync
```

### Environment Variables
```bash
# For SageMaker (optional)
export AWS_REGION=us-east-1
export SAGEMAKER_ROLE_ARN=arn:aws:iam::ACCOUNT:role/SageMakerRole

# For Spark (optional)
export JAVA_HOME=/path/to/java
```

---

## 📚 Learning Paths

### Path 1: Complete Beginner
1. Start with RAG System (concept-rich, no cloud)
2. Move to Spark (understand data distribution)
3. Finally SageMaker (orchestrate it all)

### Path 2: ML-Focused
1. Start with SageMaker (production ML)
2. Understand RAG (advanced retrieval)
3. Learn Spark (process training data at scale)

### Path 3: Data Engineering-Focused
1. Start with Spark (fundamentals)
2. Move to RAG (real-world retrieval)
3. Understand SageMaker (ML ops)

---

## 🎓 What You'll Learn

Across all three projects, you'll master:

- ✅ **Cloud ML**: Training, inference, endpoints
- ✅ **Semantic Search**: Embeddings, similarity, retrieval
- ✅ **Distributed Computing**: Partitioning, MapReduce, scaling
- ✅ **Data Processing**: ETL, transformation, aggregation
- ✅ **Production Systems**: Containerization, monitoring, versioning
- ✅ **Modern Python**: Type hints, async, testing

---

## 🔗 Connections

These projects are *independent* but *connected*:

```
SageMaker could use RAG output for training data
    ↓
RAG could use embeddings from SageMaker models
    ↓
Spark could process data for both systems at scale
```

You can work on any project independently or combine them!

---

## 📖 Documentation

- [Project Instructions](./docs/CLAUDE.md) - Original design docs
- [1_sagemaker-mlops/README.md](./1_sagemaker-mlops/README.md) - ML pipeline guide
- [2_rag-system/README.md](./2_rag-system/README.md) - RAG system guide
- [3_spark-learning/README.md](./3_spark-learning/README.md) - Spark tutorial

---

## 💡 Next Steps

1. Pick a project that interests you
2. Read its README.md
3. Follow the "Get started" instructions
4. For Spark: Follow the learning guides in `3_spark-learning/`

Happy learning! 🚀
# Retry
# test
