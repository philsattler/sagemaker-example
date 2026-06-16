# 🗺️ Spark Learning Map: Complete Architecture Guide

## Overview: What We Built

```
Your KJV Bible (23,673 verses)
         ↓
   SPARK JOB (Distributed Processing)
   ├─ 12 cores working in parallel
   ├─ Each processes ~2000 verses
   └─ Results combined automatically
         ↓
   Output: Parquet (distributed data format)
         ↓
   CSV Conversion (for readability)
         ↓
   Python Analysis (simple statistics)
```

---

## 📁 File Structure & Purpose

### Core Files You Need to Understand

```
/spark_embedding_simple.py      ← The SPARK JOB (does heavy lifting)
    ├─ Processes data in parallel
    ├─ Runs on your 12 cores
    └─ Output: data/spark_word_counts/

/convert_parquet_to_csv.py      ← Bridge script (converts format)
    ├─ Reads Parquet output from Spark
    ├─ Converts to readable CSV
    └─ Output: data/spark_word_counts_csv/

/analyze_results.py             ← Analysis script (simple Python)
    ├─ Reads the CSV file
    ├─ Does statistics
    └─ No Spark needed!

/data/spark_word_counts/        ← Spark output (Parquet format)
    └─ 12 files (one per core)

/data/spark_word_counts_csv/    ← Converted format (CSV)
    └─ Human-readable format
```

---

## 🔄 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: Load Data (spark_embedding_simple.py)          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Line 30-35: Load kjv_corpus_full.json                 │
│  ├─ Reads 23,673 verses from disk                      │
│  └─ Converts to list of tuples: (reference, text)      │
│                                                          │
│  Line 37-44: Create Spark DataFrame                    │
│  ├─ DataFrame = distributed table                      │
│  ├─ Spark splits into 12 partitions                    │
│  │  (one for each CPU core)                            │
│  └─ Each partition: ~2000 verses                       │
│                                                          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 2: Process in Parallel (spark_embedding_simple.py)│
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Line 54-61: Define processing function                │
│  ├─ count_words_in_verse(text)                         │
│  └─ Returns: integer word count                        │
│                                                          │
│  Line 63-66: Define map function                       │
│  ├─ process_verse(row)                                 │
│  ├─ Takes: (reference, text)                           │
│  └─ Returns: (reference, word_count)                   │
│                                                          │
│  Line 73: THE MAGIC - df.rdd.map(process_verse)       │
│  ├─ Spark applies process_verse to EVERY verse        │
│  ├─ Each core processes its partition in parallel      │
│  └─ Results combined automatically                     │
│                                                          │
│  PARALLEL EXECUTION:                                   │
│  ┌─────────┬─────────┬─────────┬─────────┐            │
│  │ Core 1  │ Core 2  │ Core 3  │ Core 4  │ ...        │
│  │ 2000    │ 2000    │ 2000    │ 2000    │            │
│  │ verses  │ verses  │ verses  │ verses  │            │
│  │   ↓     │   ↓     │   ↓     │   ↓     │            │
│  │ count   │ count   │ count   │ count   │            │
│  │ words   │ words   │ words   │ words   │            │
│  └─────────┴─────────┴─────────┴─────────┘            │
│         All at SAME TIME (parallel!)                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 3: Save Results (spark_embedding_simple.py)       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Line 89-92: Save to Parquet format                    │
│  ├─ results_df.write.parquet(output_path)             │
│  ├─ Creates: data/spark_word_counts/                  │
│  └─ Contains 12 Parquet files (one per core)          │
│                                                          │
│  Why Parquet? (not CSV)                                │
│  ├─ Distributed-friendly format                       │
│  ├─ Compressed (12 KB per file)                       │
│  ├─ Preserves data types                              │
│  └─ Easy for other Spark jobs to read                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 4: Convert to CSV (convert_parquet_to_csv.py)    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Line 8-9: Read Parquet                               │
│  ├─ spark.read.parquet("data/spark_word_counts")      │
│  └─ Combines all 12 files into one DataFrame          │
│                                                          │
│  Line 14-15: Write as CSV                             │
│  ├─ df.write.csv("data/spark_word_counts_csv")       │
│  └─ Creates readable format                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 5: Analyze Results (analyze_results.py)          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Line 19-21: Read CSV (pure Python)                   │
│  ├─ csv.DictReader()                                  │
│  ├─ No Spark needed!                                  │
│  └─ Creates: word_counts = {"Genesis 1:1": 10, ...}  │
│                                                          │
│  Line 24-27: Find longest verses                      │
│  ├─ sorted(word_counts.items(), reverse=True)        │
│  └─ Shows top 10                                      │
│                                                          │
│  Line 30-32: Calculate statistics                     │
│  ├─ statistics.mean(counts)                          │
│  ├─ statistics.median(counts)                        │
│  └─ statistics.stdev(counts)                         │
│                                                          │
│  Line 35-40: Distribution histogram                   │
│  ├─ Bins: 1-10, 11-20, 21-30, etc.                   │
│  └─ Shows how many verses in each bin                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Understanding Each File: Line-by-Line

