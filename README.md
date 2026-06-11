# SageMaker MLOps Pipeline

An end-to-end MLOps pipeline for training and deploying ML models using AWS SageMaker, ECR, and S3.

## Features

- **Model-agnostic Docker image**: Single container runs any model type
- **SageMaker Model Registry**: Native versioning and lineage tracking
- **Flexible model implementations**: Easily add new model types (XGBoost, LightGBM, etc.)
- **Training orchestration**: Spin up training jobs on-demand
- **Inference endpoints**: Deploy trained models as real-time inference endpoints
- **CI/CD automation**: GitHub Actions auto-builds and pushes Docker images to ECR

## Quick Start

### Prerequisites

1. AWS Account with appropriate IAM permissions
2. S3 bucket for model artifacts
3. ECR repository for Docker images
4. SageMaker execution role with access to S3, ECR, and CloudWatch
5. Python 3.11+

### Setup

1. **Clone the repo**
   ```bash
   git clone <repo-url>
   cd sagemaker-example
   ```

2. **Set environment variables**
   ```bash
   export AWS_REGION=us-east-1
   export AWS_ACCOUNT_ID=123456789012
   export ECR_REPO_NAME=sagemaker-mlops
   export S3_BUCKET=your-account-sagemaker-artifacts
   export SAGEMAKER_ROLE_ARN=arn:aws:iam::123456789012:role/SageMakerMLOpsRole
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create an IAM role** (see IAM Setup section in CLAUDE.md)

### Training a Model

```python
from agent import TrainingAgent

agent = TrainingAgent()

# Start training job
job_name = agent.train(
    model_name="xgbregressor",
    image_tag="latest",
    wait=True  # Wait for job to complete
)

print(f"Training job: {job_name}")

# Check job status
job_info = agent.describe_job(job_name)
print(f"Status: {job_info['TrainingJobStatus']}")
```

View logs in SageMaker console: **Training → Jobs → [job_name] → Logs**

### Deploying an Inference Endpoint

```python
from controller import InferenceController

controller = InferenceController()

# Deploy latest model version
endpoint = controller.deploy(
    model_name="xgbregressor",
    wait=True  # Wait for endpoint to be active
)

print(f"Endpoint: {endpoint}")

# Make predictions
test_data = [[1.0, 2.0, 3.0, 4.0]]
predictions = endpoint.predict(test_data)
print(f"Predictions: {predictions}")

# Cleanup when done
endpoint.delete()
```

### Adding a New Model Type

1. Create `models/mynewmodel.py`:
   ```python
   from models.base import BaseModel

   class MyNewModel(BaseModel):
       def __init__(self, **kwargs):
           super().__init__()
           # Initialize model

       def train(self, X, y, **kwargs):
           # Training logic
           pass

       def predict(self, X):
           # Prediction logic
           pass
   ```

2. Register in `sagemaker_config.py`:
   ```python
   MODEL_CONFIG = {
       # ... existing models ...
       "mynewmodel": ModelConfig(
           instance_type="ml.m5.xlarge",
           instance_count=1,
           hyperparameters={"param1": "value1"}
       )
   }
   ```

3. Add to `models/__init__.py`:
   ```python
   from models.mynewmodel import MyNewModel

   models = {
       # ... existing mappings ...
       "mynewmodel": MyNewModel,
   }
   ```

## Project Structure

```
.
├── CLAUDE.md                          # Architecture documentation
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── iam_policy.json                    # IAM permissions policy
├── sagemaker_config.py                # Model configs and AWS settings
├── agent.py                           # Training orchestrator
├── controller.py                      # Inference orchestrator
├── models/
│   ├── base.py                        # Abstract base class
│   ├── xgbregressor.py                # XGBoost example
│   └── lightgbmclassifier.py          # LightGBM example
├── training/
│   ├── entry.py                       # Training entry point (runs in container)
│   └── data.py                        # Data loading utilities
├── inference/
│   └── entry.py                       # Inference entry point (runs in container)
├── docker/
│   ├── Dockerfile                     # Container definition
│   └── entrypoint.sh                  # Container entry script
└── .github/workflows/
    └── docker-build-push.yml          # GitHub Action for CI/CD
