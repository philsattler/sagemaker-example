"""
Batch inference using SageMaker EC2 endpoints.

For large batch jobs (100GB+) where endpoint spinup time is negligible
or when you run multiple batches before deleting the endpoint.

Workflow:
1. Create endpoint (5-10 minutes)
2. Run batch inference (2-30 minutes)
3. Delete endpoint (1-2 minutes)

Cost: Better than Lambda for VERY large batches (100GB+)
       Worse than Lambda for small-medium batches (< 50GB)

Usage:
    from batch_on_ec2 import BatchInferenceEC2

    batch = BatchInferenceEC2(
        model_name='xgb-model',
        instance_type='ml.m5.large',
        instance_count=1
    )

    # Create endpoint
    batch.create_endpoint()

    # Run inference
    predictions = batch.batch_predict(input_data)

    # Clean up
    batch.delete_endpoint()
"""

import logging
import time
import json
import io
import pickle
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np
import sagemaker
from sagemaker.estimator import Estimator
from sagemaker.model import Model
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Setup SageMaker session
session = sagemaker.Session()
role = sagemaker.get_execution_role()
region = session.boto_region_name


class BatchInferenceEC2:
    """
    Batch inference using EC2 endpoints.
    Create, use, and clean up endpoints for batch jobs.
    """

    def __init__(
        self,
        model_name: str,
        instance_type: str = 'ml.m5.large',
        instance_count: int = 1,
        endpoint_name_prefix: str = 'batch-inference'
    ):
        """
        Initialize batch inference.

        Args:
            model_name: Name of the model in SageMaker Model Registry
            instance_type: EC2 instance type (e.g., 'ml.m5.large')
            instance_count: Number of instances to launch
            endpoint_name_prefix: Prefix for auto-generated endpoint name
        """
        self.model_name = model_name
        self.instance_type = instance_type
        self.instance_count = instance_count
        self.endpoint_name_prefix = endpoint_name_prefix

        # Generate unique endpoint name
        timestamp = int(time.time())
        self.endpoint_name = f"{endpoint_name_prefix}-{timestamp}"

        self.predictor = None
        logger.info(f"Initialized BatchInferenceEC2: {self.endpoint_name}")

    def create_endpoint(self, wait: bool = True) -> str:
        """
        Create SageMaker endpoint for batch inference.

        Args:
            wait: If True, block until endpoint is in 'InService' state

        Returns:
            Endpoint name
        """
        logger.info(f"Creating endpoint: {self.endpoint_name}")
        logger.info(f"  Instance type: {self.instance_type}")
        logger.info(f"  Instance count: {self.instance_count}")
        logger.info("  ⏳ This takes 5-10 minutes...")

        try:
            # Get model from SageMaker Model Registry
            model = Model(
                image_uri=self._get_image_uri(),
                model_data=self._get_model_data(),
                role=role,
                name=self.model_name,
                sagemaker_session=session
            )

            # Deploy
            start_time = time.time()

            self.predictor = model.deploy(
                initial_instance_count=self.instance_count,
                instance_type=self.instance_type,
                endpoint_name=self.endpoint_name,
                wait=wait
            )

            elapsed = time.time() - start_time
            logger.info(f"✅ Endpoint created in {elapsed/60:.1f} minutes")

            return self.endpoint_name

        except ClientError as e:
            logger.error(f"Failed to create endpoint: {str(e)}")
            raise

    def batch_predict(
        self,
        input_data: pd.DataFrame,
        batch_size: int = 1000,
        feature_cols: Optional[list] = None
    ) -> np.ndarray:
        """
        Run batch inference on DataFrame.

        Args:
            input_data: DataFrame with feature columns
            batch_size: Number of rows to process per API call
            feature_cols: List of feature column names (if None, use all except 'target'/'label')

        Returns:
            Array of predictions
        """
        if self.predictor is None:
            raise ValueError("Endpoint not created. Call create_endpoint() first.")

        logger.info(f"Running batch inference on {len(input_data)} rows")

        # Determine feature columns
        if feature_cols is None:
            exclude_cols = {'target', 'label', 'y'}
            feature_cols = [col for col in input_data.columns if col.lower() not in exclude_cols]

        logger.info(f"Using {len(feature_cols)} features: {feature_cols[:5]}...")

        # Extract features
        X = input_data[feature_cols].values

        # Process in batches
        predictions = []
        num_batches = (len(X) + batch_size - 1) // batch_size

        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(X))

            batch_X = X[start_idx:end_idx]

            logger.info(f"Processing batch {i+1}/{num_batches} ({start_idx}-{end_idx})")

            # Convert to CSV format for endpoint
            batch_df = pd.DataFrame(batch_X, columns=feature_cols)
            csv_data = batch_df.to_csv(header=False, index=False)

            # Invoke endpoint
            try:
                response = self.predictor.predict(
                    csv_data,
                    initial_args={'ContentType': 'text/csv'}
                )

                # Parse predictions
                batch_preds = np.array(
                    json.loads(response)['predictions']
                ).flatten()
                predictions.extend(batch_preds)

            except Exception as e:
                logger.error(f"Inference failed for batch {i}: {str(e)}")
                raise

        logger.info(f"✅ Completed inference on {len(predictions)} predictions")
        return np.array(predictions)

    def delete_endpoint(self, wait: bool = True) -> None:
        """
        Delete the SageMaker endpoint.

        Args:
            wait: If True, block until endpoint is deleted
        """
        if self.predictor is None:
            logger.warning("No endpoint to delete")
            return

        logger.info(f"Deleting endpoint: {self.endpoint_name}")
        logger.info("  ⏳ This takes 1-2 minutes...")

        try:
            start_time = time.time()

            self.predictor.delete_endpoint(wait=wait)

            elapsed = time.time() - start_time
            logger.info(f"✅ Endpoint deleted in {elapsed/60:.1f} minutes")

        except ClientError as e:
            logger.error(f"Failed to delete endpoint: {str(e)}")
            raise

    def _get_image_uri(self) -> str:
        """Get ECR image URI for SageMaker inference."""
        # This would typically come from your ECR registry
        # Format: ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/sagemaker-mlops:latest
        raise NotImplementedError("Set your image URI in sagemaker_config.py")

    def _get_model_data(self) -> str:
        """Get S3 path to model artifact."""
        # This would typically come from SageMaker Model Registry
        # Format: s3://bucket/models/model.tar.gz
        raise NotImplementedError("Set your model S3 path in sagemaker_config.py")


