"""
Training entry point for SageMaker.
This script runs inside the container and is responsible for:
1. Loading training data
2. Loading the model
3. Training the model
4. Saving the trained model to /opt/ml/model/

SageMaker sets environment variables:
- MODEL_NAME: Name of the model to train (e.g., "xgbregressor")
- SM_CHANNELS_TRAINING: Path to training data
- SM_MODEL_DIR: Path to save model output (default: /opt/ml/model/)
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Add repo root to path so we can import models
sys.path.insert(0, "/opt/ml/code")

from models import load_model
from training.data import load_training_data
from sagemaker_config import get_model_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", type=str, required=True, help="Model name to train")
    parser.add_argument("--hyperparameters", type=str, default="{}", help="JSON hyperparameters")
    args = parser.parse_args()

    model_name = args.model_name
    hyperparameters = json.loads(args.hyperparameters)

    logger.info(f"Training model: {model_name}")
    logger.info(f"Hyperparameters: {hyperparameters}")

    # Get model config
    config = get_model_config(model_name)
    logger.info(f"Model config: {config}")

    # Load training data
    data_dir = os.getenv("SM_CHANNELS_TRAINING", "/opt/ml/input/data/training")
    logger.info(f"Loading data from: {data_dir}")

    X, y = load_training_data(data_dir)
    logger.info(f"Data shape: X={X.shape}, y={y.shape}")

    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Load and train model
    model = load_model(model_name)
    logger.info(f"Training {model_name}...")

    model.train(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=10
    )

    # Save model
    model_dir = os.getenv("SM_MODEL_DIR", "/opt/ml/model")
    model_path = os.path.join(model_dir, "model.tar.gz")
    logger.info(f"Saving model to: {model_path}")
    model.save(model_path)

    logger.info("Training complete!")

if __name__ == "__main__":
    main()
