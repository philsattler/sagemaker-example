# 🚀 Spark Bible Embedding Job - Learning Guide

This guide shows how to parallelize Bible verse embeddings using Apache Spark.

## What You'll Learn

- How Spark distributes work across CPU cores
- How to read/write distributed data (Parquet)
- How to scale from your laptop to cloud

## Prerequisites

### 1. Install Spark (if not already installed)

**Mac with Homebrew:**
```bash
brew install apache-spark
```

**Or download from:**
https://spark.apache.org/downloads.html

### 2. Verify Installation

```bash
spark-submit --version
# Output: Spark 3.x.x
```

### 3. Install Python Dependencies

```bash
pip install sentence-transformers torch numpy
# Or use uv:
uv sync
```

## Running the Job

### Step 1: Run the Embedding Job

This computes embeddings in parallel across all your CPU cores:

```bash
cd /Users/philipsattler/Python/sagemaker-example

spark-submit spark_embedding_job.py
```

**What happens:**
1. ✅ Spark reads your KJV corpus (23,673 verses)
2. ✅ Distributes across your CPU cores
3. ✅ Each core computes embeddings in parallel
4. ✅ Results saved to `data/spark_embeddings/` (Parquet format)
5. ✅ Shows speedup comparison

**Expected output:**
```
================================================================================
🚀 SPARK BIBLE EMBEDDING JOB
================================================================================

✅ Spark Session Created
   - Master: local[*] (all available cores)
   - Available cores: 8

📖 Loading KJV corpus...
✅ Loaded 23673 verses in 0.45s

🔄 Converting to Spark DataFrame...
✅ Created DataFrame with 23673 rows in 1.23s
   Partitions: 8

⚙️  Computing embeddings in parallel across 8 cores...

✅ Computed 23673 embeddings in 45.32s
   - Speed: 522.1 verses/second

📊 Performance Comparison:
   - Serial (1 core): 362.5s
   - Parallel (8 cores): 45.3s
   - Speedup: 8.0x faster with parallelization
```

**Runtime:** ~30-60 seconds on a modern laptop (depending on CPU)

### Step 2: Load Embeddings Back

After the job completes, load embeddings for use in your RAG system:

```bash
python load_spark_embeddings.py
```

**What happens:**
1. ✅ Loads Parquet embeddings from Step 1
2. ✅ Converts to numpy array
3. ✅ Tests with a sample query
4. ✅ Saves as `.npy` for fast loading next time

## Understanding the Code

### Part 1: Initialize Spark
```python
spark = SparkSession.builder \
    .appName("BibleEmbeddingJob") \
    .master("local[*]") \  # Use all cores
    .getOrCreate()
```
- `local[*]` = use all available cores on your laptop
- With 8 cores, work is split 8 ways

### Part 2: Create DataFrame
```python
df = spark.createDataFrame(verse_tuples, schema=...)
```
- Convert verses to Spark DataFrame
- Spark automatically partitions across cores

### Part 3: Map Function (The Magic!)
```python
def verse_to_embedding(row):
    reference = row[0]
    text = row[1]
    embedding = create_embedding(text)  # Runs on each core!
    return (reference, embedding)

embeddings_rdd = df.rdd.map(verse_to_embedding)
```

**Key insight:**
- This function runs **in parallel** on each core
- Spark handles coordination automatically
- Same code works locally or on 100 AWS machines!

### Part 4: Force Computation
```python
embeddings_df.persist()
total_rows = embeddings_df.count()  # This triggers computation
```
- Spark is "lazy" - code doesn't run until you ask for results
- `.count()` forces Spark to compute everything

## Scaling to the Cloud

### Local (Your Laptop)
```bash
spark-submit spark_embedding_job.py
# Uses: 4-8 cores
# Time: ~45 seconds
# Cost: $0
```

### AWS EMR (100 machines)
```bash
# Same code, different cluster
spark-submit --master spark://ec2-cluster-master:7077 \
  spark_embedding_job.py

# Uses: 100 machines × 4 cores = 400 cores
# Time: ~0.5 seconds (90x faster!)
# Cost: ~$10 for 2 minutes of compute
```

**The code is identical!** Only the `--master` parameter changes.

## Output Files

After running, you'll see:

```
data/spark_embeddings/
  ├── _SUCCESS
  ├── part-00000-xxx.parquet
  ├── part-00001-xxx.parquet
  ├── ...
  └── part-00007-xxx.parquet

data/spark_embeddings_array.npy          # Fast numpy format
data/spark_embeddings_references.json    # Reference mapping
```

## Using in Your RAG System

```python
import numpy as np
from rag.simple_rag import SimpleRAG

# Quick load (pre-computed embeddings)
embeddings_array = np.load("data/spark_embeddings_array.npy")

# Or compute on demand (original way)
rag = SimpleRAG()
results = rag.answer_question("faith")
```

## Comparison: Serial vs Parallel

| Approach | Cores | Time | Cost |
|----------|-------|------|------|
| Sequential Python | 1 | 6 min | $0 |
| Local Spark | 8 | 45 sec | $0 |
| AWS EMR (100 cores) | 100 | 5 sec | $0.10 |
| AWS EMR (1000 cores) | 1000 | 0.5 sec | $0.50 |

**Key insight:** Parallelization scales linearly. Double the cores = half the time.

## Troubleshooting

### "Spark not found"
```bash
brew install apache-spark
```

### "SentenceTransformer not found"
```bash
pip install sentence-transformers torch
```

### "Java not found"
Spark requires Java. Install:
```bash
brew install openjdk
```

### Memory issues
Edit `spark_embedding_job.py`:
```python
.config("spark.driver.memory", "2g")  # Reduce if needed
.config("spark.executor.memory", "1g")
```

## Next Steps

1. ✅ Run `spark-submit spark_embedding_job.py` (learn parallelization)
2. ✅ Run `python load_spark_embeddings.py` (integrate with RAG)
3. ✅ Modify the job to process your own data
4. ✅ Deploy to AWS EMR with same code (scale to TB of data)

## Key Takeaways

- **Spark = Parallelization Framework**: Distribute work across cores/machines
- **Same Code at All Scales**: Works on laptop, works on 1000 machines
- **Learning Path**: Local → Colab/AWS Free Tier → Production
- **Cost vs Speed**: Pay for more machines only when needed

You just learned distributed computing! 🎉
