#!/bin/bash
# Build Lambda deployment package using Docker
# Creates a zip with Linux-compatible binaries

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="/tmp/lambda_build"
ZIP_PATH="$SCRIPT_DIR/lambda_package.zip"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Build Lambda Package with Docker                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    echo "   Start Docker and try again: docker run hello-world"
    exit 1
fi

echo "✓ Docker is available"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Build Docker image
echo "Building Docker image..."
docker build -f "$SCRIPT_DIR/Dockerfile.lambda" -t lambda-builder "$SCRIPT_DIR"

echo ""
echo "Creating Lambda package..."
docker run --rm -v "$OUTPUT_DIR:/output" lambda-builder

echo ""

# Check if zip was created
if [ -f "$OUTPUT_DIR/lambda_package.zip" ]; then
    # Move to batch directory
    cp "$OUTPUT_DIR/lambda_package.zip" "$ZIP_PATH"
    SIZE=$(du -h "$ZIP_PATH" | cut -f1)
    echo "✅ Lambda package created successfully!"
    echo "   Location: $ZIP_PATH"
    echo "   Size: $SIZE"
    echo ""
    echo "Next: Deploy with"
    echo "  python3 deploy_aws_cli.py"
else
    echo "❌ Failed to create Lambda package"
    exit 1
fi
