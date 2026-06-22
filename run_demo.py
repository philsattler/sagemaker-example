#!/usr/bin/env python3
"""
End-to-End SageMaker Pipeline Demo
- Train with Spot instances (70% cheaper)
- Register model
- Deploy via Lambda
- Test inference with results in S3
"""

import os
import sys
import json
import time
import boto3

# Add project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "1_sagemaker-mlops"))

from agent import TrainingAgent
from sagemaker_config import get_model_config


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def verify_setup():
    """Verify AWS setup is ready."""
    print_section("SETUP VERIFICATION")

    required_env = ["AWS_REGION", "AWS_ACCOUNT_ID", "S3_BUCKET", "SAGEMAKER_ROLE_ARN"]
    missing = [var for var in required_env if not os.getenv(var)]

    if missing:
        print(f"❌ Missing environment variables: {missing}")
        print("\nRun: source .env.local")
        return False

    # Verify S3 bucket
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    try:
        s3.head_bucket(Bucket=os.getenv("S3_BUCKET"))
        print(f"✓ S3 Bucket: {os.getenv('S3_BUCKET')}")
    except Exception as e:
        print(f"❌ S3 Bucket error: {e}")
        return False

    # Verify data exists in S3
    try:
        response = s3.head_object(
            Bucket=os.getenv("S3_BUCKET"),
            Key="data/train.csv"
        )
        size = response["ContentLength"]
        print(f"✓ Training data: s3://{os.getenv('S3_BUCKET')}/data/train.csv ({size} bytes)")
    except Exception as e:
        print(f"❌ Training data not found in S3: {e}")
        return False

    # Verify IAM role
    iam = boto3.client("iam")
    try:
        role_name = os.getenv("SAGEMAKER_ROLE_ARN").split("/")[-1]
        iam.get_role(RoleName=role_name)
        print(f"✓ IAM Role: {role_name}")
    except Exception as e:
        print(f"❌ IAM Role error: {e}")
        return False

    print("\n✅ All setup verified!")
    return True


def build_docker_image():
    """Build and push Docker image to ECR."""
    print_section("BUILD DOCKER IMAGE")

    account_id = os.getenv("AWS_ACCOUNT_ID")
    region = os.getenv("AWS_REGION")
    repo_name = os.getenv("ECR_REPO_NAME", "sagemaker-mlops")

    ecr_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{repo_name}"

    print(f"Building Docker image for ECR: {ecr_uri}")
    print("\nNote: You need Docker running locally. If Docker is not available,")
    print("skip this step and use a pre-built image URI.")

    # Check if docker is available
    import subprocess
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        print("✓ Docker is available")

        print("\nManual steps to push image:")
        print(f"  aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account_id}.dkr.ecr.{region}.amazonaws.com")
        print(f"  docker build -t {repo_name}:latest .")
        print(f"  docker tag {repo_name}:latest {ecr_uri}:latest")
        print(f"  docker push {ecr_uri}:latest")
        print("\nFor now, continuing with 'latest' tag...")

    except FileNotFoundError:
        print("⚠️  Docker not available (expected in some environments)")
        print("You can build locally and push, or use existing image")

    return True


def train_model():
    """Train the XGBoost model using Spot instances."""
    print_section("TRAINING WITH SPOT INSTANCES")

    try:
        agent = TrainingAgent(
            role_arn=os.getenv("SAGEMAKER_ROLE_ARN"),
            region=os.getenv("AWS_REGION")
        )

        config = get_model_config("xgbregressor")

        print(f"Configuration:")
        print(f"  Model: xgbregressor")
        print(f"  Instance: {config.training_instance_type} (Spot: {config.use_spot})")
        print(f"  Cost savings: 70% with Spot instances")
        print(f"  Data: s3://{os.getenv('S3_BUCKET')}/data/train.csv")
        print(f"\nStarting training job...")

        job_name = agent.train(
            model_name="xgbregressor",
            image_tag="latest",
            wait=True
        )

        print(f"\n✅ Training completed!")
        print(f"   Job name: {job_name}")

        # Get model details
        sm = boto3.client("sagemaker", region_name=os.getenv("AWS_REGION"))
        response = sm.describe_training_job(TrainingJobName=job_name)

        model_uri = response["ModelArtifacts"]["S3ModelArtifacts"]
        print(f"   Model location: {model_uri}")

        # Get job duration
        start = response["CreationTime"]
        end = response["TrainingEndTime"]
        duration_minutes = (end - start).total_seconds() / 60
        print(f"   Duration: {duration_minutes:.1f} minutes")

        return job_name, model_uri

    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def deploy_lambda_inference(model_uri):
    """Deploy model to Lambda for serverless inference."""
    print_section("DEPLOY LAMBDA INFERENCE")

    print(f"Model location: {model_uri}")
    print("\nLambda deployment requires:")
    print("  1. Update MODEL_BUCKET and MODEL_KEY in batch/lambda_handler.py")
    print("  2. Deploy with Serverless Framework or AWS CLI")
    print("\nManual steps:")
    print(f"  # Extract bucket and key from model URI")
    print(f"  # Update 1_sagemaker-mlops/batch/lambda_handler.py")
    print(f"  # serverless deploy --verbose")

    # Parse model URI
    try:
        parts = model_uri.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]
        print(f"\nModel details for Lambda:")
        print(f"  Bucket: {bucket}")
        print(f"  Key: {key}")
    except:
        pass

    return True


