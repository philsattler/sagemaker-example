#!/usr/bin/env python3
"""
Auto-deploy Lambda inference function.
No manual YAML editing needed.
"""

import os
import sys
import subprocess
import json

def get_latest_model_from_s3():
    """Get the latest trained model from S3."""
    import boto3

    s3 = boto3.client('s3')
    bucket = os.getenv('S3_BUCKET')
    prefix = 'sagemaker-artifacts/models/xgbregressor/'

    print(f"\nSearching for models in s3://{bucket}/{prefix}...")

    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    if 'Contents' not in response or not response['Contents']:
        print(f"❌ No models found in S3")
        return None

    # Get latest (most recent)
    latest = max(response['Contents'], key=lambda x: x['LastModified'])
    model_key = latest['Key']

    print(f"✓ Found model: {model_key}")
    return model_key


def update_serverless_yml(model_key):
    """Update serverless.yml with model path."""
    yml_path = 'serverless.yml'

    # Read current YAML
    with open(yml_path, 'r') as f:
        content = f.read()

    # Find and replace MODEL_KEY line
    import re
    pattern = r"MODEL_KEY:.*"
    replacement = f"MODEL_KEY: {model_key}"

    new_content = re.sub(pattern, replacement, content)

    # Write back
    with open(yml_path, 'w') as f:
        f.write(new_content)

    print(f"✓ Updated serverless.yml with model: {model_key}")


def deploy_lambda():
    """Deploy Lambda function."""
    print("\n" + "="*80)
    print("DEPLOYING TO LAMBDA")
    print("="*80)

    # Check if serverless is installed
    try:
        result = subprocess.run(['serverless', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Serverless Framework not installed")
            print("\nInstall with:")
            print("  npm install -g serverless")
            return False
    except FileNotFoundError:
        print("❌ Serverless Framework not installed")
        print("\nInstall with:")
        print("  npm install -g serverless")
        return False

    print(f"✓ Serverless version: {result.stdout.strip()}")

    # Deploy
    print("\nDeploying Lambda function...")
    result = subprocess.run(['serverless', 'deploy', '--verbose'], capture_output=True, text=True)

    if result.returncode == 0:
        print("✓ Deployment successful!")
        print(result.stdout)
        return True
    else:
        print("❌ Deployment failed!")
        print(result.stderr)
        return False


def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║        Deploy Lambda Inference (Auto-configured)          ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    # Verify setup
    if not os.getenv('S3_BUCKET'):
        print("❌ S3_BUCKET not set")
        print("Run: source .env.local")
        return 1

    try:
        # Get model
        model_key = get_latest_model_from_s3()
        if not model_key:
            return 1

        # Update config
        update_serverless_yml(model_key)

        # Deploy
        if not deploy_lambda():
            return 1

        print("\n" + "="*80)
        print("✅ LAMBDA DEPLOYED!")
        print("="*80)
        print(f"""
Your Lambda function is ready to test:
  Function name: sagemaker-mlops-inference
  Model: {model_key}
  Region: {os.getenv('AWS_REGION')}

Next: Test inference with
  python3 test_lambda_inference.py
        """)

        return 0

    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