```

## Local Testing

Test models locally before pushing to ECR:

```bash
# Test training
python -c "
from models.xgbregressor import XGBRegressor
import numpy as np

X = np.random.rand(100, 4)
y = np.random.rand(100)

model = XGBRegressor()
model.train(X, y)
print('Training successful!')
"

# Test inference
python -c "
from models.xgbregressor import XGBRegressor
import numpy as np

X_test = np.random.rand(10, 4)
model = XGBRegressor()
model.train(np.random.rand(100, 4), np.random.rand(100))
predictions = model.predict(X_test)
print(f'Predictions: {predictions}')
"
```

## Docker Build Locally

```bash
docker build -t sagemaker-mlops:latest -f docker/Dockerfile .

# Test training
docker run \
  -e MODEL_NAME=xgbregressor \
  -e PHASE=train \
  -v /path/to/data:/opt/ml/input/data/training \
  -v /tmp/model:/opt/ml/model \
  sagemaker-mlops:latest

# Check output
ls -la /tmp/model/
```

## AWS Setup

### 1. Create IAM Role

Use the policy in `iam_policy.json` to create a new IAM role with trust relationship for SageMaker.

```bash
aws iam create-role --role-name SageMakerMLOpsRole \
  --assume-role-policy-document file://trust-policy.json

aws iam put-role-policy --role-name SageMakerMLOpsRole \
  --policy-name SageMakerMLOpsPolicy \
  --policy-document file://iam_policy.json
```

### 2. Create S3 Bucket

```bash
aws s3 mb s3://your-account-sagemaker-artifacts --region us-east-1
```

### 3. Create ECR Repository

```bash
aws ecr create-repository --repository-name sagemaker-mlops --region us-east-1
```

### 4. Set Environment Variables

Update `.env` or export in shell:
```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=123456789012
export ECR_REPO_NAME=sagemaker-mlops
export S3_BUCKET=your-account-sagemaker-artifacts
export SAGEMAKER_ROLE_ARN=arn:aws:iam::123456789012:role/SageMakerMLOpsRole
```

## CI/CD: GitHub Actions

The `.github/workflows/docker-build-push.yml` workflow:
1. Builds Docker image on every push
2. Tags with commit SHA and `latest`
3. Pushes to ECR

**Required GitHub secrets**:
- `AWS_REGION`: AWS region (e.g., `us-east-1`)
- `AWS_ROLE_TO_ASSUME`: ARN of role to assume for OIDC auth
- `ECR_REPO_NAME`: Name of ECR repository (default: `sagemaker-mlops`)

## Troubleshooting

### Docker build fails locally
```bash
docker build -t test docker/ --progress=plain
# Check error messages and fix before pushing
```

### Training job stuck
Check logs in SageMaker console:
- Navigate to **Training → Training jobs → [job_name] → Logs**
- Also check CloudWatch logs in **CloudWatch → Log groups → /aws/sagemaker/TrainingJobs**

### Model not found
Ensure model name is registered in `sagemaker_config.py` and `models/__init__.py`

### ECR authentication fails
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

### Endpoint deployment fails
Check IAM permissions and S3 bucket access. Verify:
- Role has S3 read permissions
- Bucket policy allows SageMaker role
- Model artifacts exist at expected S3 path

## Next Steps

1. Add model validation step (test on holdout set before registry)
2. Add monitoring and drift detection
3. Add batch inference mode
4. Set up automated retraining schedule
5. Add cost optimization (spot instances, auto-scaling)

## Contributing

1. Create a new branch
2. Add your changes
3. Test locally with Docker
4. Commit and push
5. GitHub Action will build and push to ECR

## License

MIT