### `spark_embedding_simple.py` (THE SPARK JOB)

| Lines | What | Why | Key Concept |
|-------|------|-----|------------|
| 1-20 | Import libraries + setup | Tell Python what tools to use | Dependencies |
| 24-31 | Create Spark Session | Start Spark on your laptop | `master("local[*]")` = all cores |
| 42-49 | Load Bible corpus | Read JSON file with 23K verses | Data loading |
| 52-65 | Create DataFrame | Convert to Spark's distributed format | **Partitioning** |
| 56-61 | Define function | `count_words_in_verse()` | Pure function |
| 63-66 | Define map function | `process_verse()` takes row → returns result | Map operation |
| 73 | **THE MAGIC** | `df.rdd.map(process_verse)` | **Parallelization happens here** |
| 75-79 | Define schema | Tell Spark what output looks like | Data structure |
| 82-92 | Force computation | `.count()` triggers actual work | Lazy evaluation |
| 96-101 | Save to Parquet | Write distributed results to disk | Output format |

**Key Questions to Ask:**
- Why do we call it "lazy evaluation"?
- What does `.map()` actually do?
- Why Parquet and not CSV?

---

### `convert_parquet_to_csv.py` (CONVERTER SCRIPT)

| Lines | What | Why |
|-------|------|-----|
| 1-2 | Import Spark | Need to read Parquet |
| 5-6 | Create Spark Session | Initialize Spark |
| 9 | Read Parquet | Load Spark output |
| 12 | Show first 10 | Verify data looks right |
| 15 | Write CSV | Convert to human-readable format |
| 17 | Stop Spark | Clean up resources |

**Key Question:**
- Why can't we just read Parquet files with Python directly?
  (Answer: We CAN, but pandas needs `pyarrow` library)

---

### `analyze_results.py` (ANALYSIS SCRIPT)

| Lines | What | Why | Tool |
|-------|------|-----|------|
| 1-10 | Import libraries | csv, glob, statistics | Pure Python |
| 20-25 | Read CSV | Load results | `csv.DictReader()` |
| 28-30 | Create dictionary | word_counts = {ref: count} | Python dict |
| 33-38 | Find longest | `sorted()` by word count | Standard Python |
| 41-46 | Statistics | mean, median, stdev | `statistics` module |
| 49-56 | Histogram | Distribution across bins | List comprehension |

**Key Difference:**
- This file uses **NO Spark** - just pure Python!
- This is the "light lifting" part of the workflow

---

## 🧠 Learning Objectives (What You Should Understand)

### After Reading `spark_embedding_simple.py`:
- [ ] What is a "DataFrame"?
- [ ] What does `.master("local[*]")` mean?
- [ ] Why is partitioning important?
- [ ] What is "lazy evaluation"?
- [ ] How does `.map()` parallelize work?
- [ ] Why `.count()` at line 82 triggers computation?

### After Reading `convert_parquet_to_csv.py`:
- [ ] What format is Parquet?
- [ ] Why does Spark write to Parquet instead of CSV?
- [ ] Can you read Parquet without Spark?

