"""
Dask Job: Parallelize Bible Verse Embeddings (No Java Required!)

Dask is similar to Spark but:
- Pure Python (no Java needed)
- Easier to understand
- Same parallelization concepts
- Scales same way

RUN: python dask_embedding_job.py
"""

import json
import time
import numpy as np
from dask import delayed, compute
from sentence_transformers import SentenceTransformer
import dask.dataframe as dd
import pandas as pd

print("\n" + "="*80)
print("🚀 DASK BIBLE EMBEDDING JOB (No Java Required!)")
print("="*80)

# ============================================================================
# PART 1: LOAD CORPUS
# ============================================================================

print(f"\n📖 Loading KJV corpus...")
start_time = time.time()

with open('data/kjv_corpus_full.json', 'r') as f:
    corpus_data = json.load(f)

verses = corpus_data['verses_detailed']
print(f"✅ Loaded {len(verses)} verses in {time.time() - start_time:.2f}s")

# ============================================================================
# PART 2: CREATE PANDAS DATAFRAME (then convert to Dask)
# ============================================================================

print(f"\n🔄 Creating DataFrame...")
df_pandas = pd.DataFrame([
    {'reference': v['reference'], 'text': v['text']}
    for v in verses
])

print(f"✅ Created Pandas DataFrame: {len(df_pandas)} rows")

# ============================================================================
# PART 3: EMBEDDING FUNCTION
# ============================================================================

def create_embedding(text):
    """Create 384-dim embedding for a verse"""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()

# ============================================================================
# PART 4: PARALLELIZE WITH DASK DELAYED
# ============================================================================

print(f"\n⚙️  Setting up parallel computation with Dask...")

# Create delayed tasks (don't compute yet - Dask is lazy!)
delayed_embeddings = [
    delayed(create_embedding)(text)
    for text in df_pandas['text']
]

print(f"✅ Created {len(delayed_embeddings)} delayed tasks")
print(f"   (These will run in parallel when we ask for results)")

# ============================================================================
# PART 5: COMPUTE IN PARALLEL
# ============================================================================

print(f"\n🔄 Computing embeddings in parallel...")
print(f"   (Dask will use all available CPU cores)")

start_time = time.time()

# This is where the magic happens!
# compute() runs all delayed tasks in parallel
embeddings_list = compute(*delayed_embeddings)

elapsed = time.time() - start_time

print(f"✅ Computed {len(embeddings_list)} embeddings in {elapsed:.2f}s")
print(f"   - Speed: {len(embeddings_list)/elapsed:.1f} verses/second")

# ============================================================================
# PART 6: COMBINE RESULTS
# ============================================================================

print(f"\n📊 Building results...")

# Create final dataframe with embeddings
results = pd.DataFrame({
    'reference': df_pandas['reference'],
    'embedding': embeddings_list
})

print(f"✅ Created results DataFrame")

# Save to CSV (Parquet is also possible)
results.to_csv("data/dask_embeddings.csv", index=False)
print(f"💾 Saved to data/dask_embeddings.csv")

# ============================================================================
# PART 7: VERIFICATION
# ============================================================================

print(f"\n🔍 Sample results:")
print(f"{results.head()}")

sample_embedding = embeddings_list[0]
print(f"\n📖 Sample embedding for {results.iloc[0]['reference']}:")
print(f"   Type: {type(sample_embedding)}")
print(f"   Length: {len(sample_embedding)}")
print(f"   First 5 values: {sample_embedding[:5]}")

# ============================================================================
# PART 8: COMPARISON
# ============================================================================

print(f"\n⏱️  Performance Notes:")
print(f"   - Dask ran in parallel on your CPU cores")
print(f"   - Time: {elapsed:.1f}s")
print(f"   - Same code works on:")
print(f"     • Single machine (now)")
print(f"     • Distributed cluster (just change backend)")
print(f"     • Kubernetes, AWS, etc.")

# ============================================================================
# PART 9: LOAD AND USE
# ============================================================================

print(f"\n🔄 Converting to numpy format for RAG...")

# Convert embeddings back to numpy array
embeddings_array = np.array([np.array(e) for e in embeddings_list])
references = results['reference'].tolist()

print(f"✅ Converted to numpy")
print(f"   Shape: {embeddings_array.shape}")

# Save for fast loading
np.save("data/dask_embeddings_array.npy", embeddings_array)
import json as json_lib
with open("data/dask_embeddings_references.json", "w") as f:
    json_lib.dump(references, f)

print(f"💾 Saved numpy format for fast loading:")
print(f"   - data/dask_embeddings_array.npy")
print(f"   - data/dask_embeddings_references.json")

# ============================================================================
# PART 10: TEST WITH RAG
# ============================================================================

print(f"\n🧪 Testing with RAG query...")

query = "faith and trust"
query_emb = create_embedding(query)
query_emb_norm = np.array(query_emb) / np.linalg.norm(query_emb)

embeddings_norm = embeddings_array / np.linalg.norm(embeddings_array, axis=1, keepdims=True)
similarities = embeddings_norm @ query_emb_norm

top_k_indices = np.argsort(similarities)[-5:][::-1]

print(f"\nQuery: '{query}'")
print(f"Top 5 results:\n")
for rank, idx in enumerate(top_k_indices, 1):
    ref = references[idx]
    score = similarities[idx]
    print(f"{rank}. {ref:20s} (score: {score:.3f})")

print("\n" + "="*80)
print("✅ DASK JOB COMPLETE!")
print("="*80 + "\n")
