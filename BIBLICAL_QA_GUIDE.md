# Biblical Word Analyzer - SageMaker MLOps Integration Guide

## Overview

The Biblical Word Analyzer is now fully integrated into your SageMaker MLOps framework. It provides:

- **Word Lookup**: Map English words to original Hebrew/Greek
- **Strong's Concordance**: Access lexicon definitions and morphological analysis
- **Cross-References**: Find related verses using the same original word
- **Theological Context**: Understand original meaning and theological significance
- **LLM Explanations**: Get accessible, theologically-informed explanations

## Quick Start

### Option 1: Local Testing (Recommended for Development)

```python
from models import load_model

# Load the model
model = load_model("biblical_qa")
model.train([], [])  # Initialize

# Make a query
result = model.predict('"Word" in John 1:1 KJV')

# Access the results
word = result['word_analysis']['hebrew_original']
strongs = result['word_analysis']['strongs_number']
cross_refs = result['cross_references']

print(f"Original: {word} ({strongs})")
print(f"Cross-references: {len(cross_refs)}")
```

### Option 2: SageMaker Training (Production)

```python
from agent import TrainingAgent

agent = TrainingAgent()

# Submit training job to SageMaker
job_name = agent.train(
    model_name="biblical_qa",
    wait=False  # Async job submission
)

print(f"Training job: {job_name}")
# Check progress in SageMaker console
```

### Option 3: SageMaker Inference Endpoint (Production)

```python
from controller import InferenceController

controller = InferenceController()

# Deploy to SageMaker endpoint
endpoint = controller.deploy(
    model_name="biblical_qa",
    wait=True  # Wait for endpoint to be ready
)

# Make queries
result = endpoint.predict('"created" in Genesis 1:1 KJV')

# Clean up when done
endpoint.delete()
```

## File Structure

```
biblical_qa/                          # Biblical Word Analyzer module
├── __init__.py                      # Package exports
├── analyzer.py                      # Main BiblicalWordAnalyzer class
├── word_lookup.py                   # Word ↔ Hebrew/Greek mapping
├── concordance_data.py              # Strong's concordance data
├── cross_references.py              # Cross-reference generation
└── explainer.py                     # LLM explanation layer

models/__init__.py                   # Includes biblical_qa in registry
sagemaker_config.py                  # biblical_qa configuration
biblical_qa_example.py               # Complete usage example
```

## Configuration

The model is configured in `sagemaker_config.py`:

```python
"biblical_qa": ModelConfig(
    instance_type="ml.m5.large",
    instance_count=1,
    hyperparameters={
        "model_type": "biblical_word_analyzer",
        "description": "Biblical Word Analyzer..."
    }
)
```

## Query Format

All queries follow this format:

```
"<word>" in <Book> <Chapter>:<Verse> <Translation>
```

**Examples:**
- `"Word" in John 1:1 KJV`
- `"created" in Genesis 1:1 NIV`
- `"Trust" in Proverbs 3:5 ESV`

## Output Structure

Each prediction returns:

```python
{
    "query": {
        "word": "Word",
        "verse": "John 1:1",
        "translation": "KJV"
    },
    "word_analysis": {
        "hebrew_original": "λόγος",
        "transliteration": "logos",
        "morphology": "noun, masculine, singular, nominative",
        "strongs_number": "G3056",
        "strongs_definition": "...",
        "lexicon_definition": "..."
    },
    "explanations": {
        "simple_explanation": "...",
        "theological_explanation": "...",
        "cultural_linguistic_notes": {...},
        "key_takeaway": "..."
    },
    "verse_original_language": {
        "hebrew": "...",
        "transliteration": "...",
        "word_breakdown": [...]
    },
    "cross_references": [
        {
            "verse": "John 1:14",
            "text": "...",
            "reason": "...",
            "score": 1.48
        }
    ],
    "theological_significance": "..."
}
```

## Integration with MLOps Pipeline

### In Model Registry

The model is registered in `models/__init__.py`:

