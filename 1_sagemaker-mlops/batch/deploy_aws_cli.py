#!/usr/bin/env python3
"""
Deploy Lambda using AWS CLI (no serverless framework needed).
Simpler and more direct than serverless.
"""

import os
import sys
import subprocess
import zipfile
import tempfile
import json


def create_lambda_zip(zip_path):
    """Create deployment zip with lambda_handler.py and dependencies."""
    print("\nCreating deployment package...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    handler_file = os.path.join(script_dir, 'lambda_handler.py')
    requirements_file = os.path.join(script_dir, 'lambda_requirements.txt')

    if not os.path.exists(handler_file):
        print(f"❌ lambda_handler.py not found at {handler_file}")
        return False

    if not os.path.exists(requirements_file):
        print(f"⚠️  lambda_requirements.txt not found, creating zip with handler only")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(handler_file, arcname='lambda_handler.py')
    else:
        # Install dependencies to temp directory
        import subprocess
        deps_dir = tempfile.mkdtemp(prefix='lambda_deps_')

        print("  Installing dependencies...")
        # Try uv first (modern), fall back to pip
        try:
            result = subprocess.run(
                ['uv', 'pip', 'install', '-r', requirements_file, '-t', deps_dir],
                capture_output=True,
                text=True,
                timeout=120
            )
        except FileNotFoundError:
            # Fall back to pip if uv not found
            result = subprocess.run(
                ['pip', 'install', '-r', requirements_file, '-t', deps_dir],
                capture_output=True,
                text=True,
                timeout=120
            )

        if result.returncode != 0:
            print(f"⚠️  Some dependencies failed to install (non-critical)")

        # Create zip with dependencies + handler
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add all dependencies
            for root, dirs, files in os.walk(deps_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, deps_dir)
                    zf.write(file_path, arcname=arcname)

            # Add handler
            zf.write(handler_file, arcname='lambda_handler.py')

        # Cleanup
        import shutil
        shutil.rmtree(deps_dir)

    size_kb = os.path.getsize(zip_path) / 1024
    print(f"✓ Created zip: {zip_path} ({size_kb:.1f} KB)")
    return True


def create_iam_role(role_name, account_id):
    """Create IAM role for Lambda if it doesn't exist."""
    print(f"\nChecking IAM role: {role_name}")

    iam = __import__('boto3').client('iam')

    try:
        iam.get_role(RoleName=role_name)
        print(f"✓ Role already exists")
        return True
    except iam.exceptions.NoSuchEntityException:
        print(f"Creating role...")

        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        try:
            iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for Lambda inference"
            )
            print(f"✓ Created role")

            # Attach S3 policy
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName='lambda-s3-access',
                PolicyDocument=json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "s3:GetObject",
                                "s3:PutObject"
                            ],
                            "Resource": "arn:aws:s3:::*/*"
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"
                            ],
                            "Resource": "arn:aws:logs:*:*:*"
                        }
                    ]
                })
            )
            print(f"✓ Attached S3 and CloudWatch permissions")

            return True
        except Exception as e:
            print(f"❌ Failed to create role: {e}")
            return False


def deploy_lambda(function_name, zip_path, role_arn, region, model_key, bucket):
    """Deploy Lambda function using AWS CLI."""
    print(f"\nDeploying Lambda function: {function_name}")

    import boto3
    lambda_client = boto3.client('lambda', region_name=region)

    # Read zip file
    with open(zip_path, 'rb') as f:
        zip_content = f.read()

    # Check if function exists
    try:
        lambda_client.get_function(FunctionName=function_name)
        print(f"Function exists, updating...")

        # Update function code
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print(f"✓ Updated function code")

        # Update environment variables
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                'Variables': {
                    'MODEL_BUCKET': bucket,
                    'MODEL_KEY': model_key,
                    'S3_BUCKET': bucket
                }
            }
        )
        print(f"✓ Updated environment variables")

    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"Function doesn't exist, creating...")

        # Create function
        lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler='lambda_handler.lambda_handler',
            Code={'ZipFile': zip_content},
            Timeout=900,
            MemorySize=3008,
            Environment={
                'Variables': {
                    'MODEL_BUCKET': bucket,
                    'MODEL_KEY': model_key,
                    'S3_BUCKET': bucket
                }
            },
            Description='Batch inference for ML models'
        )
        print(f"✓ Created Lambda function")

    return True


def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║     Deploy Lambda with AWS CLI (No Serverless Needed)     ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    bucket = os.getenv('S3_BUCKET')
    region = os.getenv('AWS_REGION', 'us-east-1')
    account_id = os.getenv('AWS_ACCOUNT_ID')

    if not all([bucket, region, account_id]):
        print("❌ Missing environment variables")
        print("Run: source .env.local")
        return 1

    try:
        import boto3

        # Get latest model
        print(f"\nSearching for models in s3://{bucket}/sagemaker-artifacts/models/xgbregressor/...")
        s3 = boto3.client('s3')
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix='sagemaker-artifacts/models/xgbregressor/'
        )

        if 'Contents' not in response:
            print("❌ No models found in S3")
            return 1

        model_key = max(response['Contents'], key=lambda x: x['LastModified'])['Key']
        print(f"✓ Found model: {model_key}")

        # Create deployment zip
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            zip_path = tmp.name

        if not create_lambda_zip(zip_path):
            return 1

        # Create/update IAM role
        role_name = 'lambda-inference-role'
        if not create_iam_role(role_name, account_id):
            return 1

        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

        # Deploy function
        function_name = 'sagemaker-mlops-inference'
        if not deploy_lambda(function_name, zip_path, role_arn, region, model_key, bucket):
            return 1

        # Cleanup
        os.remove(zip_path)

        print("\n" + "="*80)
        print("✅ LAMBDA DEPLOYED!")
        print("="*80)
        print(f"""
Function: {function_name}
Region: {region}
Model: {model_key}

Test with:
  python3 test_inference.py
        """)

        return 0

    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
