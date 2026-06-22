import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ModelConfig:
    """Configuration for a model (training and inference)."""
    # Training instances (ephemeral, used once per training)
    training_instance_type: str
    training_instance_count: int = 1
    use_spot: bool = False  # Use Spot instances for training (saves ~70% cost)

    # Inference instances (persistent, can run 24/7)
    inference_instance_type: str = None  # If None, defaults to training_instance_type
    inference_instance_count: int = 1

    hyperparameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.hyperparameters is None:
            self.hyperparameters = {}
        # Fallback: if inference not specified, use training instance
        if self.inference_instance_type is None:
            self.inference_instance_type = self.training_instance_type

# Model configurations
MODEL_CONFIG = {
    "xgbregressor": ModelConfig(
        # Training: Use Spot instances to save cost (70% cheaper)
        training_instance_type="ml.m5.large",  # CPU-only for demo, Spot saves cost
        training_instance_count=1,
        use_spot=True,

        # Inference: Use Lambda for serverless (no endpoint cost)
        inference_instance_type="ml.t3.medium",  # Fallback for real-time endpoints
        inference_instance_count=1,

        hyperparameters={
            "n_estimators": 50,
            "max_depth": 5,
            "learning_rate": 0.1,
        }
    ),
    "lightgbmclassifier": ModelConfig(
        # Training: GPU for faster training
        training_instance_type="ml.p3.2xlarge",
        training_instance_count=1,

        # Inference: Cheaper CPU
        inference_instance_type="ml.t3.medium",
        inference_instance_count=1,

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
