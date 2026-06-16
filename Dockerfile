FROM python:3.11-slim

WORKDIR /opt/ml/code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY 1_sagemaker-mlops/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy model code
COPY 1_sagemaker-mlops/models/ ./models/
COPY 1_sagemaker-mlops/training/ ./training/
COPY 1_sagemaker-mlops/inference/ ./inference/
COPY 1_sagemaker-mlops/sagemaker_config.py .

# Create directories expected by SageMaker
RUN mkdir -p /opt/ml/input/data/training
RUN mkdir -p /opt/ml/model
RUN mkdir -p /opt/ml/code

# Set environment variables
ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE

# Entry point for training or inference
# Usage: docker run -e PHASE=train ... or docker run -e PHASE=inference ...
COPY docker/entrypoint.sh /opt/ml/code/entrypoint.sh
RUN chmod +x /opt/ml/code/entrypoint.sh

ENTRYPOINT ["/opt/ml/code/entrypoint.sh"]
