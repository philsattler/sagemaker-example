#!/usr/bin/env python3
"""
End-to-end workflow: train locally → upload to S3 → load and run inference locally
"""

import os
import sys
import tempfile
import logging
import numpy as np
import boto3
from sklearn.model_selection import train_test_split

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from models.xgbregressor import XGBRegressor
from sagemaker_config import S3_PREFIX, S3_BUCKET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_model_locally():
    """Train a model locally with sample data."""
    logger.info("=" * 60)
    logger.info("STEP 1: Training model locally")
    logger.info("=" * 60)

    np.random.seed(42)
    X = np.random.rand(100, 4)
    y = np.random.rand(100)

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    logger.info(f"Training data shape: {X_train.shape}")
    logger.info(f"Validation data shape: {X_val.shape}")

    logger.info("Training XGBRegressor locally...")
    model = XGBRegressor()
    model.train(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=10
    )

    logger.info("Testing local predictions...")
    test_preds = model.predict(X_val[:5])
    logger.info(f"Sample predictions: {test_preds}")

    return model, X_val[:5]

def save_and_upload_to_s3(model, model_name="xgbregressor"):
    """Save model locally then upload to S3."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Saving model and uploading to S3")
    logger.info("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = os.path.join(tmpdir, "model.tar.gz")
        logger.info(f"Saving model to {local_path}")
        model.save(local_path)

        s3_client = boto3.client("s3")
        s3_key = f"{S3_PREFIX}/models/{model_name}/trained-model.tar.gz"
        s3_uri = f"s3://{S3_BUCKET}/{s3_key}"

        logger.info(f"Uploading to S3: {s3_uri}")
        s3_client.upload_file(local_path, S3_BUCKET, s3_key)
        logger.info("✓ Model uploaded to S3")

        return s3_uri

def load_from_s3_and_infer(s3_uri, test_data):
    """Download model from S3 and run inference locally."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Loading model from S3 and running inference")
    logger.info("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        local_model_path = os.path.join(tmpdir, "model.tar.gz")

        # Download from S3
        logger.info(f"Downloading model from S3: {s3_uri}")
        s3_client = boto3.client("s3")

        # Parse S3 URI to get bucket and key
        s3_parts = s3_uri.replace("s3://", "").split("/", 1)
        bucket = s3_parts[0]
        key = s3_parts[1]

        s3_client.download_file(bucket, key, local_model_path)
        logger.info("✓ Model downloaded")

        # Load model
        logger.info("Loading model...")
        model = XGBRegressor()
        model.load(local_model_path)
        logger.info("✓ Model loaded")

        # Run inference
        logger.info(f"Test data shape: {test_data.shape}")
        logger.info(f"Test data:\n{test_data}")

        logger.info("Making predictions...")
        predictions = model.predict(test_data)
        logger.info(f"✓ Predictions: {predictions}")

        return predictions

if __name__ == "__main__":
    try:
        # Train locally
        model, test_data = train_model_locally()

        # Save and upload
        s3_uri = save_and_upload_to_s3(model)

        # Load from S3 and run inference
        predictions = load_from_s3_and_infer(s3_uri, test_data)

        logger.info("\n" + "=" * 60)
        logger.info("✅ Complete workflow finished successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        raise
