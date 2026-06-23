"""
Serverless batch inference using AWS Lambda.

For infrequent batch jobs (daily, weekly, or one-off).
- No endpoint spinup time (cold start only: 5-10 sec)
- Pay only for compute (cheap for small-medium batches)
- Zero operational overhead (no cleanup needed)

Usage:
    Invoke via AWS CLI:
        aws lambda invoke --function-name batch-inference \\
            --payload '{"bucket": "my-bucket", "input_key": "data.csv"}' \\
            response.json

    Or via boto3:
        import boto3
        client = boto3.client('lambda')
        response = client.invoke(
            FunctionName='batch-inference',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'bucket': 'my-bucket',
                'input_key': 'data/batch.csv',
                'output_key': 'results/batch_predictions.csv'
            })
        )
"""

import json
import io
import logging
import pickle
import boto3
import numpy as np
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

# Model is loaded once at Lambda container startup (reused across invocations)
MODEL = None
MODEL_TYPE = None  # 'xgboost' or 'lightgbm'
MODEL_BUCKET = "sagemaker-mlops-495811053995"
MODEL_KEY = "sagemaker-artifacts/models/xgbregressor/local-20260623120000.tar.gz"  # Paste YOUR key here


def load_model(bucket: str, model_key: str) -> tuple:
    """Load model from S3 (cached in Lambda container)."""
    global MODEL, MODEL_TYPE

    if MODEL is not None:
        logger.info("Using cached model")
        return MODEL, MODEL_TYPE

    logger.info(f"Loading model from s3://{bucket}/{model_key}")

    # Download model from S3
    obj = s3_client.get_object(Bucket=bucket, Key=model_key)
    model_bytes = obj['Body'].read()

    # Load based on file extension
    if model_key.endswith('.pkl'):
        MODEL = pickle.loads(model_bytes)
        # Infer model type from pickle (would be set during training)
        model_class = type(MODEL).__name__
        if 'XGBRegressor' in model_class or 'XGBClassifier' in model_class:
            MODEL_TYPE = 'xgboost'
        elif 'LGBMRegressor' in model_class or 'LGBMClassifier' in model_class:
            MODEL_TYPE = 'lightgbm'
        else:
            MODEL_TYPE = 'unknown'
    else:
        raise ValueError(f"Unsupported model format: {model_key}")

    logger.info(f"Model loaded. Type: {MODEL_TYPE}")
    return MODEL, MODEL_TYPE


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for batch inference.

    Expected event structure:
    {
        "bucket": "my-bucket",           # S3 bucket with input data
        "input_key": "data/batch.csv",   # CSV file to predict on
        "output_key": "results/predictions.csv",  # Where to save results
        "model_bucket": "my-bucket",     # Bucket with model (optional)
        "model_key": "models/xgb_model.pkl"  # Model file (optional)
    }
    """
    try:
        logger.info(f"Received event: {event}")

        # Parse input
        bucket = event.get('bucket')
        input_key = event.get('input_key')
        output_key = event.get('output_key', f"results/{input_key.split('/')[-1]}")
        model_bucket = event.get('model_bucket', bucket)
        model_key = event.get('model_key', 'models/model.pkl')

        if not bucket or not input_key:
            raise ValueError("Missing required parameters: bucket, input_key")

        # Load model
        model, model_type = load_model(model_bucket, model_key)

        # Load input data from S3
        logger.info(f"Reading input from s3://{bucket}/{input_key}")
        obj = s3_client.get_object(Bucket=bucket, Key=input_key)
        df = pd.read_csv(io.BytesIO(obj['Body'].read()))

        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

        # Prepare features for inference
        # Assumes CSV has feature columns (exclude target if present)
        exclude_cols = ['target', 'label', 'y']
        feature_cols = [col for col in df.columns if col.lower() not in exclude_cols]

        X = df[feature_cols].values
        logger.info(f"Running inference on {X.shape[0]} samples, {X.shape[1]} features")

        # Run inference
        if model_type == 'xgboost':
            import xgboost as xgb
            # XGBoost handles numpy arrays directly
            predictions = model.predict(X)
        elif model_type == 'lightgbm':
            # LightGBM also handles numpy arrays
            predictions = model.predict(X)
        else:
            # Generic sklearn-like interface
            predictions = model.predict(X)

        logger.info(f"Predictions shape: {predictions.shape}")

        # Add predictions to dataframe
        df['prediction'] = predictions

        # Save results to S3
        logger.info(f"Saving results to s3://{bucket}/{output_key}")
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)

        s3_client.put_object(
            Bucket=bucket,
            Key=output_key,
            Body=csv_buffer.getvalue(),
            ContentType='text/csv'
        )

        # Return success
        result = {
            'statusCode': 200,
            'rows_processed': len(df),
            'output_location': f"s3://{bucket}/{output_key}",
            'model_used': model_type,
            'features_used': feature_cols
        }

        logger.info(f"Success: {result}")
        return result

    except Exception as e:
        logger.error(f"Error during inference: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'error': str(e)
        }


# Local testing
if __name__ == '__main__':
    # Test event
    test_event = {
        'bucket': 'my-bucket',
        'input_key': 'data/test_batch.csv',
        'output_key': 'results/test_predictions.csv',
        'model_bucket': 'my-bucket',
        'model_key': 'models/xgb_model.pkl'
    }

    class MockContext:
        def __init__(self):
            self.aws_request_id = 'test-request-id'
            self.invoked_function_arn = 'test-arn'

    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))
