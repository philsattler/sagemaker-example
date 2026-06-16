"""
Analyze Spark job results - NO Spark needed, just Python!

This shows that:
1. Spark did the HARD work (distributed across 12 cores)
2. You just read simple CSV for results
3. No Java, no Spark, no complexity needed after computation
"""

import csv
import statistics

print("\n" + "="*80)
print("📊 Analyzing Spark Job Results")
print("="*80)

# Read CSV (simple Python, no Spark!)
import glob

word_counts = {}
csv_files = glob.glob('data/spark_word_counts_csv/part-*.csv')

if not csv_files:
    print("❌ CSV file not found! Make sure to run: spark-submit convert_parquet_to_csv.py")
    exit(1)

with open(csv_files[0], 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        reference = row['reference']
        word_count = int(row['word_count'])
        word_counts[reference] = word_count

print(f"\n✅ Loaded {len(word_counts)} verses from Spark output\n")

# Find longest verses
longest = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
print("🔝 Top 10 longest verses (by word count):")
for rank, (ref, count) in enumerate(longest, 1):
    print(f"   {rank:2d}. {ref:25s} - {count:3d} words")

# Statistics
counts = list(word_counts.values())
print(f"\n📈 Statistics:")
print(f"   - Total verses: {len(counts)}")
print(f"   - Average words/verse: {statistics.mean(counts):.1f}")
print(f"   - Shortest verse: {min(counts)} words")
print(f"   - Longest verse: {max(counts)} words")
print(f"   - Median: {statistics.median(counts):.1f} words")
print(f"   - Std deviation: {statistics.stdev(counts):.1f}")

# Histogram
print(f"\n📊 Word count distribution:")
ranges = [
    ("1-10 words", 1, 10),
    ("11-20 words", 11, 20),
    ("21-30 words", 21, 30),
    ("31-40 words", 31, 40),
    ("40+ words", 41, float('inf'))
]

for label, min_w, max_w in ranges:
    count = sum(1 for c in counts if min_w <= c <= max_w)
    percentage = (count / len(counts)) * 100
    bar = "█" * int(percentage / 2)
    print(f"   {label:15s}: {count:5d} verses ({percentage:5.1f}%) {bar}")

print("\n" + "="*80)
print("🎓 KEY LEARNING:")
print("""
1. SPARK DID THE WORK:
   - Distributed the 24K verses across 12 cores
   - Each core counted words in parallel
   - Results saved to Parquet format

2. YOU JUST READ THE RESULTS:
   - Simple Python CSV reading (no dependencies!)
   - No Spark needed for analysis
   - No Java, no complexity

3. THIS SCALES:
   - Same workflow scales to terabytes
   - Spark handles the parallel part
   - You handle the analysis part

This is how real production systems work:
- Heavy processing with Spark/Hadoop
- Result analysis with simple tools
""")
print("="*80 + "\n")
