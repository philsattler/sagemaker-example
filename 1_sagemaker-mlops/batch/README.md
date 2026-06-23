# Batch Inference: Lambda vs EC2

Two approaches for batch predictions: serverless (Lambda) and managed endpoints (EC2).

## Quick Decision Matrix

| Factor | Lambda | EC2 |
|--------|--------|-----|
| **Spinup time** | 5-10 sec | 5-10 min ⚠️ |
| **Cost (small batch < 10GB)** | $0.32 ✅ | $0.048 |
| **Cost (large batch 100GB)** | $32 | $0.48 ✅ |
| **Cold start latency** | ~5 sec | N/A |
| **Operational overhead** | None ✅ | Delete endpoint |
| **Best for** | Infrequent small-medium | Large / frequent |

**TL;DR**: 
- **Use Lambda** for infrequent batch jobs (weekly, daily, one-off)
- **Use EC2** for large batches (100GB+) or frequent batching

---

## ⚡ Quick Start (Automated)

**From the batch directory:**

```bash
# 1. Train model locally
python3 ../train_locally.py

# 2. Deploy to Lambda (auto-configures everything)
python3 deploy.py

# 3. Test inference
python3 test_inference.py
```

That's it! The scripts handle model discovery, configuration, and deployment automatically.

---

## 🚀 Option 1: Serverless Lambda (Recommended for Most Cases)

### Advantages
✅ **Fast to start**: 5-10 second cold start (vs 5-10 minute endpoint creation)  
✅ **Zero overhead**: No cleanup, no accidental runaway costs  
✅ **Cheap for small batches**: ~$0.32 per batch for 10GB  
✅ **Auto-scaling**: Handle traffic spikes automatically  
✅ **Easy deployment**: One command to deploy  

### Disadvantages
❌ **Expensive for huge batches**: > 100GB data moves → EC2  
❌ **15 minute timeout limit**: Can't run forever  
❌ **Memory cap at 10GB**: Can't load larger models  

### Setup

#### 1. Install Serverless Framework
```bash
npm install -g serverless
npm install --save-dev serverless-python-requirements
```

#### 2. Deploy
```bash
cd 1_sagemaker-mlops/batch
serverless deploy
```

#### 3. Invoke

**Via AWS CLI:**
```bash
aws lambda invoke --function-name batch-inference-batch-inference \
  --payload '{"bucket":"my-bucket","input_key":"data.csv"}' \
  response.json

cat response.json
```

**Via Python:**
```python
import boto3
import json

client = boto3.client('lambda')

response = client.invoke(
    FunctionName='batch-inference-batch-inference',
    InvocationType='RequestResponse',  # Wait for result
    Payload=json.dumps({
        'bucket': 'my-bucket',
        'input_key': 'data/weekly_batch.csv',
        'output_key': 'results/weekly_predictions.csv',
        'model_bucket': 'my-bucket',
        'model_key': 'models/xgb_model.pkl'
    })
)

result = json.loads(response['Payload'].read())
print(f"Processed {result['rows_processed']} rows")
print(f"Results: {result['output_location']}")
```

#### 4. Monitor Logs
```bash
serverless logs -f batch-inference --tail
```

#### 5. Clean Up
```bash
serverless remove
```

### Cost Example: 10GB Batch

```
Lambda: 10GB × 16 min × $0.0001667/GB-sec = $0.32
vs
EC2:    m5.large × 22 min (creation + inference + deletion) = $0.05

But EC2 has 6-12 min overhead!
If inference only takes 2 min, Lambda is better.
```

---

## 🏗️ Option 2: EC2 Endpoints

### Advantages
✅ **Good for large batches**: 100GB+ data (endpoint overhead becomes negligible)  
✅ **Higher throughput**: Can process faster with larger instances  
✅ **Unlimited time**: No timeout limit  
✅ **Better for repeated batching**: Create once, run multiple batches, then delete  

### Disadvantages
❌ **Slow to start**: 5-10 minute endpoint creation time  
❌ **Operational burden**: Must explicitly delete endpoint (or burn money)  
❌ **Worse for infrequent jobs**: Spinup time overshadows inference  
❌ **More expensive for small batches**: Cost of endpoint creation dominates  

### Setup

#### 1. Load Model into SageMaker

