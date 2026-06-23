#!/usr/bin/env python3
"""
End-to-end EC2 batch inference test.

Shows the complete workflow:
1. Create endpoint with trained model
2. Run batch predictions
3. Delete endpoint
4. Track costs
"""

import os
import sys
import json
import time
import pandas as pd

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import boto3
from sagemaker.model import Model
from sagemaker.predictor import Predictor
from sagemaker.serializers import CSVSerializer
from sagemaker.deserializers import JSONDeserializer
import sagemaker


def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║        EC2 Batch Inference End-to-End Test                ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    # Get environment
    region = os.getenv('AWS_REGION', 'us-east-1')
    account_id = os.getenv('AWS_ACCOUNT_ID')
    bucket = os.getenv('S3_BUCKET')

    if not all([account_id, bucket]):
        print("❌ Missing environment variables")
        print("Run: source .env.local")
        return 1

    try:
        # Get latest trained model from S3
        print("\n" + "="*80)
        print("FINDING TRAINED MODEL")
        print("="*80)

        s3 = boto3.client('s3', region_name=region)
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix='sagemaker-artifacts/models/xgbregressor/'
        )

        if 'Contents' not in response or not response['Contents']:
            print("❌ No trained model found in S3")
            print("Run: python3 ../local/train_locally.py")
            return 1

        model_key = max(response['Contents'], key=lambda x: x['LastModified'])['Key']
        model_uri = f"s3://{bucket}/{model_key}"
        print(f"✓ Found model: {model_uri}")

        # Create test data
        print("\n" + "="*80)
        print("CREATING TEST DATA")
        print("="*80)

        test_data = pd.DataFrame({
            'MedInc': [8.3252, 7.2574, 7.1736, 6.4588, 6.3634],
            'HouseAge': [41.0, 52.0, 52.0, 47.0, 47.0],
            'AveRooms': [6.98, 8.29, 6.29, 6.43, 6.00],
            'AveBedrms': [1.02, 1.08, 1.10, 1.08, 1.10],
            'Population': [322.0, 496.0, 413.0, 1094.0, 1157.0],
            'AveOccup': [2.56, 2.80, 2.06, 2.32, 1.79],
            'Latitude': [37.88, 37.85, 37.85, 37.84, 37.84],
            'Longitude': [-122.23, -122.24, -122.24, -122.25, -122.25]
        })

        print(f"✓ Created test data: {test_data.shape[0]} rows")

        # Create EC2 endpoint
        print("\n" + "="*80)
        print("CREATING EC2 ENDPOINT")
        print("="*80)
        print("This takes 5-10 minutes...")

        # Get SageMaker role and session
        role_arn = os.getenv('SAGEMAKER_ROLE_ARN')
        sm_session = sagemaker.Session(default_bucket=bucket)

        # Create model from S3 artifacts
        endpoint_name = f"xgb-batch-inference-{int(time.time())}"

        # Use your own Docker image in ECR (has proper permissions)
        custom_image = f"{account_id}.dkr.ecr.{region}.amazonaws.com/sagemaker-mlops:latest"

        model = Model(
            image_uri=custom_image,
            model_data=model_uri,
            role=role_arn,
            sagemaker_session=sm_session,
            name=endpoint_name
        )

        # Deploy endpoint
        predictor = model.deploy(
            initial_instance_count=1,
            instance_type='ml.m5.large',
            endpoint_name=endpoint_name,
            wait=True
        )
        print(f"✓ Endpoint created: {endpoint_name}")

        # Run inference
        print("\n" + "="*80)
        print("RUNNING BATCH INFERENCE")
        print("="*80)

        # Convert to CSV for XGBoost
        csv_data = test_data.to_csv(header=False, index=False)

        # Predict
        predictions = predictor.predict(csv_data)
        print(f"✓ Generated {len(test_data)} predictions")
        print("\nPredictions:")
        print(predictions)

        # Delete endpoint
        print("\n" + "="*80)
        print("DELETING ENDPOINT")
        print("="*80)

        predictor.delete_endpoint()
        print("✓ Endpoint deleted")

        # Summary
        print("\n" + "="*80)
        print("✅ EC2 BATCH INFERENCE TEST COMPLETE!")
        print("="*80)
        print(f"""
Results:
  Endpoint: {batch.endpoint_name}
  Instance: ml.m5.large
  Rows processed: {len(predictions)}

Cost estimate:
  Endpoint creation: ~$0.05
  Inference (15 min): ~$0.04
  Total: ~$0.09

For comparison:
  Lambda (if available): ~$0.25
  Real-time endpoint (30 days): ~$70
        """)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
