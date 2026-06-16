"""
Example: How to use Lambda vs EC2 batch inference.

Shows both approaches with timing and cost comparisons.
"""

import boto3
import json
import pandas as pd
import numpy as np
from batch_on_ec2 import BatchInferenceEC2


def example_lambda_batch():
    """Example: Run batch inference via Lambda."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Lambda Batch Inference")
    print("="*80)

    client = boto3.client('lambda')

    # Assume you have sample data in S3
    event = {
        'bucket': 'my-sagemaker-bucket',
        'input_key': 'data/weekly_batch.csv',
        'output_key': 'results/weekly_predictions.csv',
        'model_bucket': 'my-sagemaker-bucket',
        'model_key': 'models/xgb_model.pkl'
    }

    print("\n📤 Invoking Lambda function...")
    print(f"   Input: s3://{event['bucket']}/{event['input_key']}")
    print(f"   Output: s3://{event['bucket']}/{event['output_key']}")

    try:
        response = client.invoke(
            FunctionName='batch-inference-batch-inference',
            InvocationType='RequestResponse',  # Wait for completion
            Payload=json.dumps(event)
        )

        # Read response
        result = json.loads(response['Payload'].read())

        if response['StatusCode'] == 200:
            print("\n✅ Success!")
            print(f"   Rows processed: {result.get('rows_processed', 'N/A')}")
            print(f"   Output: {result.get('output_location', 'N/A')}")
            print(f"   Model used: {result.get('model_used', 'N/A')}")
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"\n❌ Failed to invoke Lambda: {str(e)}")
        print("   Make sure:")
        print("   - Lambda function is deployed: serverless deploy")
        print("   - S3 bucket exists and has the input data")
        print("   - AWS credentials are configured")


def example_ec2_batch():
    """Example: Run batch inference via EC2 endpoint."""
    print("\n" + "="*80)
    print("EXAMPLE 2: EC2 Batch Inference")
    print("="*80)

    print("\n⚠️  This example shows the workflow structure.")
    print("   To actually run it, you need:")
    print("   - A trained model in SageMaker Model Registry")
    print("   - Input data as CSV")
    print("")

    # Example workflow (won't run without setup)
    example_code = '''
    from batch_on_ec2 import batch_inference_workflow

    # Run complete workflow: create endpoint → infer → delete
    results = batch_inference_workflow(
        input_csv='data/large_batch.csv',
        output_csv='results/predictions.csv',
        model_name='xgb-model',
        instance_type='ml.m5.large'
    )

    print(f"Processed: {results['input_rows']} rows")
    print(f"Total time: {results['timing']['total_sec']:.0f} sec")
    print(f"Cost: ${results['cost_estimate']['estimated_cost']:.2f}")
    '''

    print("Code:")
    print(example_code)

    # Show what the output would look like
    print("\nExpected output structure:")
    expected_output = {
        'input_rows': 10000,
        'predictions': 10000,
        'endpoint_name': 'batch-inference-1716854400',
        'timing': {
            'endpoint_creation_sec': 540,
            'inference_sec': 180,
            'endpoint_deletion_sec': 60,
            'total_sec': 780
        },
        'cost_estimate': {
            'instance_type': 'ml.m5.large',
            'hourly_rate': 0.096,
            'total_hours': 0.217,
            'estimated_cost': 0.02
        }
    }
    print(json.dumps(expected_output, indent=2))


def example_manual_ec2_control():
    """Example: Manual control over EC2 endpoint lifecycle."""
    print("\n" + "="*80)
    print("EXAMPLE 3: EC2 Manual Control (Advanced)")
    print("="*80)

    print("\nUse this when you want to:")
    print("- Create endpoint once, run multiple batches")
    print("- Fine-tune instance types or counts")
    print("- Monitor each step independently")

    code = '''
    from batch_on_ec2 import BatchInferenceEC2
    import pandas as pd

    # Create batch processor
    batch = BatchInferenceEC2(
        model_name='xgb-model',
        instance_type='ml.m5.xlarge',
        instance_count=2  # Multi-instance for parallelism
    )

    print("🚀 Creating endpoint (5-10 minutes)...")
    batch.create_endpoint(wait=True)

    # Run multiple batches before deleting
    for batch_file in ['batch_1.csv', 'batch_2.csv', 'batch_3.csv']:
        print(f"📊 Processing {batch_file}...")
        df = pd.read_csv(batch_file)

        predictions = batch.batch_predict(
            df,
            batch_size=5000,  # Tune for your data
            feature_cols=['feature1', 'feature2', 'feature3']
        )

        df['prediction'] = predictions
        df.to_csv(f"results/{batch_file}", index=False)

    # Clean up after all batches
    print("🗑️ Deleting endpoint...")
    batch.delete_endpoint(wait=True)
    '''

    print("Code:")
    print(code)


def cost_comparison():
    """Show cost comparison between Lambda and EC2."""
    print("\n" + "="*80)
    print("COST COMPARISON")
    print("="*80)

    # Lambda costs
    lambda_cost_per_gb_sec = 0.0001667

    # EC2 costs
    instance_costs = {
        'ml.m5.large': 0.096,
        'ml.m5.xlarge': 0.192,
        'ml.m5.2xlarge': 0.384,
    }

    scenarios = [
        {'size_gb': 1, 'inference_min': 1},
        {'size_gb': 10, 'inference_min': 5},
        {'size_gb': 50, 'inference_min': 15},
        {'size_gb': 100, 'inference_min': 30},
    ]

    print("\n{:<15} {:<20} {:<20} {:<15}".format(
        "Batch Size", "Lambda Cost", "EC2 Cost (m5.large)", "Winner"
    ))
    print("-" * 75)

    for scenario in scenarios:
        size_gb = scenario['size_gb']
        infer_min = scenario['inference_min']

        # Lambda cost
        lambda_cost = size_gb * infer_min * 60 * lambda_cost_per_gb_sec

        # EC2 cost (endpoint + inference + deletion)
        endpoint_creation_min = 10
        deletion_min = 2
        total_min = endpoint_creation_min + infer_min + deletion_min
        total_hours = total_min / 60
        ec2_cost = total_hours * instance_costs['ml.m5.large']

        winner = "Lambda" if lambda_cost < ec2_cost else "EC2"

        print("{:<15} ${:<19.2f} ${:<19.2f} {}".format(
            f"{size_gb}GB", lambda_cost, ec2_cost, winner
        ))

    print("\n💡 Key insights:")
    print("   - Lambda: Cheap for small batches, expensive for large")
    print("   - EC2: Expensive startup, but better for 50GB+")
    print("   - Break-even: ~30GB batch with 15 min inference")


if __name__ == '__main__':
    print("\n" + "🎓 BATCH INFERENCE EXAMPLES" + "\n")

    # Run examples
    example_lambda_batch()
    example_ec2_batch()
    example_manual_ec2_control()
    cost_comparison()

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. Lambda (recommended for most cases):")
    print("   $ cd batch && serverless deploy")
    print("   $ serverless invoke -f batch-inference -d '{...}'")
    print("\n2. EC2 (for large batches):")
    print("   $ python -c 'from batch_on_ec2 import batch_inference_workflow; ...'")
    print("\n3. Read batch/README.md for detailed docs and decision guidance")