```python
def load_model(model_name: str) -> BaseModel:
    models = {
        "xgbregressor": XGBRegressor,
        "lightgbmclassifier": LightGBMClassifier,
        "biblical_qa": BiblicalWordAnalyzer,  # ← Registered here
    }
```

### In SageMaker Config

Configuration is in `sagemaker_config.py`:

```python
MODEL_CONFIG = {
    "biblical_qa": ModelConfig(...)  # ← Configured here
}
```

### Training via Agent

```python
from agent import TrainingAgent
agent = TrainingAgent()
job = agent.train("biblical_qa")  # Works just like other models
```

### Inference via Controller

```python
from controller import InferenceController
controller = InferenceController()
endpoint = controller.deploy("biblical_qa")
```

## Extending the System

### Add More Bible Verses

Edit `biblical_qa/concordance_data.py`:

```python
HEBREW_LEXICON = {
    "H7225": {
        "hebrew": "רֵאשִׁית",
        "transliteration": "reshit",
        # ... add more entries
    }
}

STRONGS_TO_VERSES = {
    "H7225": [
        {"book": "Genesis", "chapter": 1, "verse": 1, "text": "..."},
        # ... add more verses
    ]
}
```

### Add New Translations

Edit `biblical_qa/word_lookup.py`:

```python
BIBLE_DATABASE = {
    "KJV": {...},
    "NIV": {...},
    "ESV": {...},
    "NASB": {...},  # ← Add new translation
}
```

### Improve Explanations with LLM

The `lingual_explainer.py` module can be enhanced with an actual LLM call:

```python
# Add to lingual_explainer.py
from anthropic import Anthropic

def explain_with_claude(strongs_definition, context):
    client = Anthropic()
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"Explain this biblical term accessibly: {strongs_definition}"
            }
        ]
    )
    return message.content[0].text
```

## Testing

Run the integration tests:

```bash
# Test integration with SageMaker framework
python tests/test_biblical_qa_integration.py

# Test Biblical Word Analyzer directly
python tests/test_biblical_word_analyzer.py

# Run complete example
python biblical_qa_example.py
```

## Common Commands

```bash
# Load and use locally
python -c "
from models import load_model
model = load_model('biblical_qa')
model.train([], [])
result = model.predict('\"Word\" in John 1:1 KJV')
print(result['word_analysis'])
"

# Check configuration
python -c "
from sagemaker_config import get_model_config
config = get_model_config('biblical_qa')
print(f'Instance: {config.instance_type}')
"

# Submit to SageMaker (requires quota)
python -c "
from agent import TrainingAgent
agent = TrainingAgent()
agent.train('biblical_qa')
"
```

## FAQ

**Q: Do I need AWS quota to use this?**
A: No! The model works perfectly locally. AWS quota is only needed if you want to deploy to SageMaker endpoints.

**Q: Can I add more Bible verses?**
A: Yes! Edit `concordance_data.py` to add more verses and Strong's mappings.

**Q: Can I use a real LLM for explanations?**
A: Yes! The explainer module is designed to accept LLM calls. You can use Claude API for better explanations.

**Q: How do I scale this to more verses?**
A: Load Bible data from APIs (Bible.is, OpenBible.info) instead of hardcoding. Update `word_lookup.py` to fetch from APIs.

**Q: Can this work with other languages?**
A: Yes! The system is designed to handle any language pair. Add new languages to the lexicon data.

## Next Steps

1. **Local Development**: Use `biblical_qa_example.py` to get familiar with the system
2. **Extend Data**: Add more Bible verses and translations
3. **Enhance Explanations**: Integrate with Claude API for better explanations
4. **Scale**: Connect to real Bible APIs for complete verse coverage
5. **Deploy**: Once comfortable, request AWS quota and deploy to SageMaker

## Support

For issues or questions:
- Check `tests/test_biblical_qa_integration.py` for integration examples
- Run `python biblical_qa_example.py` for a full walkthrough
- Review `CLAUDE.md` for architecture details
