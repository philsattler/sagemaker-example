#!/usr/bin/env python3
"""
Train XGBoost model locally and upload to S3.
Simulates SageMaker training without needing AWS quota.
Self-contained to avoid dask/lightgbm conflicts.
"""

import os
import sys
import json
import pickle
import tempfile
import tarfile
from datetime import datetime

import boto3
import pandas as pd
from sklearn.model_selection import train_test_split
import xgboost as xgb


def download_data_from_s3():
    """Download training data from S3."""
    print("\n" + "="*80)
    print("DOWNLOADING DATA FROM S3")
    print("="*80)

    s3 = boto3.client('s3')
    bucket = os.getenv('S3_BUCKET')

    csv_path = '/tmp/train.csv'
    s3.download_file(bucket, 'data/train.csv', csv_path)

    print(f"✓ Downloaded from s3://{bucket}/data/train.csv")
    return csv_path


def train_model_locally():
    """Train XGBoost model locally."""
    print("\n" + "="*80)
    print("TRAINING MODEL LOCALLY")
    print("="*80)

    # Download data
    csv_path = download_data_from_s3()

    # Load data
    print("\nLoading data...")
    df = pd.read_csv(csv_path)
    print(f"✓ Loaded {len(df)} rows × {len(df.columns)} columns")

    # Prepare features and target
    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values

    print(f"\nFeature matrix: {X.shape}")
    print(f"Target vector: {y.shape}")

    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Train set: {X_train.shape}")
    print(f"Val set: {X_val.shape}")

    # Train XGBoost
    print("\nTraining XGBoost...")
    model = xgb.XGBRegressor(
        n_estimators=50,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=5,
        verbose=0
    )
    print("✓ Training complete!")

    return model


def save_model_to_s3(model):
    """Save model to S3 as tar.gz (SageMaker format)."""
    print("\n" + "="*80)
    print("SAVING AND UPLOADING MODEL")
    print("="*80)

    s3 = boto3.client('s3')
    bucket = os.getenv('S3_BUCKET')

    with tempfile.TemporaryDirectory() as tmpdir:
        # Save model as pickle
        model_file = os.path.join(tmpdir, 'xgboost-model')
        model.get_booster().save_model(model_file)
        print(f"✓ Model saved locally")

        # Create tar.gz (SageMaker expects this format)
        tar_path = os.path.join(tmpdir, 'model.tar.gz')
        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(model_file, arcname='xgboost-model')

        file_size = os.path.getsize(tar_path) / 1024
        print(f"✓ Model packaged as tar.gz ({file_size:.1f} KB)")

        # Upload to S3
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        model_key = f"sagemaker-artifacts/models/xgbregressor/local-{timestamp}.tar.gz"

        print(f"\nUploading to S3...")
        s3.upload_file(tar_path, bucket, model_key)

        model_uri = f"s3://{bucket}/{model_key}"
        print(f"✓ Model uploaded!")
        print(f"  URI: {model_uri}")

        return model_uri, model_key


def save_model_info(model_uri, model_key):
    """Save model info for Lambda."""
    print("\n" + "="*80)
    print("MODEL INFORMATION")
    print("="*80)

    info = {
        'model_uri': model_uri,
        'model_key': model_key,
        'model_type': 'xgbregressor',
        'timestamp': datetime.now().isoformat(),
        'training_method': 'local',
        'framework': 'xgboost',
    }

    print(json.dumps(info, indent=2))
    return info


def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║        Local XGBoost Training + S3 Upload                 ║
    ║   (No AWS quota needed - trains on your machine)          ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    # Verify setup
    if not os.getenv('S3_BUCKET'):
        print("❌ S3_BUCKET not set")
        print("Run: source .env.local")
        return 1

    try:
        # Train
        model = train_model_locally()

        # Upload to S3
        model_uri, model_key = save_model_to_s3(model)

        # Save info
        info = save_model_info(model_uri, model_key)

        # Print next steps
        print("\n" + "="*80)
        print("✅ TRAINING COMPLETE!")
        print("="*80)
        print(f"""
Your trained model is ready for Lambda inference:

  S3 Location: {model_uri}
  Bucket:      {os.getenv('S3_BUCKET')}
  Key:         {model_key}

Next: Deploy to Lambda and test inference
        """)

        return 0

    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
