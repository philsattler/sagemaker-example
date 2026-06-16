# Training vs Inference Compute Optimization

Your SageMaker setup now separates training and inference instance types, so you can optimize for each workload.

## The Problem We Fixed

**Before**: Training and inference used the same instance type
```python
ModelConfig(instance_type="ml.m5.large")  # ← Used for BOTH
```

**After**: Separate types for training and inference
```python
ModelConfig(
    training_instance_type="ml.p3.2xlarge",    # ← Training (GPU, expensive)
    inference_instance_type="ml.t3.medium"      # ← Inference (CPU, cheap)
)
```

---

## Why This Matters

### Training
- **Runs infrequently** (weekly, monthly)
- **Needs speed** (GPU accelerates training 10-100x)
- **Can tolerate high cost** (runs for 2-4 hours, not 24/7)
- **Best choice**: ml.p3.2xlarge ($3.06/hour)

### Inference
- **Runs continuously** (24/7 or on-demand)
- **Throughput matters** (but XGBoost/LightGBM are CPU-efficient)
- **Cost is critical** (runs thousands of hours/year)
- **Best choice**: ml.t3.medium ($0.042/hour)

---

## Cost Comparison

### Scenario: Weekly training + 24/7 inference endpoint

**Old Setup** (both on ml.m5.large):
```
Training: 1 job/week × 3 hours × $0.096/hour = $0.29/week
Inference: 24/7 × $0.096/hour = $67/month
Total: ~$291/month
```

**New Setup** (training on GPU, inference on CPU):
```
Training: 1 job/week × 3 hours × $3.06/hour = $9.18/week ($37/month)
Inference: 24/7 × $0.042/hour = $30/month
Total: ~$67/month  ← 77% cheaper! ✅
```

**Savings: $224/month** (or ~$2,700/year)

---

## Default Configurations

Preconfigured instance types in `sagemaker_config.py`:

| Model | Training (Expensive) | Inference (Cheap) | Training Time | Inference Latency |
|-------|----------------------|-------------------|---------------|-------------------|
| XGBoost | ml.p3.2xlarge (GPU) | ml.t3.medium (CPU) | ~2 hours | ~100ms |
| LightGBM | ml.p3.2xlarge (GPU) | ml.t3.medium (CPU) | ~1 hour | ~50ms |

---

## How to Use

### Training (uses GPU)
```python
from agent import TrainingAgent

agent = TrainingAgent()
job_name = agent.train(model_name="xgbregressor")
# Automatically uses ml.p3.2xlarge (GPU) ✅
```

### Inference (uses cheap CPU)
```python
from controller import InferenceController

controller = InferenceController()
endpoint = controller.deploy(model_name="xgbregressor")
# Automatically uses ml.t3.medium (CPU) ✅
```

### Override Instance Type (if needed)
```python
# Use different instance for specific deployment
endpoint = controller.deploy(
    model_name="xgbregressor",
    instance_type="ml.m5.large",        # Override default
    instance_count=2                     # Scale out
)
```

---

## Customization

Edit `sagemaker_config.py` to change instance types:

```python
MODEL_CONFIG = {
    "xgbregressor": ModelConfig(
        # Change training instance (GPU options):
        # - ml.p3.2xlarge: $3.06/hour (1 GPU) - fastest
        # - ml.p3.8xlarge: $12.24/hour (4 GPUs) - huge datasets
        # - ml.g4dn.xlarge: $0.526/hour (1 GPU) - budget GPU
        training_instance_type="ml.p3.2xlarge",

        # Change inference instance (CPU options):
        # - ml.t3.small: $0.021/hour - minimal load
        # - ml.t3.medium: $0.042/hour - low load (default)
        # - ml.t3.large: $0.084/hour - moderate load
        # - ml.m5.large: $0.096/hour - higher load
        inference_instance_type="ml.t3.medium",
    ),
}
```

---

## Instance Type Guide

### For Training (pick ONE based on data size)

| Instance | GPU | Cost/Hour | Batch Size | Good For |
|----------|-----|-----------|-----------|----------|
| ml.p3.2xlarge | 1×V100 | $3.06 | Small-medium | Most models ✅ |
| ml.p3.8xlarge | 4×V100 | $12.24 | Large | Huge datasets |
| ml.g4dn.xlarge | 1×T4 | $0.526 | Small | Budget training |
| ml.m5.2xlarge | None | $0.384 | Tiny | CPU-only models |

**Recommendation**: Start with `ml.p3.2xlarge` (1 GPU), it's the sweet spot.

### For Inference (pick ONE based on expected QPS)

| Instance | vCPU | Memory | Cost/Hour | QPS | Good For |
|----------|------|--------|-----------|-----|----------|
| ml.t3.small | 2 | 2GB | $0.021 | ~5 | Experimental |
| ml.t3.medium | 2 | 4GB | $0.042 | ~10 | Low traffic ✅ |
| ml.t3.large | 2 | 8GB | $0.084 | ~20 | Moderate |
| ml.m5.large | 2 | 8GB | $0.096 | ~30 | High traffic |
| ml.m5.2xlarge | 8 | 32GB | $0.384 | ~100 | Very high |

**Recommendation**: Start with `ml.t3.medium` for batch inference, scale to ml.m5 if you add real-time endpoints.

---

## When to Scale

### Scale Training (bigger GPU)
```
❌ DON'T if: Training < 1 hour (overhead not worth it)
✅ DO if: Training > 4 hours (GPU speedup saves time & money)
```

### Scale Inference (more instances)
```
❌ DON'T if: < 10 requests/minute (single instance fine)
✅ DO if: > 100 requests/minute (need 2+ instances)
```

Set via override:
```python
endpoint = controller.deploy(
    model_name="xgbregressor",
    instance_count=2  # Run on 2 instances for HA + throughput
)
```

---

## Files Updated

- `sagemaker_config.py`: Added separate `training_instance_type` and `inference_instance_type`
- `agent.py`: Uses `training_instance_type` for training jobs
- `controller.py`: Uses `inference_instance_type` for inference endpoints

---

## Next Steps

1. **Try it**: `python agent.py` trains on GPU, `python controller.py` deploys on cheap CPU
2. **Monitor costs**: Check CloudWatch to see actual training/inference duration
3. **Tune instances**: If training still slow, upgrade GPU. If inference latency high, upgrade CPU.
4. **Add auto-scaling**: For real-time endpoints, enable target tracking to scale based on load

---

## Cost Monitoring

Check SageMaker costs in AWS Console:
1. CloudWatch → Billing
2. Filter by: `ml.p3.2xlarge` (training) vs `ml.t3.medium` (inference)
3. Set alerts if monthly bill exceeds budget

---

## See Also

- [SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
- [Instance Types & Pricing](https://aws.amazon.com/sagemaker/pricing/)
- [Training vs Inference Best Practices](https://docs.aws.amazon.com/sagemaker/latest/dg/how-it-works.html)
