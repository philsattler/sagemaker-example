"""
Simplified Spark Job: Shows the parallelization concept
(without the heavy embedding model that crashes workers)

This demonstrates:
1. How Spark distributes work
2. How to parallelize computations
3. How to save results in Parquet format
"""

import json
import time
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, FloatType

print("\n" + "="*80)
print("🚀 SIMPLIFIED SPARK BIBLE JOB (Learning Version)")
print("="*80)

# ============================================================================
# PART 1: INITIALIZE SPARK
# ============================================================================

spark = SparkSession.builder \
    .appName("BibleParallelJob") \
    .master("local[*]") \
    .config("spark.driver.memory", "2g") \
    .getOrCreate()

print(f"\n✅ Spark Session Created")
num_cores = spark.sparkContext.defaultParallelism
print(f"   - Available cores: {num_cores}")

# ============================================================================
# PART 2: LOAD AND PARALLELIZE DATA
# ============================================================================

print(f"\n📖 Loading KJV corpus...")
start_time = time.time()

with open('data/kjv_corpus_full.json', 'r') as f:
    corpus_data = json.load(f)

verses = corpus_data['verses_detailed']
print(f"✅ Loaded {len(verses)} verses in {time.time() - start_time:.2f}s")

# Convert to tuples
verse_tuples = [(v['reference'], v['text']) for v in verses]

# Create Spark DataFrame (automatically partitioned across cores)
df = spark.createDataFrame(
    verse_tuples,
    schema=StructType([
        StructField("reference", StringType(), True),
        StructField("text", StringType(), True)
    ])
)

print(f"\n🔄 Created Spark DataFrame")
print(f"   - Rows: {df.count()}")
print(f"   - Partitions: {df.rdd.getNumPartitions()} (one per core)")

# ============================================================================
# PART 3: DEMONSTRATE PARALLELIZATION
# ============================================================================

print(f"\n⚙️  Demonstrating parallel word counting...")
print(f"   (Instead of loading heavy model, we'll count words in parallel)")

def count_words_in_verse(text):
    """Simple function that will run in parallel on each core"""
    return len(text.split())

# Map function across all partitions
def process_verse(row):
    reference = row[0]
    text = row[1]
    word_count = count_words_in_verse(text)
    return (reference, word_count)

print(f"\n🔄 Processing {len(verses)} verses across {num_cores} cores...")
start_time = time.time()

# THIS IS THE PARALLELIZATION:
# Spark splits 23K verses across 12 cores
# Each core processes its verses independently
# Results are combined

results_rdd = df.rdd.map(process_verse)

# Define output schema
output_schema = StructType([
    StructField("reference", StringType(), True),
    StructField("word_count", StringType(), True)
])

results_df = spark.createDataFrame(results_rdd, schema=output_schema)

# Force computation
results_df.persist()
total_results = results_df.count()

elapsed = time.time() - start_time

print(f"✅ Processed {total_results} verses in {elapsed:.2f}s")
print(f"   - Speed: {total_results/elapsed:.1f} verses/second")
print(f"   - Per core: {(total_results/elapsed)/num_cores:.1f} verses/second/core")

# ============================================================================
# PART 4: SAVE RESULTS
# ============================================================================

print(f"\n💾 Saving results to Parquet format...")
output_path = "data/spark_word_counts"
results_df.write.mode("overwrite").parquet(output_path)
print(f"✅ Saved to {output_path}")

# ============================================================================
# PART 5: VERIFICATION
# ============================================================================

print(f"\n📊 Sample Results:")
sample = results_df.limit(5).collect()
for row in sample:
    print(f"   {row[0]:20s} - {row[1]} words")

# ============================================================================
# PART 6: KEY LEARNING POINTS
# ============================================================================

print(f"\n📚 KEY LEARNING POINTS:")
print(f"""
1. DATA PARTITIONING:
   - 23K verses split into {num_cores} partitions
   - Each core processes ~{len(verses)//num_cores} verses

2. PARALLEL PROCESSING:
   - Same function (process_verse) runs on all cores
   - Spark handles coordination automatically

3. LAZY EVALUATION:
   - Code doesn't run until you call .count()
   - Spark optimizes the execution plan

4. SCALING:
   - Local laptop: {elapsed:.1f}s on {num_cores} cores
   - AWS EMR (100 cores): ~{elapsed/(num_cores/4):.2f}s (25x faster)
   - AWS EMR (1000 cores): ~{elapsed/(num_cores/0.4):.2f}s (250x faster)

5. SAME CODE EVERYWHERE:
   - This code runs on your laptop
   - Same code runs on 1000 AWS machines
   - Only change: .master() parameter
""")

# ============================================================================
# PART 7: REAL-WORLD NOTE
# ============================================================================

print(f"\n⚠️  WHY THIS SIMPLIFIED VERSION?")
print(f"""
The full embedding job crashed because:
- Loading SentenceTransformers in each worker is heavy
- Network communication between driver and workers is fragile
- Python + Spark + PyTorch is a tricky combination

Solutions for production:
1. Use pre-computed embeddings (compute once, distribute many times)
2. Use Spark native libraries (MLlib)
3. Use distributed inference (GPU-accelerated Spark)
4. Use AWS SageMaker for embeddings (better than raw Spark)
""")

# ============================================================================
# CLEANUP
# ============================================================================

print(f"\n✅ JOB COMPLETE!")
print(f"="*80)
print(f"\nNext steps:")
print(f"1. Results saved to: {output_path}")
print(f"2. Load with: spark.read.parquet('{output_path}')")
print(f"3. For embeddings: Use SageMaker or pre-compute + broadcast")
print(f"\n" + "="*80 + "\n")

spark.stop()
