#!/usr/bin/env python3
"""
Test Lambda inference function.
"""

import os
import json
import boto3

def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║        Test Lambda Inference                              ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    bucket = os.getenv('S3_BUCKET')
    region = os.getenv('AWS_REGION')

    if not bucket:
        print("❌ S3_BUCKET not set")
        print("Run: source .env.local")
        return 1

    # Create test data
    print("\n" + "="*80)
    print("UPLOADING TEST DATA")
    print("="*80)

    test_csv = """MedInc,HouseAge,AveRooms,AveBedrms,Population,AveOccup,Latitude,Longitude
8.3252,41.0,6.984127,1.023810,322.0,2.555556,37.88,-122.23
7.2574,52.0,8.288136,1.081081,496.0,2.802260,37.85,-122.24
7.1736,52.0,6.289604,1.096386,413.0,2.063887,37.85,-122.24"""

    s3 = boto3.client('s3', region_name=region)
    s3.put_object(
        Bucket=bucket,
        Key='inference/test_input.csv',
        Body=test_csv
    )
    print(f"✓ Test data uploaded: s3://{bucket}/inference/test_input.csv")

    # Invoke Lambda
    print("\n" + "="*80)
    print("INVOKING LAMBDA")
    print("="*80)

    lambda_client = boto3.client('lambda', region_name=region)

    # Get model from S3
    response = s3.list_objects_v2(
        Bucket=bucket,
        Prefix='sagemaker-artifacts/models/xgbregressor/'
    )
    if 'Contents' not in response or not response['Contents']:
        print("❌ No model found in S3")
        return 1

    model_key = max(response['Contents'], key=lambda x: x['LastModified'])['Key']
    print(f"Using model: {model_key}")

    # Invoke
    print("\nInvoking Lambda function...")
    try:
        response = lambda_client.invoke(
            FunctionName='sagemaker-mlops-inference',
            Payload=json.dumps({
                'bucket': bucket,
                'input_key': 'inference/test_input.csv',
                'output_key': 'inference/test_predictions.csv',
                'model_bucket': bucket,
                'model_key': model_key
            })
        )
    except Exception as e:
        print(f"❌ Lambda invocation failed: {e}")
        print("\nMake sure you deployed with: python3 deploy_lambda.py")
        return 1

    # Parse response
    result = json.loads(response['Payload'].read())
    print(f"✓ Lambda response: {result}")

    if result.get('statusCode') != 200:
        print(f"❌ Lambda returned error: {result.get('body', 'Unknown error')}")
        return 1

    # Download predictions
    print("\n" + "="*80)
    print("INFERENCE RESULTS")
    print("="*80)

    try:
        obj = s3.get_object(Bucket=bucket, Key='inference/test_predictions.csv')
        predictions = obj['Body'].read().decode()
        print(f"\n✓ Predictions saved to S3:")
        print(f"  s3://{bucket}/inference/test_predictions.csv\n")
        print(predictions)
    except Exception as e:
        print(f"❌ Could not download predictions: {e}")
        return 1

    print("\n" + "="*80)
    print("✅ INFERENCE TEST COMPLETE!")
    print("="*80)
    return 0


if __name__ == "__main__":
    exit(main())
