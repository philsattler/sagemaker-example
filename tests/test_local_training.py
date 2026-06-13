import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Import your model
from models import load_model

# Create sample data locally
print("Creating sample training data...")
np.random.seed(42)
X = np.random.rand(100, 4)
y = np.random.rand(100)

# Split data
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"Training data shape: {X_train.shape}")
print(f"Validation data shape: {X_val.shape}")

# Load and train model
print("\nTraining XGBRegressor locally...")
model = load_model("xgbregressor")

model.train(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    early_stopping_rounds=10
)

# Test predictions
print("\nMaking predictions...")
predictions = model.predict(X_val[:5])
print(f"Predictions: {predictions}")

# Save model
print("\nSaving model...")
model.save("/tmp/local_model.tar.gz")
print("✅ Model saved to /tmp/local_model.tar.gz")

# Test loading
print("\nLoading model...")
model2 = load_model("xgbregressor")
model2.load("/tmp/local_model.tar.gz")
predictions2 = model2.predict(X_val[:5])
print(f"Predictions after reload: {predictions2}")
print("✅ Training complete!")
