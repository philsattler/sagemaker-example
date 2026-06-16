"""
Load Spark-generated embeddings back into your RAG system.

This shows how to use the Parquet embeddings from Spark
in your existing RAG system.

NOTE: We use pandas instead of Spark to load - simpler and no Java needed!
"""

import pandas as pd
import numpy as np
import json

print("\n" + "="*80)
print("📚 Loading Spark Embeddings into RAG System")
print("="*80)

# ============================================================================
# Load embeddings from Parquet (using pandas, not Spark)
# ============================================================================

print("\n📖 Loading embeddings from Parquet...")
# Parquet files work with pandas - no need for Spark!
embeddings_df = pd.read_parquet("data/spark_word_counts")

print(f"✅ Loaded {len(embeddings_df)} rows")

# ============================================================================
# Convert to format compatible with RAG system
# ============================================================================

print("\n🔄 Converting to working format...")

# With pandas, it's simpler!
references = embeddings_df['reference'].tolist()
word_counts = embeddings_df['word_count'].tolist()

# Create a simple dictionary
word_count_dict = dict(zip(references, word_counts))

print(f"✅ Converted to dictionary")
print(f"   Total verses: {len(word_count_dict)}")

# ============================================================================
# Example: Analyze the data
# ============================================================================

print("\n🔍 Analyzing Spark output...")

# Find verses with most words
sorted_verses = sorted(word_count_dict.items(), key=lambda x: x[1], reverse=True)

print(f"\nTop 5 longest verses (by word count):\n")
for rank, (ref, word_count) in enumerate(sorted_verses[:5], 1):
    print(f"{rank}. {ref:20s} - {word_count} words")

# Statistics
word_counts_list = list(word_count_dict.values())
print(f"\nWord count statistics:")
print(f"   - Average: {np.mean(word_counts_list):.1f} words/verse")
print(f"   - Min: {np.min(word_counts_list)} words")
print(f"   - Max: {np.max(word_counts_list)} words")
print(f"   - Median: {np.median(word_counts_list):.1f} words")

# ============================================================================
# Save as JSON for easy reference
# ============================================================================

print(f"\n💾 Saving results as JSON...")

with open("data/spark_word_counts_results.json", "w") as f:
    json.dump(word_count_dict, f, indent=2)

print(f"✅ Saved: data/spark_word_counts_results.json")

# ============================================================================
# Key Learning: What We Did
# ============================================================================

print(f"""
🎓 KEY LEARNING POINTS:

1. PARQUET FILES:
   - Spark writes data as Parquet (distributed format)
   - Pandas can read Parquet files directly
   - No need for Spark just to load results!

2. DISTRIBUTED → CENTRALIZED:
   - Spark distributed the work across 12 cores
   - We collected results back into a single dictionary
   - In real life, you'd keep big data distributed

3. NO JAVA REQUIRED:
   - Using pandas instead of Spark means no Java dependency
   - But Spark is still useful for the computation step

4. WORKFLOW:
   - spark-submit: Process data (parallel)
   - pandas: Load results (simple)
   - RAG system: Use results (your existing code)

Next time, just load with:
   df = pd.read_parquet("data/spark_word_counts")
""")

print("="*80 + "\n")
