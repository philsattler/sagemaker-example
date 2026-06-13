import os
from agent import TrainingAgent

# Verify environment is set
assert os.getenv("SAGEMAKER_ROLE_ARN"), "SAGEMAKER_ROLE_ARN not set"
assert os.getenv("S3_BUCKET"), "S3_BUCKET not set"

print("=" * 60)
print("Starting SageMaker Training Job")
print("=" * 60)
print(f"Account: {os.getenv('AWS_ACCOUNT_ID')}")
print(f"Bucket: {os.getenv('S3_BUCKET')}")
print(f"Role: {os.getenv('SAGEMAKER_ROLE_ARN')}")
print("=" * 60)

# Create training agent
agent = TrainingAgent()

# Start training
try:
    job_name = agent.train(
        model_name="xgbregressor",
        image_tag="latest",
        wait=False  # Don't wait; just submit the job
    )
    print(f"\n✅ Training job submitted: {job_name}")
    print(f"\nMonitor progress:")
    print(f"  AWS Console → SageMaker → Training jobs → {job_name}")
    print(f"\nOr check status with:")
    print(f"  aws sagemaker describe-training-job --training-job-name {job_name}")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
