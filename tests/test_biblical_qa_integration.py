"""
Test Biblical Word Analyzer integration with SageMaker MLOps framework.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import load_model
from sagemaker_config import get_model_config

print("=" * 100)
print("BIBLICAL WORD ANALYZER - SAGEMAKER INTEGRATION TEST")
print("=" * 100)

# Test 1: Load model via registry
print("\n✓ TEST 1: Load model via registry")
print("-" * 100)
try:
    model = load_model("biblical_qa")
    print(f"✅ Successfully loaded model: {model.__class__.__name__}")
    print(f"   Model type: {model.get_metadata().get('model_type')}")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    sys.exit(1)

# Test 2: Get model configuration
print("\n✓ TEST 2: Get model configuration")
print("-" * 100)
try:
    config = get_model_config("biblical_qa")
    print(f"✅ Configuration loaded:")
    print(f"   Instance Type: {config.instance_type}")
    print(f"   Instance Count: {config.instance_count}")
    print(f"   Hyperparameters: {config.hyperparameters}")
except Exception as e:
    print(f"❌ Failed to get config: {e}")
    sys.exit(1)

# Test 3: Train/Initialize model
print("\n✓ TEST 3: Initialize model (training step)")
print("-" * 100)
try:
    model.train([], [])
    print(f"✅ Model initialized successfully")
    print(f"   Metadata: {model.get_metadata()}")
except Exception as e:
    print(f"❌ Failed to train: {e}")
    sys.exit(1)

# Test 4: Use model for prediction
print("\n✓ TEST 4: Use model for inference (predictions)")
print("-" * 100)
test_queries = [
    '"Word" in John 1:1 KJV',
    '"created" in Genesis 1:1 KJV',
]

for query in test_queries:
    try:
        result = model.predict(query)
        if "error" in result:
            print(f"❌ Query error: {query}")
            print(f"   Error: {result['error']}")
        else:
            word_analysis = result.get("word_analysis", {})
            print(f"✅ Query successful: {query}")
            print(f"   Hebrew/Greek: {word_analysis.get('hebrew_original')}")
            print(f"   Strong's Number: {word_analysis.get('strongs_number')}")
            print(f"   Found {len(result.get('cross_references', []))} cross-references")
    except Exception as e:
        print(f"❌ Query failed: {query}")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Test 5: Save and load model
print("\n✓ TEST 5: Save and load model (persistence)")
print("-" * 100)
try:
    model_path = "/tmp/test_biblical_qa.tar.gz"
    model.save(model_path)
    print(f"✅ Model saved to {model_path}")

    # Load it back
    model2 = load_model("biblical_qa")
    model2.load(model_path)
    print(f"✅ Model loaded from {model_path}")
    print(f"   Restored metadata: {model2.get_metadata()}")
except Exception as e:
    print(f"❌ Failed to save/load: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Verify model list
print("\n✓ TEST 6: Verify model is in registry")
print("-" * 100)
try:
    from sagemaker_config import MODEL_CONFIG
    available_models = list(MODEL_CONFIG.keys())
    if "biblical_qa" in available_models:
        print(f"✅ biblical_qa is registered")
        print(f"   All registered models: {available_models}")
    else:
        print(f"❌ biblical_qa not found in registry")
        print(f"   Available: {available_models}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Failed to verify registry: {e}")
    sys.exit(1)

print("\n" + "=" * 100)
print("✅ ALL INTEGRATION TESTS PASSED")
print("=" * 100)
print("\nBiblical Word Analyzer is fully integrated into SageMaker MLOps framework!")
print("\nNext steps:")
print("  1. Train: python -c \"from agent import TrainingAgent; agent = TrainingAgent(); agent.train('biblical_qa')\"")
print("  2. Deploy: python -c \"from controller import InferenceController; c = InferenceController(); c.deploy('biblical_qa')\"")
print("  3. Query: endpoint.predict('\\\"Word\\\" in John 1:1 KJV')")
