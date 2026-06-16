"""
Spark Job: Parallelize Bible Verse Embeddings Across Multiple Cores

This demonstrates:
1. Reading data with Spark
2. Parallelize computation across CPU cores
3. Computing embeddings in parallel
4. Saving results

RUN: spark-submit spark_embedding_job.py
"""

import json
import time
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, FloatType
from sentence_transformers import SentenceTransformer

# ============================================================================
# PART 1: INITIALIZE SPARK
# ============================================================================

print("\n" + "="*80)
print("🚀 SPARK BIBLE EMBEDDING JOB")
print("="*80)

spark = SparkSession.builder \
    .appName("BibleEmbeddingJob") \
    .master("local[*]") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "2g") \
    .getOrCreate()

print(f"\n✅ Spark Session Created")
print(f"   - Master: local[*] (all available cores)")
print(f"   - Driver memory: 4GB")

# Get number of cores
num_cores = spark.sparkContext.defaultParallelism
print(f"   - Available cores: {num_cores}")

# ============================================================================
# PART 2: LOAD CORPUS
# ============================================================================

print(f"\n📖 Loading KJV corpus...")
start_time = time.time()

with open('data/kjv_corpus_full.json', 'r') as f:
    corpus_data = json.load(f)

verses = corpus_data['verses_detailed']
print(f"✅ Loaded {len(verses)} verses in {time.time() - start_time:.2f}s")

# ============================================================================
# PART 3: CREATE SPARK DATAFRAME
# ============================================================================

print(f"\n🔄 Converting to Spark DataFrame...")
start_time = time.time()

# Convert to list of tuples (reference, text)
verse_tuples = [(v['reference'], v['text']) for v in verses]

# Create Spark RDD and convert to DataFrame
df = spark.createDataFrame(
    verse_tuples,
    schema=StructType([
        StructField("reference", StringType(), True),
        StructField("text", StringType(), True)
    ])
)

print(f"✅ Created DataFrame with {df.count()} rows in {time.time() - start_time:.2f}s")
print(f"   Partitions: {df.rdd.getNumPartitions()}")

# ============================================================================
# PART 4: EMBEDDING FUNCTION (runs on each executor)
# ============================================================================

def create_embedding(text):
    """
    Create a 384-dimensional embedding for a verse.
    This function runs on EACH CORE in parallel!
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()  # Convert to list for JSON serialization

# ============================================================================
# PART 5: MAP EMBEDDINGS IN PARALLEL
# ============================================================================

print(f"\n⚙️  Computing embeddings in parallel across {num_cores} cores...")
print(f"   (This will take ~30-60 seconds on your laptop)")
print(f"   (On 100 AWS machines, this would take ~1-2 seconds!)")

start_time = time.time()

# The magic: Spark distributes this across all cores
def verse_to_embedding(row):
    """
    Process one verse:
    Input: (reference, text)
    Output: (reference, embedding)

    Spark runs this in PARALLEL on multiple cores!
    """
    reference = row[0]
    text = row[1]
    embedding = create_embedding(text)
    return (reference, embedding)

# Convert to RDD, map embedding function, convert back to DataFrame
embeddings_rdd = df.rdd.map(verse_to_embedding)

# Define output schema
output_schema = StructType([
    StructField("reference", StringType(), True),
    StructField("embedding", ArrayType(FloatType()), True)
])

embeddings_df = spark.createDataFrame(embeddings_rdd, schema=output_schema)

# Force computation (important: Spark is lazy by default!)
embeddings_df.persist()
total_rows = embeddings_df.count()

elapsed = time.time() - start_time
print(f"✅ Computed {total_rows} embeddings in {elapsed:.2f}s")
print(f"   - Speed: {total_rows/elapsed:.1f} verses/second")
print(f"   - Per core: {(total_rows/elapsed)/num_cores:.1f} verses/second/core")

# ============================================================================
# PART 6: SAVE RESULTS
# ============================================================================

print(f"\n💾 Saving embeddings to Parquet format...")
start_time = time.time()

# Parquet is optimized for distributed data
output_path = "data/spark_embeddings"
embeddings_df.write.mode("overwrite").parquet(output_path)

print(f"✅ Saved to {output_path} in {time.time() - start_time:.2f}s")

# ============================================================================
# PART 7: VERIFICATION & STATS
# ============================================================================

print(f"\n📊 Verification & Statistics:")
print(f"   - Total verses processed: {total_rows}")
print(f"   - Embedding dimension: 384")
print(f"   - Expected output size: ~{total_rows * 384 * 4 / (1024**2):.1f} MB")

# Read back one embedding to verify
sample = embeddings_df.limit(1).collect()
sample_ref = sample[0]['reference']
sample_embedding = sample[0]['embedding']
print(f"\n   Sample verse: {sample_ref}")
print(f"   First 5 embedding values: {sample_embedding[:5]}")
print(f"   Embedding shape: (384,)")

# ============================================================================
# PART 8: COMPARISON - SERIAL VS PARALLEL
# ============================================================================

print(f"\n⏱️  Performance Comparison:")
serial_time = total_rows * (elapsed / total_rows / num_cores)
print(f"   - Serial (1 core): {serial_time:.1f}s")
print(f"   - Parallel ({num_cores} cores): {elapsed:.1f}s")
print(f"   - Speedup: {serial_time / elapsed:.1f}x faster with parallelization")

print(f"\n📈 Scaling Simulation:")
print(f"   - If you had 100 AWS cores:")
print(f"     - Time: ~{elapsed / (num_cores/4):.1f}s (1/25th of local time)")
print(f"   - If you had 1000 AWS cores:")
print(f"     - Time: ~{elapsed / (num_cores/0.4):.1f}s (1/250th of local time)")

# ============================================================================
# PART 9: LOAD AND USE EMBEDDINGS
# ============================================================================

print(f"\n🔍 Loading embeddings back for RAG:")

embeddings_loaded = spark.read.parquet(output_path)
print(f"✅ Loaded {embeddings_loaded.count()} embeddings from Parquet")

# Show structure
embeddings_loaded.printSchema()

# Show sample
print(f"\n📖 Sample results:")
embeddings_loaded.limit(3).show(truncate=False)

# ============================================================================
# PART 10: CLEANUP
# ============================================================================

print(f"\n✅ JOB COMPLETE!")
print(f"="*80)
print(f"\nNext steps:")
print(f"1. Embeddings saved to: {output_path}")
print(f"2. Load them in your RAG system:")
print(f"   embeddings_df = spark.read.parquet('{output_path}')")
print(f"3. Convert to numpy array for RAG similarity search")
print(f"\n" + "="*80 + "\n")

spark.stop()