def batch_inference_workflow(
    input_csv: str,
    output_csv: str,
    model_name: str = 'xgb-model',
    instance_type: str = 'ml.m5.large'
) -> Dict[str, Any]:
    """
    Complete batch inference workflow: create → infer → delete.

    Args:
        input_csv: Path to input CSV file
        output_csv: Path to save predictions
        model_name: Model name in SageMaker Registry
        instance_type: EC2 instance type

    Returns:
        Dictionary with results and timing
    """
    logger.info("=" * 80)
    logger.info("BATCH INFERENCE WORKFLOW (EC2)")
    logger.info("=" * 80)

    total_start = time.time()

    # Load data
    logger.info(f"\n1️⃣ Loading input data from {input_csv}")
    df = pd.read_csv(input_csv)
    logger.info(f"   Loaded {len(df)} rows, {len(df.columns)} columns")

    # Create batch inference object
    batch = BatchInferenceEC2(
        model_name=model_name,
        instance_type=instance_type,
        instance_count=1
    )

    try:
        # Create endpoint
        logger.info(f"\n2️⃣ Creating endpoint")
        create_start = time.time()
        batch.create_endpoint(wait=True)
        create_time = time.time() - create_start

        # Run inference
        logger.info(f"\n3️⃣ Running inference")
        infer_start = time.time()
        predictions = batch.batch_predict(df)
        infer_time = time.time() - infer_start

        # Save results
        logger.info(f"\n4️⃣ Saving results to {output_csv}")
        df['prediction'] = predictions
        df.to_csv(output_csv, index=False)
        logger.info(f"   Saved {len(df)} predictions")

    finally:
        # Delete endpoint
        logger.info(f"\n5️⃣ Cleaning up")
        delete_start = time.time()
        batch.delete_endpoint(wait=True)
        delete_time = time.time() - delete_start

    total_time = time.time() - total_start

    # Results
    results = {
        'input_rows': len(df),
        'predictions': len(predictions),
        'endpoint_name': batch.endpoint_name,
        'timing': {
            'endpoint_creation_sec': create_time,
            'inference_sec': infer_time,
            'endpoint_deletion_sec': delete_time,
            'total_sec': total_time
        },
        'cost_estimate': {
            'instance_type': instance_type,
            'hourly_rate': 0.096,  # m5.large rate (example)
            'total_hours': total_time / 3600,
            'estimated_cost': (total_time / 3600) * 0.096
        }
    }

    logger.info("\n" + "=" * 80)
    logger.info("RESULTS")
    logger.info("=" * 80)
    logger.info(json.dumps(results, indent=2))

    return results


if __name__ == '__main__':
    # Example usage
    results = batch_inference_workflow(
        input_csv='data/test_batch.csv',
        output_csv='results/batch_predictions.csv',
        model_name='xgb-model',
        instance_type='ml.m5.large'
    )
