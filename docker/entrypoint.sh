#!/bin/bash

set -e

# Default to training phase if not specified
PHASE=${PHASE:-train}
MODEL_NAME=${MODEL_NAME:-xgbregressor}

echo "Starting SageMaker container - Phase: $PHASE, Model: $MODEL_NAME"

if [ "$PHASE" = "train" ]; then
    echo "Running training entry point..."
    python training/entry.py \
        --model-name "$MODEL_NAME" \
        --hyperparameters "${HYPERPARAMETERS:-'{}'}"
elif [ "$PHASE" = "inference" ]; then
    echo "Starting inference server..."
    python inference/entry.py
else
    echo "Unknown phase: $PHASE"
    exit 1
fi
