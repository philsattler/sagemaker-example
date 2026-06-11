import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ModelConfig:
    """Configuration for a model."""
    instance_type: str
    instance_count: int
    hyperparameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.hyperparameters is None:
            self.hyperparameters = {}

# Model configurations: maps model name to instance type and hyperparameters
MODEL_CONFIG = {
    "xgbregressor": ModelConfig(
        instance_type="ml.m5.xlarge",
        instance_count=1,
        hyperparameters={
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
        }
    ),
    "lightgbmclassifier": ModelConfig(
        instance_type="ml.m5.xlarge",
        instance_count=1,
        hyperparameters={
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
        }
    ),
}

# AWS configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")
SAGEMAKER_ROLE_ARN = os.getenv("SAGEMAKER_ROLE_ARN", "")
ECR_REPO_NAME = os.getenv("ECR_REPO_NAME", "sagemaker-mlops")
ECR_IMAGE_URI = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO_NAME}"

# S3 configuration
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_PREFIX = "sagemaker-artifacts"
S3_TRAINING_OUTPUT = f"s3://{S3_BUCKET}/{S3_PREFIX}/training"
S3_MODEL_ARTIFACTS = f"s3://{S3_BUCKET}/{S3_PREFIX}/models"

def get_model_config(model_name: str) -> ModelConfig:
    """Get configuration for a model."""
    if model_name not in MODEL_CONFIG:
        raise ValueError(f"Unknown model: {model_name}. Available: {list(MODEL_CONFIG.keys())}")
    return MODEL_CONFIG[model_name]

def get_training_image_uri(tag: str = "latest") -> str:
    """Get full ECR image URI for training."""
    return f"{ECR_IMAGE_URI}:{tag}"

def get_s3_model_path(model_name: str) -> str:
    """Get S3 path for model artifacts."""
    return f"{S3_MODEL_ARTIFACTS}/{model_name}"
