from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("ConvertCSV").master("local[*]").getOrCreate()

# Read Parquet
df = spark.read.parquet("data/spark_word_counts")

print(f"✅ Loaded Spark results")
print(f"   Total rows: {df.count()}\n")

# Show first 10
print("First 10 results:")
df.show(10)

# Save to CSV
df.coalesce(1).write.mode("overwrite").csv("data/spark_word_counts_csv", header=True)
print(f"\n✅ Converted to CSV: data/spark_word_counts_csv")

spark.stop()
