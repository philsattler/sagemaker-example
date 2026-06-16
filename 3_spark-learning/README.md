# ⚡ Spark Learning: Distributed Computing Tutorial

Complete self-paced learning system for understanding Apache Spark and distributed computing using the KJV Bible as sample data.

## What You'll Learn

✅ How partitioning distributes work across CPU cores  
✅ How `.map()` parallelizes operations  
✅ Lazy evaluation and when computation happens  
✅ The MapReduce pattern (foundation of Big Data)  
✅ How to scale from laptop to cloud (same code!)  

## Quick Start

```bash
# Run the Spark job (processes 23,673 verses in parallel)
spark-submit spark_embedding_simple.py

# Convert Parquet output to readable CSV
spark-submit convert_parquet_to_csv.py

# Analyze results with pure Python (no Spark needed!)
python3 analyze_results.py
```

## The 3-Command Workflow

```
Input Data (23,673 Bible verses)
    ↓
spark_embedding_simple.py (Spark job: parallelized)
    ↓
Parquet output (distributed format)
    ↓
convert_parquet_to_csv.py (format conversion)
    ↓
CSV file (human-readable)
    ↓
analyze_results.py (Python analysis)
    ↓
Statistics & Insights
```

## Learning Guides

1. **YOUR_LEARNING_STRUCTURE.md** - Start here!
   - Overview of what you have
   - How to use the system
   - Learning path

2. **SPARK_LEARNING_MAP.md** - Deep dive
   - Architecture with diagrams
   - Line-by-line code explanation
   - Key concepts

3. **QUICK_START.md** - Hands-on exercises
   - 5 exercises (Easy → Hard)
   - Step-by-step instructions
   - Questions to answer

## The Exercises

| # | Exercise | Difficulty | What You Learn | Time |
|---|----------|-----------|----------------|------|
| 1 | Run the workflow | Easy | The 3-command pattern | 5 min |
| 2 | Explore the code | Easy | How to read Spark code | 10 min |
| 3 | Add a metric | Medium | Modifying the function | 15 min |
| 4 | Filter data | Medium | `.filter()` operation | 10 min |
| 5 | Group by book | Hard | Data aggregation | 30 min |

## Key Files

- `spark_embedding_simple.py` - The main Spark job
  - Loads KJV corpus
  - Partitions across cores
  - Counts words in parallel
  - Saves to Parquet

- `convert_parquet_to_csv.py` - Format bridge
  - Reads Parquet
  - Writes CSV
  - Makes results readable

- `analyze_results.py` - Simple analysis
  - Pure Python (no Spark!)
  - Statistics, histograms
  - Shows you don't need Spark for final analysis

## Data

- Input: 23,673 Bible verses (KJV)
- Processing: Count words per verse in parallel
- Output: `data/spark_word_counts/` (Parquet) and CSV
- Result: Statistics showing longest verses, distributions, etc.

## Scaling to Cloud

Same code works on:
- **Local (your laptop)**: 0.3 seconds on 12 cores
- **AWS EMR (100 cores)**: 0.03 seconds (10x faster)
- **AWS EMR (1000 cores)**: 0.003 seconds (100x faster)

Just change `--master` parameter!

## Concepts Explained

**Partitioning**: Spark splits 23,673 verses across 12 cores automatically
```
Core 1: 1973 verses → process
Core 2: 1973 verses → process  (ALL AT SAME TIME!)
... (12 cores)
```

**Lazy Evaluation**: Code doesn't run until you ask for results
```
df.rdd.map(fn)  ← Just a plan, nothing happens yet
.count()         ← NOW Spark executes!
```

**MapReduce**: The pattern behind distributed computing
```
MAP:    Apply function to every item IN PARALLEL
REDUCE: Combine results (automatic in Spark)
```

## See Also

- [RAG System](../2_rag-system/)
- [SageMaker MLOps](../1_sagemaker-mlops/)

---

**Ready to learn?** Start with `YOUR_LEARNING_STRUCTURE.md`!
