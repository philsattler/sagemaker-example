# Biblical Word Analyzer - CLI Cheat Sheet

## Quick Start

```bash
python biblical_qa_cli.py Word in John 1:1 KJV
```

## Common Queries

### New Testament

```bash
# John 1:1 - The Word
python biblical_qa_cli.py Word in John 1:1 KJV

# Matthew 5:3 - Blessed
python biblical_qa_cli.py Blessed in Matthew 5:3 KJV

# Romans 3:23 - Sin
python biblical_qa_cli.py sin in Romans 3:23 KJV

# 1 Corinthians 13:4 - Love
python biblical_qa_cli.py Love in 1_Corinthians 13:4 KJV
```

### Old Testament

```bash
# Genesis 1:1 - Created
python biblical_qa_cli.py created in Genesis 1:1 KJV

# Genesis 1:1 - Beginning
python biblical_qa_cli.py beginning in Genesis 1:1 KJV

# Psalm 23:1 - Lord
python biblical_qa_cli.py Lord in Psalm 23:1 KJV

# Proverbs 3:5 - Trust
python biblical_qa_cli.py Trust in Proverbs 3:5 KJV
```

## Supported Translations

- **KJV** - King James Version
- **NIV** - New International Version
- **ESV** - English Standard Version

## Query Format

```
python biblical_qa_cli.py WORD in BOOK CHAPTER:VERSE TRANSLATION
```

### Parts

- **WORD** - The word to analyze (case-insensitive)
- **in** - Literal "in" separator
- **BOOK** - Bible book name
  - Single-word: Genesis, John, Psalm, Proverbs, Isaiah, etc.
  - Multi-word: Use underscore (1_Corinthians, 1_Timothy, etc.)
- **CHAPTER:VERSE** - Numbers with colon (1:1, 23:5, 3:16, etc.)
- **TRANSLATION** - KJV, NIV, or ESV

## Output Explanation

### 📖 Original Word Analysis
- **Hebrew/Greek** - The word in its original language
- **Transliteration** - How to pronounce it
- **Morphology** - Part of speech, gender, number, tense
- **Strong's Number** - Cross-reference ID (H=Hebrew, G=Greek)
- **Definition** - Strong's dictionary definition

### 💡 Explanations
- **Simple** - Easy-to-understand explanation
- **Theological** - Deeper theological meaning and significance
- **Key Takeaway** - The most important insight

### 📝 Verse in Original Language
- Complete verse in Hebrew or Greek
- Transliteration for pronunciation
- Word-by-word breakdown showing meaning of each component

### 🔗 Cross-References
- Other verses using the same Hebrew/Greek word
- Ranked by theological relevance
- Shows how the word is used elsewhere in Scripture

### ✝️ Theological Significance
- Context and broader theological implications
- How this word relates to key biblical themes

## Examples by Theme

### Creation
```bash
python biblical_qa_cli.py created in Genesis 1:1 KJV
python biblical_qa_cli.py made in Genesis 1:7 KJV
python biblical_qa_cli.py formed in Genesis 2:7 KJV
```

### God's Word
```bash
python biblical_qa_cli.py Word in John 1:1 KJV
python biblical_qa_cli.py word in Psalm 119:105 KJV
python biblical_qa_cli.py spoke in Genesis 1:3 KJV
```

### Faith & Trust
```bash
python biblical_qa_cli.py Trust in Proverbs 3:5 KJV
python biblical_qa_cli.py faith in Hebrews 11:1 KJV
python biblical_qa_cli.py believe in John 3:16 KJV
```

### Love
```bash
python biblical_qa_cli.py Love in 1_John 4:8 KJV
python biblical_qa_cli.py love in 1_Corinthians 13:4 KJV
python biblical_qa_cli.py loved in John 3:16 KJV
```

### Blessing
```bash
python biblical_qa_cli.py Blessed in Matthew 5:3 KJV
python biblical_qa_cli.py bless in Genesis 1:28 KJV
python biblical_qa_cli.py blessing in Genesis 12:2 KJV
```

## Interactive Mode

```bash
python
>>> from models import load_model
>>> model = load_model("biblical_qa")
>>> model.train([], [])
>>> 
>>> # Single query
>>> result = model.predict('"Word" in John 1:1 KJV')
>>> 
>>> # Access specific parts
>>> word = result['word_analysis']['hebrew_original']
>>> strongs = result['word_analysis']['strongs_number']
>>> cross_refs = result['cross_references']
>>> explanations = result['explanations']
>>> 
>>> # Pretty print JSON
>>> import json
>>> print(json.dumps(result['word_analysis'], indent=2))
>>> 
>>> exit()
```

## Tips & Tricks

### Get just the Hebrew/Greek word
```bash
python -c "from models import load_model; m = load_model('biblical_qa'); m.train([], []); r = m.predict('\"Word\" in John 1:1 KJV'); print(r['word_analysis']['hebrew_original'])"
```

### Get Strong's number
```bash
python -c "from models import load_model; m = load_model('biblical_qa'); m.train([], []); r = m.predict('\"created\" in Genesis 1:1 KJV'); print(r['word_analysis']['strongs_number'])"
```

### Count cross-references
```bash
python -c "from models import load_model; m = load_model('biblical_qa'); m.train([], []); r = m.predict('\"Trust\" in Proverbs 3:5 KJV'); print(f'Found {len(r[\"cross_references\"])} cross-references')"
```

### Export as JSON
```bash
python -c "from models import load_model; import json; m = load_model('biblical_qa'); m.train([], []); r = m.predict('\"Word\" in John 1:1 KJV'); print(json.dumps(r, indent=2))" > output.json
```

## Help

```bash
python biblical_qa_cli.py --help
python biblical_qa_cli.py -h
python biblical_qa_cli.py help
```

## Troubleshooting

### "Invalid query format"
- Check syntax: `python biblical_qa_cli.py WORD in BOOK CHAPTER:VERSE TRANSLATION`
- Make sure all parts are present
- Check translation code (KJV, NIV, ESV)

### "Error during analysis"
- Verify the verse exists
- Check that the book name is spelled correctly
- Try a different translation

### Word not found
- The word may not be in the current Bible database
- Database contains ~100 verses - more can be added to `biblical_qa/concordance_data.py`

## Performance

- First run: ~1-2 seconds (model initialization)
- Subsequent queries: <1 second
- No internet required (fully local)

## Next Steps

- Add more verses to expand the database
- Export results to JSON for further processing
- Integrate with other tools via JSON output
- Use in scripts and automation
