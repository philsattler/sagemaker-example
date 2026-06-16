"""
Inference entry point for SageMaker.
This script runs as the model server inside the SageMaker inference endpoint container.

SageMaker environment variables:
- SM_MODEL_DIR: Path to model artifacts (default: /opt/ml/model/)
- SM_CHANNELS_INFERENCE: Path to inference data (if batch)
"""

import os
import sys
import json
import logging
import pickle
from pathlib import Path

import numpy as np

# Add repo root to path
sys.path.insert(0, "/opt/ml/code")

from models import load_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelServer:
    """Simple model server for SageMaker inference."""

    def __init__(self):
        self.model = None
        self.model_name = None
        self._load_model()

    def _load_model(self):
        """Load model from /opt/ml/model/."""
        model_dir = os.getenv("SM_MODEL_DIR", "/opt/ml/model")
        model_path = os.path.join(model_dir, "model.tar.gz")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")

        logger.info(f"Loading model from {model_path}")

        # Read model metadata to determine model type
        import tarfile
        with tarfile.open(model_path, "r:gz") as tar:
            metadata_f = tar.extractfile("metadata.pkl")
            import pickle
            metadata = pickle.load(metadata_f)

        self.model_name = metadata.get("model_type")
        logger.info(f"Model type: {self.model_name}")

        # Load model instance
        self.model = load_model(self.model_name)
        self.model.load(model_path)
        logger.info("Model loaded successfully")

    def predict(self, features):
        """
        Generate predictions for input features.

        Args:
            features: numpy array or list of shape (n_samples, n_features)

        Returns:
            predictions: numpy array of predictions
        """
        if isinstance(features, list):
            features = np.array(features)

        predictions = self.model.predict(features)
        return predictions.tolist() if isinstance(predictions, np.ndarray) else predictions

def main():
    """Start the inference server."""
    server = ModelServer()

    # Simple test inference
    logger.info("Inference server ready")

if __name__ == "__main__":
    main()