### After Reading `analyze_results.py`:
- [ ] How is this different from Spark code?
- [ ] Why don't we need Spark here?
- [ ] What's a `DictReader`?

---

## 🔧 Hands-On Exercises (Do These Yourself)

### Exercise 1: Understand Partitioning

**Goal**: See how Spark splits work

**Steps**:
1. Open `spark_embedding_simple.py`
2. Find line 53 that says `Partitions: {df.rdd.getNumPartitions()}`
3. Change `.master("local[*]")` on line 14 to `.master("local[2]")`
4. Run: `spark-submit spark_embedding_simple.py`
5. Compare the output

**Question to Answer**:
- How did the number of partitions change?
- Did it run faster or slower? Why?

---

### Exercise 2: Modify the Processing Function

**Goal**: Add a new metric

**Current function (line 56-61)**:
```python
def count_words_in_verse(text):
    return len(text.split())
```

**Your Task**: Add character count
```python
def count_words_and_chars(text):
    words = len(text.split())
    chars = len(text)
    return (words, chars)  # Return TUPLE
```

**Then you need to**:
1. Update `process_verse()` to return 3 fields instead of 2
2. Update the schema (lines 77-81) to include a third field
3. Run and check results

**Questions to Answer**:
- Which verse has the most characters?
- What's the average characters per verse?

---

### Exercise 3: Filter Before Processing

**Goal**: Process only certain verses

**Add AFTER line 49** (after creating DataFrame):
```python
# Only process verses containing the word "faith"
df = df.filter(df[1].contains("faith"))
```

**Then run it**

**Questions to Answer**:
- How many verses contain "faith"?
- Is it faster or slower than processing all verses? Why?
- What's the average word count in faith-related verses?

---

### Exercise 4: Group by Book (Hard)

**Goal**: Calculate statistics per book

**Modify the process_verse function** to return book name instead of just word count

**Then modify** the analysis script to group results by book

**Questions to Answer**:
- Which book has the longest average verse?
- Which book has the shortest?
- Which book has the most verses?

---

## 📊 How to Verify Your Changes

After modifying code, check:

1. **Does it run without errors?**
   ```bash
   spark-submit spark_embedding_simple.py
   ```

2. **Check the output format**:
   ```bash
   head data/spark_word_counts_csv/part-*.csv
   ```

3. **Run the analysis**:
   ```bash
   python3 analyze_results.py
   ```

4. **Compare results**:
   - Did the numbers change?
   - Does it make sense?

---

## 🎓 Key Concepts Explained

### Lazy Evaluation
```
Code you write:
  df.rdd.map(process_verse)  ← Just a PLAN
  
No work happens yet!

When you call .count():
  .count()  ← NOW Spark executes the plan
  
This is called "lazy evaluation"
```

### Partitioning
```
23,673 verses + 12 cores = ?

Spark splits automatically:
  Core 1: verses 0-1973
  Core 2: verses 1974-3947
  Core 3: verses 3948-5921
  ... (and so on)

Each core processes independently
Then results combine automatically
```

### MapReduce Pattern
```
MAP phase:      process_verse applied to EVERY verse in parallel
REDUCE phase:   combine all results (implicit in Spark)

This is the fundamental pattern of distributed computing!
```

---

## 🚀 Next Level: Scaling to Cloud

If you understand the above, here's how it scales:

**Local (your laptop)**:
```
spark-submit spark_embedding_simple.py
├─ 12 cores
├─ 0.3 seconds
└─ Cost: $0
```

**AWS EMR (100 cores)**:
```
spark-submit --master spark://ec2-cluster:7077 spark_embedding_simple.py
├─ 100 cores
├─ ~0.05 seconds (6x faster)
└─ Cost: $2
```

**Same code! Different master!**

---

## ✅ Checklist: Did You Really Learn?

- [ ] I can explain what `.master("local[*]")` does
- [ ] I understand why Spark uses partitions
- [ ] I know what "lazy evaluation" means
- [ ] I can modify the processing function
- [ ] I can add a filter before processing
- [ ] I can read and understand CSV output
- [ ] I can run analysis on results
- [ ] I understand why this scales to terabytes

If you checked all boxes, you understand distributed computing! 🎉

