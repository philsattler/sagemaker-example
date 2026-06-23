"""
Example: EC2 Batch Inference

Shows how to use the BatchInferenceEC2 class for batch predictions.
"""

from batch_on_ec2 import batch_inference_workflow
import pandas as pd

# Example data
data = pd.DataFrame({
    'feature1': [1, 2, 3],
    'feature2': [4, 5, 6]
})

# Run inference
results = batch_inference_workflow(data, model_s3_path='s3://my-bucket/model.tar.gz')
print(results)
