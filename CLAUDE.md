# SageMaker MLOps Pipeline

## Project Overview

This repo implements an end-to-end MLOps pipeline for iterating on multiple model types (XGBRegressor, LightGBMClassifier, etc.) using AWS SageMaker for training and inference orchestration.

**Key principle**: Model-agnostic Docker image + dynamic model loading from S3. One container handles all model types; different implementations load at runtime.

## Architecture Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Model Registry | SageMaker Model Registry | Native versioning, approval workflows, lineage tracking |
| Job Triggers | Manual via Python API/CLI | Simple, on-demand; can add EventBridge scheduling later |
| Docker Strategy | Model-agnostic | One image for all models; reduces rebuild overhead |
| Observability | SageMaker native logs | No external orchestrator (Prefect/Airflow) needed |
| State Management | S3 + SageMaker Model Registry | Tarball artifacts in S3, metadata in registry |

## File Structure

```
.
├── CLAUDE.md                          # This file
├── README.md                          # Usage guide
├── docker/
│   └── Dockerfile                     # Model-agnostic training/inference image
├── sagemaker_config.py                # Model → EC2 instance type mapping, SageMaker job config
├── iam_policy.json                    # IAM permissions (SageMaker ↔ S3, ECR, CloudWatch)
├── models/
│   ├── __init__.py
│   ├── base.py                        # Abstract base class for all models
│   ├── xgbregressor.py                # Example: XGBoost regressor
│   └── lightgbmclassifier.py          # Example: LightGBM classifier
├── training/
│   ├── __init__.py
│   ├── entry.py                       # SageMaker training entry point (called inside container)
│   └── data.py                        # Data loading and preprocessing
├── inference/
│   ├── __init__.py
│   ├── entry.py                       # SageMaker inference entry point (called inside container)
│   └── predictor.py                   # Prediction logic
├── agent.py                           # Training orchestrator (launches SageMaker jobs)
├── controller.py                      # Inference orchestrator (spins up endpoints)
├── .github/workflows/
│   └── docker-build-push.yml          # GitHub Action: build Docker image, push to ECR
└── requirements.txt                   # Python dependencies
```

## Workflows

### Training Workflow

```
User calls: agent.train(model_name="xgbregressor")
    ↓
Agent pulls model code from repo
    ↓
Agent calls SageMaker.create_training_job()
    ↓
SageMaker spins up EC2 instance (as per sagemaker_config)
    ↓
SageMaker pulls Docker image from ECR
    ↓
Container runs training/entry.py
    ↓
Model artifacts saved to S3 (tarball)
    ↓
Agent registers model in SageMaker Model Registry
    ↓
Logs viewable in SageMaker console
```

### Inference Workflow

```
User calls: controller.predict(model_name="xgbregressor", features=[...])
    ↓
Controller queries SageMaker Model Registry for latest version
    ↓
Controller calls SageMaker.create_endpoint()
    ↓
SageMaker spins up EC2 instance
    ↓
SageMaker pulls Docker image from ECR + model tarball from S3
    ↓
Container runs inference/entry.py
    ↓
Endpoint accepts inference requests
    ↓
Predictions returned
```

## Development Workflow

### 1. Add a New Model Type

Create `models/mynewmodel.py`:
```python
from models.base import BaseModel

class MyNewModel(BaseModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize your model
    
    def train(self, X, y):
        # Training logic
        pass
    
    def predict(self, X):
        # Prediction logic
        pass
    
    def save(self, path):
        # Save to path (will be tarball'd)
        pass
    
    def load(self, path):
        # Load from path
        pass
```

Register in `sagemaker_config.py`:
```python
MODEL_CONFIG = {
    "mynewmodel": {
        "instance_type": "ml.m5.xlarge",
        "instance_count": 1,
        "entry_module": "mynewmodel"
    }
}
```

### 2. Local Testing

Test your model locally before pushing to ECR:
```bash
# Test training
python -c "from models.mynewmodel import MyNewModel; m = MyNewModel(); m.train(...)"

# Test inference
python -c "from models.mynewmodel import MyNewModel; m = MyNewModel(); m.load(...); m.predict(...)"
```

### 3. Push to ECR

GitHub Action automatically builds and pushes on commit:
- Trigger: `git push` to any branch
- Action: Build Docker image, tag with commit SHA, push to ECR

### 4. Start Training Job

```python
from agent import TrainingAgent

agent = TrainingAgent()
job_name = agent.train(model_name="xgbregressor")
# Check logs: SageMaker console → Training → Job name → Logs
```

### 5. Deploy Inference Endpoint

```python
from controller import InferenceController

controller = InferenceController()
endpoint = controller.deploy(model_name="xgbregressor")
predictions = endpoint.predict(features=[...])
```

## AWS Setup

### 1. IAM Role

Create a role with policy from `iam_policy.json`. This role must be:
- Assumable by SageMaker
- Assumable by EC2
- Assumable by your local user (for manual agent/controller calls)

### 2. ECR Repository

Create an ECR repo named `sagemaker-mlops` (or update `docker-build-push.yml`).

### 3. S3 Bucket

Create S3 bucket for model artifacts (e.g., `your-account-sagemaker-artifacts`). Update paths in `sagemaker_config.py`.

### 4. Environment Variables

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=123456789012
export ECR_REPO_NAME=sagemaker-mlops
export S3_BUCKET=your-account-sagemaker-artifacts
export SAGEMAKER_ROLE_ARN=arn:aws:iam::123456789012:role/SageMakerMLOpsRole
```

## Key Files Explained

### `sagemaker_config.py`
Maps model names to SageMaker job configs (instance type, count, hyperparameters). Used by both `agent.py` and `controller.py`.

### `docker/Dockerfile`
Single image that:
- Installs training/inference dependencies
- Copies model implementations from repo
- Accepts environment variable `MODEL_NAME` and `PHASE` (train/inference)
- Runs appropriate entry point

### `models/base.py`
Abstract interface all models must implement:
- `train(X, y)`
- `predict(X)`
- `save(path)` → tarball model artifacts
- `load(path)` ← restore from tarball

### `agent.py`
Orchestrates training:
- Takes model name, pulls config from `sagemaker_config.py`
- Creates SageMaker training job with ECR image
- Polls for completion, saves logs
- Registers model in Model Registry with S3 path

### `controller.py`
Orchestrates inference:
- Queries Model Registry for latest model version
- Creates SageMaker endpoint with ECR image
- Loads model artifacts from S3
- Routes prediction requests to endpoint
- Can delete endpoint when done

## Debugging

**Training job stuck**: Check SageMaker console → Training jobs → Logs tab.

**Model not registering**: Verify S3 tarball exists and path is correct in `agent.py`.

**Endpoint won't deploy**: Check ECR image exists and IAM role has S3 read permissions.

**Docker build fails**: Run `docker build docker/ -t test` locally to debug.

## Future Enhancements

- Add EventBridge scheduler for automatic daily retraining
- Add model validation step (test on holdout set before registry)
- Add monitoring dashboard (CloudWatch metrics, model drift detection)
- Add model rollback mechanism (revert to previous version)
- Add batch inference mode (process S3 data, write results back)
