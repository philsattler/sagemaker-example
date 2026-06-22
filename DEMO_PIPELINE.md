# End-to-End SageMaker Pipeline Demo

This demo shows the full ML pipeline with **Spot instance training** and **Lambda serverless inference**.

## Setup (Already Done!)

✅ **S3 Bucket**: `sagemaker-mlops-495811053995`  
✅ **IAM Role**: `SageMakerMLOpsRole`  
✅ **Dataset**: California Housing (s3://sagemaker-mlops-495811053995/data/train.csv)  
✅ **Config**: XGBRegressor with Spot instances enabled  

## Environment Variables

```bash
source .env.local
```

Verify:
```bash
echo $S3_BUCKET
echo $SAGEMAKER_ROLE_ARN
```

## Pipeline Steps

### Step 1: Build Docker Image (One-time)

```bash
# Log into ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 495811053995.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repository if not exists
aws ecr create-repository --repository-name sagemaker-mlops --region us-east-1 2>/dev/null || true

# Build and push Docker image
docker build -t sagemaker-mlops:latest .
docker tag sagemaker-mlops:latest 495811053995.dkr.ecr.us-east-1.amazonaws.com/sagemaker-mlops:latest
docker push 495811053995.dkr.ecr.us-east-1.amazonaws.com/sagemaker-mlops:latest

echo "✓ Docker image pushed to ECR"
```

### Step 2: Train Model with Spot Instances

```bash
python3 << 'PYTHON_EOF'
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "1_sagemaker-mlops"))

from agent import TrainingAgent

# Initialize agent
agent = TrainingAgent(
    role_arn=os.getenv("SAGEMAKER_ROLE_ARN"),
    region=os.getenv("AWS_REGION")
)

# Train model (uses Spot instances for 70% cost savings!)
print("\n🚀 Starting training with Spot instances...\n")
job_name = agent.train(
    model_name="xgbregressor",
    image_tag="latest",
    wait=True  # Wait for completion
)

print(f"\n✓ Training completed: {job_name}")
PYTHON_EOF
```

**What's happening**:
- ✅ Spot instances launched (70% cheaper than on-demand)
- ✅ Data loaded from S3
- ✅ Model trained with system metrics logged
- ✅ Model artifact saved to S3
- ✅ Model automatically registered in Model Registry

### Step 3: Deploy to Lambda

Once training completes, update the model path in your Lambda handler:

```bash
# Get the model path from training job
aws sagemaker describe-training-job \
  --training-job-name <job_name_from_step_2> \
  --query 'ModelArtifacts.S3ModelArtifacts' \
  --output text
```

Update in `1_sagemaker-mlops/batch/lambda_handler.py`:
```python
MODEL_BUCKET = "sagemaker-mlops-495811053995"
MODEL_KEY = "sagemaker-artifacts/models/xgbregressor/<model_name>.tar.gz"
```

### Step 4: Test Lambda Inference

```bash
python3 << 'PYTHON_EOF'
import json
import boto3
import base64

# Create test CSV
test_csv = """MedInc,HouseAge,AveRooms,AveBedrms,Population,AveOccup,Latitude,Longitude
8.3252,41.0,6.984127,1.023810,322.0,2.555556,37.88,-122.23
7.2574,52.0,8.288136,1.081081,496.0,2.802260,37.85,-122.24"""

# Upload to S3
s3 = boto3.client('s3')
s3.put_object(
    Bucket="sagemaker-mlops-495811053995",
    Key="inference/input.csv",
    Body=test_csv
)

print("✓ Test data uploaded to s3://sagemaker-mlops-495811053995/inference/input.csv")
print("\nNext: Deploy and invoke Lambda function")
PYTHON_EOF
```

## Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| **Training (Spot)** | $0.10 | 1hr × ml.m5.large Spot (70% cheaper) |
| **Training Data (S3)** | <$0.01 | 1KB dataset |
| **Model Storage (S3)** | <$0.01 | ~1MB model |
| **Lambda Invocation** | ~$0.20 | 1000 invocations × 5 sec × 3GB |
| **Total** | **~$0.32** | Far cheaper than real-time endpoint ($70/month!) |

## Key Learnings

1. **Spot Instances**: 70% cost savings for batch training
2. **Lambda Inference**: No idle cost, pay only for actual compute
3. **Model Registry**: Automatic versioning and reproducibility
4. **System Metrics**: CloudWatch logs track CPU/memory/GPU utilization

## See Also

- [Interview Prep](1_sagemaker-mlops/.interview-prep.md)
- [Batch Inference](1_sagemaker-mlops/batch/README.md)
- [Training Metrics](1_sagemaker-mlops/METRICS_LOGGING.md)
