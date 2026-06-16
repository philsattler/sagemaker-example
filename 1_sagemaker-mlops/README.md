# 🚀 SageMaker MLOps Pipeline

End-to-end MLOps pipeline for iterating on multiple model types (XGBRegressor, LightGBMClassifier) using AWS SageMaker for training and inference orchestration.

## Key Principle
**Model-agnostic Docker image + dynamic model loading from S3.** One container handles all model types; different implementations load at runtime.

## Quick Start

```bash
# Train a model
python agent.py --model xgbregressor

# Deploy for inference
python controller.py --model xgbregressor

# Make predictions
python controller.py --predict --features "[1.0, 2.0, 3.0]"
```

## Architecture

- **Training**: `agent.py` orchestrates SageMaker training jobs
- **Inference**: `controller.py` manages endpoints and predictions
- **Models**: `models/` implements different model types
- **Docker**: `../docker/Dockerfile` builds the container
- **Configuration**: `sagemaker_config.py` maps models to EC2 instance types

## Files

- `agent.py` - Training orchestrator
- `controller.py` - Inference orchestrator
- `sagemaker_config.py` - Model → EC2 instance mapping
- `models/` - Model implementations (XGBoost, LightGBM, etc.)
- `training/` - SageMaker training entry point
- `inference/` - SageMaker inference entry point
- `.github/workflows/` - CI/CD for Docker builds

## AWS Setup

1. Create IAM role with SageMaker permissions
2. Create ECR repository (`sagemaker-mlops`)
3. Create S3 bucket for artifacts
4. Set environment variables:
   ```bash
   export AWS_REGION=us-east-1
   export SAGEMAKER_ROLE_ARN=arn:aws:iam::ACCOUNT:role/SageMakerRole
   export S3_BUCKET=your-bucket
   ```

## See Also

- [Full documentation](../docs/CLAUDE.md)
- [RAG System](../2_rag-system/)
- [Spark Learning](../3_spark-learning/)
