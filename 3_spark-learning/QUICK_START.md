# ⚡ Quick Start: Learn by Doing

This guide lets YOU run the exercises at your own pace.

---

## The Three Commands You Need to Know

```bash
# Command 1: Run the Spark job (the heavy lifting)
spark-submit spark_embedding_simple.py

# Command 2: Convert results to CSV (format conversion)
spark-submit convert_parquet_to_csv.py

# Command 3: Analyze results with Python (simple stats)
python3 analyze_results.py
```

That's it! These three commands power the entire workflow.

---

## Exercise 1: Run It Yourself (5 minutes)

**Goal**: Run the full workflow and see what happens

**Steps**:
1. Open Terminal in this directory
2. Run: `spark-submit spark_embedding_simple.py`
3. Wait for it to finish
4. Run: `spark-submit convert_parquet_to_csv.py`
5. Run: `python3 analyze_results.py`

**What to watch for**:
- How long does Spark job take?
- How many partitions does it create? (should be 12)
- What's the longest verse?
- What's the average verse length?

---

## Exercise 2: Explore the Code (10 minutes)

**Goal**: Read and understand `spark_embedding_simple.py`

**Read these sections**:
- Lines 1-31: Setup and data loading
  - Question: What does `master("local[*]")` mean?
- Lines 42-49: Create DataFrame
  - Question: What's a "partition"?
- Lines 56-61: Processing function
  - Question: What does `count_words_in_verse()` return?
- Line 73: The map operation
  - Question: Why is this the "magic" line?

**Action**: Add a comment next to line 73 explaining what `.map()` does

---

## Exercise 3: Modify the Function (15 minutes)

**Goal**: Add a new metric to track

**Current code (lines 56-61)**:
```python
def count_words_in_verse(text):
    return len(text.split())
```

**Your task**:
1. Open `spark_embedding_simple.py`
2. Change it to also count characters:

```python
def count_words_in_verse(text):
    words = len(text.split())
    chars = len(text)
    return (words, chars)  # Return both!
```

3. Update `process_verse()` to return both:
```python
def process_verse(row):
    reference = row[0]
    text = row[1]
    words, chars = count_words_in_verse(text)  # Unpack!
    return (reference, words, chars)  # Return both!
```

4. Update the schema (lines 77-81):
```python
output_schema = StructType([
    StructField("reference", StringType(), True),
    StructField("word_count", StringType(), True),
    StructField("char_count", StringType(), True)  # ADD THIS
])
```

5. Run: `spark-submit spark_embedding_simple.py`
6. Run: `spark-submit convert_parquet_to_csv.py`
7. Check: `head data/spark_word_counts_csv/part-*.csv`

**Verify**: Do you see three columns now? (reference, word_count, char_count)

---

## Exercise 4: Filter the Data (10 minutes)

**Goal**: Process only certain verses

**Add AFTER line 49** (after `df = spark.createDataFrame(...)`):

```python
# Only keep verses that mention "love"
df = df.filter(df[1].contains("love"))
```

**Then run the full workflow**:
```bash
spark-submit spark_embedding_simple.py
spark-submit convert_parquet_to_csv.py
python3 analyze_results.py
```

**Questions to answer**:
1. How many verses mention "love"?
2. What's the average word count for those verses?
3. Is it different from the overall average (31.7)?

---

## Exercise 5: Group by Book (Challenge!)

**Goal**: Find statistics per book

**This requires modifying both Spark and Python code**

**In `spark_embedding_simple.py`**:
1. Modify `process_verse()` to extract book name:
```python
def process_verse(row):
    reference = row[0]
    text = row[1]
    # Extract book name (first word of reference)
    book = reference.split()[0]
    word_count = count_words_in_verse(text)
    return (book, word_count)
```

2. Update schema to reflect this

3. Run the Spark job

**In `analyze_results.py`**:
1. After loading data, group by book:
```python
from collections import defaultdict

verses_by_book = defaultdict(list)
for book, word_count in word_counts.items():
    verses_by_book[book].append(word_count)
```

2. Calculate per-book statistics:
```python
for book in sorted(verses_by_book.keys()):
    counts = verses_by_book[book]
    avg = statistics.mean(counts)
    print(f"{book}: {len(counts)} verses, avg {avg:.1f} words")
```

**Questions to answer**:
1. Which book has the longest verses on average?
2. Which book has the shortest?
3. How does it compare to the overall average?

---

## Checklist: As You Learn

**After Exercise 1**:
- [ ] Can I run the full workflow?
- [ ] Do I understand the 3-command flow?

**After Exercise 2**:
- [ ] Can I read Spark code?
- [ ] Do I know what `master("local[*]")` does?
- [ ] Can I find the `.map()` line?

**After Exercise 3**:
- [ ] Did my modified code run?
- [ ] Are there now 3 columns in the output?
- [ ] Do I understand tuples?

**After Exercise 4**:
- [ ] Did the filter work?
- [ ] Did the verse count decrease?
- [ ] Do I understand `.contains()` filter?

**After Exercise 5**:
- [ ] Did grouping work?
- [ ] Can I find the book with longest verses?
- [ ] Do I understand defaultdict?

---

## When You Get Stuck

**Error: "pyspark not found"**
→ Run with `spark-submit`, not `python3`

**Error: "reference field not found"**
→ Check if you updated the schema

**Output looks wrong**
→ Check: `head data/spark_word_counts_csv/part-*.csv`

**Results didn't change after modification**
→ Did you re-run BOTH spark-submit commands?

---

## Key Insights (Read These)

### Why Spark?
- Your laptop: 0.3 seconds (12 cores)
- 100 AWS cores: 0.03 seconds (10x faster)
- Same code!

### Why This Matters
- Scaling doesn't require rewriting code
- Distribution is automatic
- You get parallelism "for free"

### The Pattern
```
Load → Partition → Map → Reduce → Save
 ↓        ↓        ↓       ↓       ↓
JSON    Spark     fn   Combine  Parquet
        splits   runs  results
       it up!    in
              parallel
```

---

## Next Steps

Once you complete all exercises:
1. Try modifying the function further
2. Try different filters
3. Combine multiple operations
4. Run with different core counts
5. Read about AWS EMR

---

**Remember**: You're learning the same concepts used in petabyte-scale data processing at companies like Netflix, Uber, and Google!

