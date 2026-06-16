# Batch Inference Quick Start

## What You Have

✅ **Lambda** (serverless) - for infrequent small-medium batches  
✅ **EC2** (endpoints) - for large batches or repeated jobs  
✅ **Complete documentation** - README.md with decision trees and cost analysis  
✅ **Working examples** - example_usage.py shows both approaches  

---

## 30-Second Decision

**How often do you run batch inference?**

```
Weekly + small batch (<10GB)     → Use LAMBDA ✅ (fastest, cheapest)
Weekly + large batch (>50GB)     → Use EC2 ✅ (spinup time worth it)
One-off / infrequent small batch → Use LAMBDA ✅ (avoid EC2 overhead)
Multiple batches before cleanup  → Use EC2 (create once, reuse)
```

---

## Try Lambda (Recommended)

### Prerequisites
```bash
# Install Serverless Framework
npm install -g serverless
npm install --save-dev serverless-python-requirements

# Configure AWS
aws configure  # Enter your AWS credentials
```

### Deploy
```bash
cd 1_sagemaker-mlops/batch
serverless deploy
```

### Invoke (test with dummy data)
```bash
# Create test data in S3 first, then:
serverless invoke -f batch-inference -d '{
  "bucket": "my-bucket",
  "input_key": "data/test.csv",
  "output_key": "results/predictions.csv"
}'
```

### Monitor
```bash
serverless logs -f batch-inference --tail
```

### Clean Up
```bash
serverless remove
```

---

## Try EC2 (for large batches)

### Prerequisites
```bash
# Requires a trained model in SageMaker Model Registry
# and proper AWS credentials configured
```

### Usage
```python
from sagemaker.estimator import Estimator

# First, train and register your model
# Then use batch_inference_workflow()

from batch_on_ec2 import batch_inference_workflow

results = batch_inference_workflow(
    input_csv='data/large_batch.csv',
    output_csv='results/predictions.csv',
    model_name='your-model-name',
    instance_type='ml.m5.large'
)

print(f"Processed {results['input_rows']} rows")
print(f"Cost: ${results['cost_estimate']['estimated_cost']:.2f}")
print(f"Total time: {results['timing']['total_sec']:.0f} sec")
```

---

## File Reference

| File | Purpose |
|------|---------|
| `lambda_handler.py` | Lambda function for serverless batch inference |
| `batch_on_ec2.py` | EC2 endpoint batch inference class |
| `serverless.yml` | Deployment configuration for Serverless Framework |
| `lambda_requirements.txt` | Python dependencies for Lambda |
| `README.md` | Detailed docs, cost analysis, decision tree |
| `example_usage.py` | Code examples for both approaches |

---

## Cost Estimates

### Lambda: 10GB batch (infrequent)
```
10GB × 5 min × $0.0001667/GB-sec = $0.32 ✅
```

### EC2: 100GB batch (one time)
```
Endpoint creation (10 min):   $0.269
Inference (30 min):          $0.807
Endpoint deletion (2 min):   $0.054
Total:                       ~$1.13 ✅
(Lambda would cost $300!)
```

---

## Next Steps

1. **Read** [README.md](README.md) for detailed decision guidance
2. **Run** [example_usage.py](example_usage.py) to see both approaches in action
3. **Deploy** Lambda or EC2 based on your use case
4. **Monitor** CloudWatch logs for execution details

---

## Common Issues

**"ModuleNotFoundError: No module named 'boto3'"**
- Install dependencies: `pip install -r lambda_requirements.txt`

**"AWS credentials not configured"**
- Run: `aws configure` and enter your credentials

**"Endpoint creation fails"**
- Make sure your model is in SageMaker Model Registry
- Check that IAM role has SageMaker permissions

**"Lambda timeout"**
- Lambda has a 15-minute timeout limit
- For longer jobs, use EC2 instead

---

## See Also

- [SageMaker MLOps README](../README.md)
- [Batch README (detailed)](README.md)
- [Example Code](example_usage.py)
