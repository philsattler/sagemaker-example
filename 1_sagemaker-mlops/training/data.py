"""
Data loading and preprocessing for training.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path

def load_training_data(data_dir: str):
    """
    Load training data from the data directory.

    Expects:
    - data_dir/train.csv: Training data with features and target

    The last column is assumed to be the target.
    """
    csv_file = os.path.join(data_dir, "train.csv")

    if not os.path.exists(csv_file):
        # Look for any CSV file
        csv_files = list(Path(data_dir).glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {data_dir}")
        csv_file = csv_files[0]

    df = pd.read_csv(csv_file)

    # Assume last column is target
    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values

    # Convert to numpy arrays if needed
    if not isinstance(X, np.ndarray):
        X = np.array(X)
    if not isinstance(y, np.ndarray):
        y = np.array(y)

    return X, y
