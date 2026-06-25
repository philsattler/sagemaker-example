#!/usr/bin/env python3
"""
End-to-end workflow: train locally → upload to S3 → register → deploy → inference
"""

import os
import sys
import tempfile
import logging
import numpy as np
import boto3
from pathlib import Path
from sklearn.model_selection import train_test_split

# Add parent directory to path so imports work
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from models.xgbregressor import XGBRegressor
from inference_controller import InferenceController
from sagemaker_config import S3_PREFIX, S3_BUCKET, AWS_REGION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_model_locally():
    """Train a model locally with sample data."""
    logger.info("=" * 60)
    logger.info("STEP 1: Training model locally")
    logger.info("=" * 60)

    # Create sample data
    logger.info("Creating sample training data...")
    np.random.seed(42)
    X = np.random.rand(100, 4)
    y = np.random.rand(100)

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    logger.info(f"Training data shape: {X_train.shape}")
    logger.info(f"Validation data shape: {X_val.shape}")

    # Train model
    logger.info("Training XGBRegressor locally...")
    model = XGBRegressor()
    model.train(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=10
    )

    # Test local predictions
    logger.info("Testing local predictions...")
    test_preds = model.predict(X_val[:5])
    logger.info(f"Sample predictions: {test_preds}")

    return model, X_val[:5]

def save_and_upload_to_s3(model, model_name="xgbregressor"):
    """Save model locally then upload to S3."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Saving model and uploading to S3")
    logger.info("=" * 60)

    # Save to temporary location
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = os.path.join(tmpdir, "model.tar.gz")
        logger.info(f"Saving model to {local_path}")
        model.save(local_path)

        # Upload to S3
        s3_client = boto3.client("s3")
        s3_key = f"{S3_PREFIX}/models/{model_name}/trained-model.tar.gz"
        s3_uri = f"s3://{S3_BUCKET}/{s3_key}"

        logger.info(f"Uploading to S3: {s3_uri}")
        s3_client.upload_file(local_path, S3_BUCKET, s3_key)
        logger.info("✓ Model uploaded to S3")

        return s3_uri

def register_and_deploy(s3_model_uri, model_name="xgbregressor"):
    """Register model in SageMaker and deploy it."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Registering model in SageMaker")
    logger.info("=" * 60)

    controller = InferenceController()

    # Register the model
    logger.info(f"Registering model from S3: {s3_model_uri}")
    registered_name = controller.register_model_from_s3(
        model_name=model_name,
        s3_model_uri=s3_model_uri
    )
    logger.info(f"✓ Model registered as: {registered_name}")

    # Deploy the model
    logger.info("\n" + "=" * 60)
    logger.info("STEP 4: Deploying model as inference endpoint")
    logger.info("=" * 60)

    endpoint = controller.deploy(model_name=model_name, wait=True)
    logger.info(f"✓ Endpoint deployed: {endpoint.endpoint_name}")

    return endpoint

def run_inference(endpoint, test_data):
    """Run inference on the deployed endpoint."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 5: Running inference on deployed model")
    logger.info("=" * 60)

    logger.info(f"Test data shape: {test_data.shape}")
    logger.info(f"Test data:\n{test_data}")

    # Run predictions
    logger.info("Making predictions via endpoint...")
    predictions = endpoint.predict(test_data)
    logger.info(f"✓ Predictions from endpoint: {predictions}")

    return predictions

def cleanup(endpoint):
    """Delete the endpoint."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 6: Cleanup")
    logger.info("=" * 60)

    logger.info(f"Deleting endpoint: {endpoint.endpoint_name}")
    endpoint.delete()
    logger.info("✓ Endpoint deleted")

if __name__ == "__main__":
    try:
        # Train locally
        model, test_data = train_model_locally()

        # Save and upload
        s3_uri = save_and_upload_to_s3(model)

        # Register and deploy
        endpoint = register_and_deploy(s3_uri)

        # Run inference
        predictions = run_inference(endpoint, test_data)

        # Cleanup
        cleanup(endpoint)

        logger.info("\n" + "=" * 60)
        logger.info("✅ Complete workflow finished successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        raise
