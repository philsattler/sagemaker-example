"""
Inference Controller: Orchestrates SageMaker inference endpoints.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

import boto3
import numpy as np
from sagemaker.session import Session
from sagemaker.model import Model

from sagemaker_config import (
    get_model_config,
    get_training_image_uri,
    AWS_REGION,
    SAGEMAKER_ROLE_ARN,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InferenceController:
    """Orchestrates model inference on SageMaker."""

    def __init__(self, role_arn: Optional[str] = None, region: str = AWS_REGION):
        self.role_arn = role_arn or SAGEMAKER_ROLE_ARN
        self.region = region
        self.sagemaker_session = Session(default_bucket=None)
        self.sm_client = boto3.client("sagemaker", region_name=region)

        if not self.role_arn:
            raise ValueError("SAGEMAKER_ROLE_ARN not set. Set via environment or pass to __init__")

        self.endpoints = {}  # Track active endpoints

    def deploy(
        self,
        model_name: str,
        model_version: Optional[str] = None,
        instance_type: Optional[str] = None,
        instance_count: Optional[int] = None,
        wait: bool = True,
    ) -> "InferenceEndpoint":
        """
        Deploy a model to a SageMaker inference endpoint.

        Args:
            model_name: Name of model to deploy
            model_version: Specific model version (latest if not specified)
            instance_type: EC2 instance type (uses inference config if not specified)
            instance_count: Number of instances (uses inference config if not specified)
            wait: Whether to wait for endpoint to be active

        Returns:
            InferenceEndpoint: Endpoint object for making predictions
        """
        config = get_model_config(model_name)
        # Use inference-specific instance type and count (not training)
        instance_type = instance_type or config.inference_instance_type
        instance_count = instance_count or config.inference_instance_count

        # Get latest model from registry
        model_name_obj = self._get_latest_model(model_name, model_version)

        endpoint_name = self._generate_endpoint_name(model_name)

        logger.info(f"Deploying endpoint: {endpoint_name}")
        logger.info(f"Model: {model_name_obj}, Instance: {instance_type}")

        # Create endpoint configuration
        self.sm_client.create_endpoint_config(
            EndpointConfigName=endpoint_name,
            ProductionVariants=[
                {
                    "VariantName": "default",
                    "ModelName": model_name_obj,
                    "InstanceType": instance_type,
                    "InitialInstanceCount": instance_count,
                }
            ],
        )

        # Create endpoint
        self.sm_client.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_name,
        )

        logger.info(f"Endpoint creation started: {endpoint_name}")

        if wait:
            self._wait_for_endpoint(endpoint_name)
            logger.info(f"Endpoint is active: {endpoint_name}")

        endpoint = InferenceEndpoint(
            endpoint_name=endpoint_name,
            model_name=model_name,
            sm_client=self.sm_client,
        )

        self.endpoints[endpoint_name] = endpoint
        return endpoint

    def _get_latest_model(self, model_name: str, version: Optional[str] = None) -> str:
        """Get the latest model from SageMaker Model Registry."""
        logger.info(f"Fetching latest model: {model_name}")

        # Query model registry for models matching the name
        response = self.sm_client.list_models(NameContains=model_name)
        models = response.get("ModelSummaries", [])

        if not models:
            raise ValueError(f"No models found for {model_name}")

        # Sort by creation time, get latest
        models = sorted(models, key=lambda x: x["CreationTime"], reverse=True)
        model_name_obj = models[0]["ModelName"]

        logger.info(f"Latest model: {model_name_obj}")
        return model_name_obj

    def _wait_for_endpoint(self, endpoint_name: str, timeout: int = 3600) -> None:
        """Wait for endpoint to be in service."""
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = self.sm_client.describe_endpoint(EndpointName=endpoint_name)
            status = response["EndpointStatus"]

            logger.info(f"Endpoint status: {status}")

            if status == "InService":
                return
            elif status == "Failed":
                raise RuntimeError(f"Endpoint deployment failed: {response.get('FailureReason')}")

            time.sleep(30)

        raise TimeoutError(f"Endpoint deployment timed out after {timeout}s")

    def delete_endpoint(self, endpoint_name: str) -> None:
        """Delete an inference endpoint."""
        logger.info(f"Deleting endpoint: {endpoint_name}")

        # Delete endpoint
        self.sm_client.delete_endpoint(EndpointName=endpoint_name)

        # Delete endpoint config
        self.sm_client.delete_endpoint_config(EndpointConfigName=endpoint_name)

        logger.info(f"Endpoint deleted: {endpoint_name}")

        if endpoint_name in self.endpoints:
            del self.endpoints[endpoint_name]

    def _generate_endpoint_name(self, model_name: str) -> str:
        """Generate a unique endpoint name."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{model_name}-endpoint-{timestamp}"

    def list_endpoints(self) -> list:
        """List all SageMaker endpoints."""
        response = self.sm_client.list_endpoints()
        return response.get("Endpoints", [])


class InferenceEndpoint:
    """Wrapper for interacting with a SageMaker inference endpoint."""

    def __init__(self, endpoint_name: str, model_name: str, sm_client):
        self.endpoint_name = endpoint_name
        self.model_name = model_name
        self.sm_client = sm_client
        self.runtime_client = boto3.client("sagemaker-runtime")

    def predict(self, features) -> List[float]:
        """
        Generate predictions using the endpoint.

        Args:
            features: numpy array or list of shape (n_samples, n_features)

        Returns:
            predictions: List of predictions
        """
        if isinstance(features, np.ndarray):
            features = features.tolist()

        # Serialize input
        body = json.dumps(features)

        logger.info(f"Making prediction on {self.endpoint_name}")

        # Invoke endpoint
        response = self.runtime_client.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType="application/json",
            Body=body,
        )

        # Parse response
        result = json.loads(response["Body"].read().decode())
        return result

    def delete(self) -> None:
        """Delete this endpoint."""
        controller = InferenceController()
        controller.delete_endpoint(self.endpoint_name)

    def __repr__(self) -> str:
        return f"InferenceEndpoint(name={self.endpoint_name}, model={self.model_name})"


if __name__ == "__main__":
    # Example usage
    controller = InferenceController()
    endpoint = controller.deploy(model_name="xgbregressor")
    print(f"Endpoint: {endpoint}")

    # Make predictions
    test_features = [[1.0, 2.0, 3.0]]
    predictions = endpoint.predict(test_features)
    print(f"Predictions: {predictions}")

    # Cleanup
    endpoint.delete()