def test_inference():
    """Create test data for inference."""
    print_section("TEST DATA FOR INFERENCE")

    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    bucket = os.getenv("S3_BUCKET")

    # Create test CSV
    test_csv = """MedInc,HouseAge,AveRooms,AveBedrms,Population,AveOccup,Latitude,Longitude
8.3252,41.0,6.984127,1.023810,322.0,2.555556,37.88,-122.23
7.2574,52.0,8.288136,1.081081,496.0,2.802260,37.85,-122.24
7.1736,52.0,6.289604,1.096386,413.0,2.063887,37.85,-122.24"""

    # Upload test data
    try:
        s3.put_object(
            Bucket=bucket,
            Key="inference/test_input.csv",
            Body=test_csv
        )
        print(f"✓ Test data uploaded: s3://{bucket}/inference/test_input.csv")
        print("\nTest data:")
        print(test_csv)

        print("\n\nOnce Lambda is deployed, test with:")
        print(f"""
python3 << 'EOF'
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-1')

response = lambda_client.invoke(
    FunctionName='sagemaker-mlops-inference',
    Payload=json.dumps({{
        'bucket': '{bucket}',
        'input_key': 'inference/test_input.csv',
        'output_key': 'inference/predictions.csv',
        'model_bucket': '{bucket}',
        'model_key': 'sagemaker-artifacts/models/...'  # Update with actual model
    }})
)

result = json.loads(response['Payload'].read())
print("Inference result:", result)

# Check output in S3
s3 = boto3.client('s3')
obj = s3.get_object(Bucket='{bucket}', Key='inference/predictions.csv')
print("\\nPredictions:")
print(obj['Body'].read().decode())
EOF
        """)

    except Exception as e:
        print(f"❌ Failed to upload test data: {e}")

    return True


def cost_summary():
    """Show cost breakdown."""
    print_section("COST SUMMARY")

    print("""
Component                Cost    Notes
─────────────────────────────────────────────────────────
Training (Spot)          $0.10   1h × ml.m5.large Spot (70% off)
Training Data (S3)       <$0.01  ~1KB dataset
Model Storage (S3)       <$0.01  ~1MB model
Lambda Invocations       ~$0.20  1000 calls × 5 sec × 3GB
─────────────────────────────────────────────────────────
TOTAL                    ~$0.32  vs $70/month for real-time endpoint!

Savings with Spot instances:
- On-demand: 1h × ml.m5.large = $0.096/hour
- Spot: 1h × ml.m5.large = $0.029/hour
- Savings: 70%
    """)


def main():
    """Run the full demo pipeline."""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   SageMaker MLOps End-to-End Pipeline Demo                ║
    ║   Spot Training + Lambda Serverless Inference             ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    # Step 1: Verify setup
    if not verify_setup():
        print("\n❌ Setup incomplete. Run: source .env.local")
        return

    # Step 2: Build image (optional)
    user_input = input("\nBuild Docker image? (y/n): ").strip().lower()
    if user_input == "y":
        build_docker_image()

    # Step 3: Train model
    user_input = input("\nStart training job? (y/n): ").strip().lower()
    if user_input == "y":
        job_name, model_uri = train_model()

        if job_name:
            # Step 4: Deploy Lambda
            deploy_lambda_inference(model_uri)

            # Step 5: Test inference
            user_input = input("\nCreate test inference data? (y/n): ").strip().lower()
            if user_input == "y":
                test_inference()

    # Show cost summary
    cost_summary()

    print("\n" + "="*80)
    print("📚 Next steps:")
    print("  1. Deploy Lambda with your model")
    print("  2. Test inference with sample data")
    print("  3. Check CloudWatch logs for metrics")
    print("  4. Review .interview-prep.md for deeper learning")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Ensure env vars are loaded
    if not os.getenv("S3_BUCKET"):
        print("⚠️  Environment variables not set")
        print("Run: source .env.local")
        sys.exit(1)

    main()
