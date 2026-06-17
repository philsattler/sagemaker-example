# Metrics Logging for Training

Your training pipeline now automatically logs system metrics (CPU, memory, GPU) throughout training. This helps you identify bottlenecks and optimize instance selection.

---

## What Gets Logged

### System Information (At Startup)
```
================================================================================
SYSTEM INFORMATION
================================================================================
CPU Cores: 4 physical, 8 logical
Memory: 16.0 GB total
GPU: 1 device(s) available
  GPU0: Tesla V100 (16.0GB)
================================================================================
```

### Per-Stage Metrics
Each stage logs metrics at start and completion:

```
Training model: xgbregressor
Hyperparameters: {...}

================================================================================
DATA LOADING STARTED
================================================================================
[METRICS] CPU:  15.2% | Memory:  2.3GB/ 16.0GB ( 14.3%)
[DATA LOADING] Loaded X=(10000, 50), y=(10000,)
[METRICS] CPU:  18.5% | Memory:  3.1GB/ 16.0GB ( 19.4%)
[DATA LOADING] Split: train=(8000, 50), val=(2000, 50)
[METRICS] CPU:  12.1% | Memory:  3.1GB/ 16.0GB ( 19.4%)
================================================================================
DATA LOADING COMPLETED in 0.3 minutes
================================================================================

================================================================================
TRAINING XGBREGRESSOR STARTED
================================================================================
[METRICS] CPU:  25.0% | Memory:  3.5GB/ 16.0GB ( 21.9%) | GPU0: 0.5GB/16.0GB (3.1%)
[TRAINING XGBREGRESSOR] Training completed
[METRICS] CPU:  92.5% | Memory:  8.2GB/ 16.0GB ( 51.3%) | GPU0: 12.3GB/16.0GB (76.9%)
================================================================================
TRAINING XGBREGRESSOR COMPLETED in 15.2 minutes
================================================================================

================================================================================
MODEL SAVING STARTED
================================================================================
[METRICS] CPU:   5.2% | Memory:  8.2GB/ 16.0GB ( 51.3%)
[MODEL SAVING] Model saved to /opt/ml/model/model.tar.gz
[METRICS] CPU:   3.1% | Memory:  7.9GB/ 16.0GB ( 49.4%)
================================================================================
MODEL SAVING COMPLETED in 0.2 minutes
================================================================================

================================================================================
TRAINING COMPLETE!
================================================================================
```

---

## How to Analyze the Output

### 1. Memory Exhaustion
```
[METRICS] CPU: 45% | Memory: 95% (15.2GB/16.0GB)
```
**Issue:** Memory is critically high  
**Action:** 
- Reduce batch size in model hyperparameters
- Use smaller instance type (ml.m5.large instead of ml.m5.xlarge)
- Check if data loading is keeping old data in memory

### 2. GPU Not Being Used
```
[METRICS] CPU: 92% | Memory: 45% | GPU0: 2.1GB/16.0GB (13.2%)
```
**Issue:** GPU utilization is low while CPU is maxed  
**Action:**
- Data loading/preprocessing is bottleneck
- Increase number of workers in data loader
- Ensure model is actually using GPU (check model code)

### 3. Perfect Utilization
```
[METRICS] CPU: 85% | Memory: 70% | GPU0: 14.3GB/16.0GB (89.4%)
```
**Good:** Resources are being fully utilized  
**Action:** None needed, training is efficient

### 4. Gradual Memory Growth
```
[METRICS] Memory: 10% → 25% → 45% → 65% → 80%
```
**Issue:** Possible memory leak (data accumulating)  
**Action:**
- Check training code for accidental data accumulation
- Ensure eval_set isn't being duplicated
- Profile memory usage with `memory_profiler`

---

## Viewing Logs in CloudWatch

After training completes, logs are automatically available in CloudWatch:

```bash
# View logs from a completed training job
aws logs get-log-events \
  --log-group-name '/aws/sagemaker/TrainingJobs' \
  --log-stream-name 'xgbregressor-training-20260617120000/algo-1-stdout' \
  --query 'events[*].message' \
  --output text | grep METRICS
```

This shows only the metrics lines:
```
[METRICS] CPU:  15.2% | Memory:  2.3GB/ 16.0GB ( 14.3%)
[METRICS] CPU:  18.5% | Memory:  3.1GB/ 16.0GB ( 19.4%)
[METRICS] CPU:  92.5% | Memory:  8.2GB/ 16.0GB ( 51.3%) | GPU0: 12.3GB/16.0GB (76.9%)
```

---

## Customizing Metrics Logging

### Change logging interval
Default is every 30 seconds. To log more frequently:

```python
# In training/entry.py
with MetricsLogger("TRAINING XGBREGRESSOR", interval_seconds=10) as metrics:
    model.train(...)
```

### Add custom messages with metrics
```python
with MetricsLogger("TRAINING") as metrics:
    for epoch in range(num_epochs):
        model.fit_epoch(...)
        metrics.log(f"Epoch {epoch+1}/{num_epochs} complete")
        # Logs metrics + message at same time
```

### Disable GPU metrics
If you don't have GPU or want to skip GPU monitoring:

```python
# In training/entry.py
from training.metrics import MetricsLogger

# Pass track_gpu=False
with MetricsLogger("TRAINING", track_gpu=False) as metrics:
    model.train(...)
```

---

## Key Insights from Metrics

After collecting metrics from a few training runs, you can optimize:

**1. Instance Type Selection**
- If GPU utilization < 30% with CPU at 90%: Consider CPU-only instance
- If memory at 95% consistently: Need larger instance
- If GPU at 98%: You're using resources well

**2. Batch Size Tuning**
- Memory proportional to batch size
- If memory jumps from 60% → 95% with batch_size +1: Found your limit
- Optimal: Memory at 70-85% (leaves room for spikes)

**3. Training Duration**
- Compare wall-clock time to actual compute time
- If GPU idle periods: Data loading is bottleneck
- If memory stable: Good data pipeline

**4. Cost Optimization**
- If CPU maxed with low GPU/memory: Training is bound by CPU
- If all resources at 85-90%: Instance is well-matched
- If memory spikes then drops: Model needs less memory than allocated

---

## Example: Debugging a Crash

If your training job crashes mid-way:

```bash
# Get LAST 50 lines (usually has the error)
aws logs get-log-events \
  --log-group-name '/aws/sagemaker/TrainingJobs' \
  --log-stream-name 'xgbregressor-training-20260617120000/algo-1-stdout' \
  --query 'events[-50:].message' \
  --output text
```

Look for patterns:
```
[METRICS] CPU: 92% | Memory: 98% (15.7GB/16.0GB)    ← Memory near limit
[METRICS] CPU: 98% | Memory: 99% (15.8GB/16.0GB)    ← Spike!
<crash or slowdown>
```

**Solution:** Reduce batch size or use larger instance

---

## See Also

- [Training Entry Point](entry.py) - Main training script
- [SageMaker MLOps](README.md) - Full pipeline documentation
- [Agent](../agent.py) - How to launch training jobs
