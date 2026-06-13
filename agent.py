"""
Training Agent: Orchestrates SageMaker training jobs.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import boto3
from sagemaker.session import Session
from sagemaker.estimator import Estimator
from sagemaker.model import Model

from sagemaker_config import (
    get_model_config,
    get_training_image_uri,
    get_s3_model_path,
    AWS_REGION,
    SAGEMAKER_ROLE_ARN,
    S3_TRAINING_OUTPUT,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainingAgent:
    """Orchestrates model training on SageMaker."""

    def __init__(self, role_arn: Optional[str] = None, region: str = AWS_REGION):
        self.role_arn = role_arn or SAGEMAKER_ROLE_ARN
        self.region = region
        self.sagemaker_session = Session(default_bucket=None)
        self.sm_client = boto3.client("sagemaker", region_name=region)

        if not self.role_arn:
            raise ValueError("SAGEMAKER_ROLE_ARN not set. Set via environment or pass to __init__")

    def train(
        self,
        model_name: str,
        image_tag: str = "latest",
        hyperparameters: Optional[Dict[str, Any]] = None,
        wait: bool = True,
    ) -> str:
        """
        Start a SageMaker training job.

        Args:
            model_name: Name of model to train (must be in sagemaker_config.py)
            image_tag: ECR image tag (default: "latest")
            hyperparameters: Override default hyperparameters
            wait: Whether to wait for job completion

        Returns:
            job_name: Name of the training job
        """
        config = get_model_config(model_name)
        image_uri = get_training_image_uri(image_tag)

        # Prepare hyperparameters
        job_hyperparameters = {
            "model_name": model_name,
            "hyperparameters": json.dumps(config.hyperparameters)
        }
        if hyperparameters:
            job_hyperparameters["hyperparameters"] = json.dumps(hyperparameters)

        job_name = self._generate_job_name(model_name)

        logger.info(f"Starting training job: {job_name}")
        logger.info(f"Model: {model_name}, Instance: {config.instance_type}")
        logger.info(f"Image: {image_uri}")

        # Create estimator
        estimator = Estimator(
            image_uri=image_uri,
            role=self.role_arn,
            instance_count=config.instance_count,
            instance_type=config.instance_type,
            output_path=S3_TRAINING_OUTPUT,
            sagemaker_session=self.sagemaker_session,
            hyperparameters=job_hyperparameters,
        )

        # Start training
        estimator.fit(
            wait=wait,
            job_name=job_name,
        )

        logger.info(f"Training job submitted: {job_name}")

        if wait:
            logger.info(f"Training job completed: {job_name}")
            # Register model in Model Registry
            self._register_model(job_name, model_name)

        return job_name

    def _register_model(self, training_job_name: str, model_name: str) -> str:
        """Register trained model in SageMaker Model Registry."""
        logger.info(f"Registering model in Model Registry...")

        # Get training job details
        response = self.sm_client.describe_training_job(TrainingJobName=training_job_name)
        model_uri = response["ModelArtifacts"]["S3ModelArtifacts"]

        logger.info(f"Model URI: {model_uri}")

        # Create model
        model_obj = Model(
            image_uri=response["AlgorithmSpecification"]["TrainingImage"],
            model_data=model_uri,
            role=self.role_arn,
            sagemaker_session=self.sagemaker_session,
            name=f"{model_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        )

        model_obj.create()
        logger.info(f"Model registered: {model_obj.name}")

        return model_obj.name

    def _generate_job_name(self, model_name: str) -> str:
        """Generate a unique training job name."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{model_name}-training-{timestamp}"

    def describe_job(self, job_name: str) -> Dict[str, Any]:
        """Get details about a training job."""
        return self.sm_client.describe_training_job(TrainingJobName=job_name)

    def list_jobs(self, model_name: Optional[str] = None, max_results: int = 10) -> list:
        """List recent training jobs."""
        response = self.sm_client.list_training_jobs(
            MaxResults=max_results,
            SortOrder="Descending",
        )

        jobs = response.get("TrainingJobSummaries", [])

        if model_name:
            jobs = [j for j in jobs if model_name in j["TrainingJobName"]]

        return jobs

if __name__ == "__main__":
    # Example usage
    agent = TrainingAgent()
    job_name = agent.train(model_name="xgbregressor")
    print(f"Training job: {job_name}")