First, train and save a model:
```python
from sagemaker.estimator import Estimator
import sagemaker

# In your training script
session = sagemaker.Session()
role = sagemaker.get_execution_role()

estimator = Estimator(
    image_uri='your-ecr-uri',
    role=role,
    instance_count=1,
    instance_type='ml.m5.xlarge',
    output_path=f's3://{session.default_bucket()}/models'
)

estimator.fit(training_data)
model = estimator.create_model(name='xgb-model')
```

#### 2. Use for Batch Inference

```python
from batch_on_ec2 import batch_inference_workflow

results = batch_inference_workflow(
    input_csv='data/large_batch.csv',
    output_csv='results/predictions.csv',
    model_name='xgb-model',
    instance_type='ml.m5.large'  # Adjust based on data size
)

print(f"Processed {results['input_rows']} rows")
print(f"Total time: {results['timing']['total_sec']:.0f} sec")
print(f"Cost estimate: ${results['cost_estimate']['estimated_cost']:.2f}")
```

Or manual control:

```python
from batch_on_ec2 import BatchInferenceEC2
import pandas as pd

# Create batch processor
batch = BatchInferenceEC2(
    model_name='xgb-model',
    instance_type='ml.m5.xlarge',
    instance_count=1
)

# Create endpoint
batch.create_endpoint(wait=True)

# Load and predict
df = pd.read_csv('data/large_batch.csv')
predictions = batch.batch_predict(df, batch_size=5000)

# Save results
df['prediction'] = predictions
df.to_csv('results/predictions.csv', index=False)

# Clean up!
batch.delete_endpoint(wait=True)
```

### Cost Example: 100GB Batch

```
Scenario: XGBoost inference on 100GB data, m5.xlarge instance

EC2:
- Endpoint creation (10 min): $0.269
- Inference (30 min):        $0.807
- Deletion (2 min):          $0.054
- Total:                     ~$1.13 ✅

Lambda:
- 100GB × 30 min × $0.0001667/GB-sec = $300 ❌

Decision: EC2 wins decisively for 100GB!
```

---

## Decision Tree

```
How often do you run batch inference?

├─ DAILY or MORE FREQUENT
│  └─ Keep endpoint warm (don't delete)
│     └─ Use SageMaker endpoint (not batch)
│
├─ WEEKLY
│  ├─ Batch size < 10GB?
│  │  └─ Use LAMBDA (cold start is fine)
│  │
│  └─ Batch size > 50GB?
│     └─ Use EC2 (spinup time negligible)
│
└─ MONTHLY or ONE-OFF
   ├─ Batch size < 10GB?
   │  └─ Use LAMBDA ✅ (best value)
   │
   └─ Batch size > 50GB?
      └─ Use EC2 (spinup worth it)
```

---

## Files

### Lambda Implementation
- `lambda_handler.py` - Main Lambda function
- `serverless.yml` - Deployment configuration
- `lambda_requirements.txt` - Python dependencies

### EC2 Implementation
- `batch_on_ec2.py` - Batch inference class
  - `BatchInferenceEC2`: Low-level endpoint control
  - `batch_inference_workflow()`: High-level wrapper with timing/cost tracking

---

## Common Questions

**Q: Can Lambda handle my 50GB batch?**  
A: Yes, but it'll cost ~$16. EC2 would be ~$0.50 for the same job. Use EC2 for anything > 20GB.

**Q: What if my inference takes > 15 minutes?**  
A: Lambda has a hard 15-minute timeout. Use EC2 (no timeout) or split the batch.

**Q: Can I use Lambda for daily batch jobs?**  
A: Yes, but consider keeping a warm SageMaker endpoint instead. Daily traffic doesn't justify Lambda's cold start overhead.

**Q: How do I reduce Lambda cold start time?**  
A: Provisioned concurrency (~$0.015/hour), but expensive if idle. For infrequent jobs, just accept 5-10 sec cold start.

**Q: Can I parallelize across Lambda invocations?**  
A: Yes! Split your data, invoke Lambda N times in parallel, combine results. Each invocation gets its own container.

---

## Next Steps

1. **For infrequent small batches**: Use Lambda
   ```bash
   serverless deploy
   serverless invoke -f batch-inference -d '...'
   ```

2. **For large batches or repeated jobs**: Use EC2
   ```python
   from batch_on_ec2 import batch_inference_workflow
   batch_inference_workflow(...)
   ```

3. **For always-on inference**: Use warm SageMaker endpoint
   - See `../controller.py` for endpoint management

---

## See Also

- [SageMaker MLOps Overview](../README.md)
- [Controller (Endpoint Management)](../controller.py)
- [Agent (Training)](../agent.py)
