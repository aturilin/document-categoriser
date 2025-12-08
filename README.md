# Document Categorizer

LLM-powered document categorizer that automatically organizes markdown files into [PARA](https://fortelabs.com/blog/para/) structure using Claude API.

## Features

- **AI-Powered Classification**: Uses Claude to analyze content and categorize documents
- **PARA Methodology**: Organizes into Areas, Resources, and Archive
- **Automatic Frontmatter**: Adds metadata (category, tags, summary) to each file
- **Checkpointing**: Resume processing from where you left off
- **MOC Generation**: Creates Map of Content hub files for navigation
- **Dry Run Mode**: Test without making changes

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/aturilin/document-categoriser.git
cd document-categoriser
pip install -r requirements.txt
```

### 2. Add Your API Key

```bash
echo 'ANTHROPIC_API_KEY=sk-ant-your-key-here' > .env
```

Get your API key from [console.anthropic.com](https://console.anthropic.com/)

### 3. Add Your Documents

```bash
mkdir -p input
cp /path/to/your/notes/*.md input/
```

### 4. Run Categorizer

```bash
# Test with 5 files first (dry run)
python3 categorize.py --dry-run --limit 5

# Process 10 files for real
python3 categorize.py --limit 10

# Process all files
python3 categorize.py

# Resume if interrupted
python3 categorize.py --resume
```

### 5. Build Index and MOC

```bash
# Build searchable index
python3 build_index.py

# Generate navigation hubs
python3 generate_moc.py
```

## Directory Structure

```
document-categoriser/
├── input/                    # Put your markdown files here
├── output/                   # Categorized files appear here
│   ├── areas/
│   │   ├── health/
│   │   ├── finance/
│   │   ├── career/
│   │   └── family/
│   ├── resources/
│   │   ├── data-science/
│   │   ├── programming/
│   │   ├── business/
│   │   └── personal-dev/
│   ├── archive/
│   │   ├── old-projects/
│   │   ├── completed/
│   │   └── outdated/
│   └── _MOC/                 # Generated navigation hubs
├── data/                     # Index, stats, checkpoints
├── categorize.py             # Main categorizer
├── build_index.py            # Index builder
├── generate_moc.py           # MOC generator
└── requirements.txt
```

## PARA Categories

| Category | Description | Subcategories |
|----------|-------------|---------------|
| **areas** | Ongoing responsibilities | health, finance, career, family |
| **resources** | Reference material | data-science, programming, business, personal-dev |
| **archive** | Completed/outdated | old-projects, completed, outdated |

## Customization

### Change Categories

Edit `CATEGORIES` dict in `categorize.py`:

```python
CATEGORIES = {
    "areas": ["health", "finance", "career", "family", "your-area"],
    "resources": ["programming", "your-resource"],
    "archive": ["outdated"],
}
```

### Change Prompt

Edit `CLASSIFICATION_PROMPT_TEMPLATE` in `categorize.py` to adjust classification rules.

### Use Different Model

```python
CONFIG = {
    "model": "claude-3-haiku-20240307",  # Cheaper, faster
    # or
    "model": "claude-sonnet-4-20250514",  # Better quality
}
```

## Commands Reference

### categorize.py

```bash
python3 categorize.py [options]

Options:
  --dry-run     Test without changes
  --limit N     Process only N files
  --resume      Continue from checkpoint
```

### build_index.py

```bash
python3 build_index.py [options]

Options:
  --stats       Show statistics only (no file write)
```

### generate_moc.py

```bash
python3 generate_moc.py [options]

Options:
  --preview     Show preview without writing files
```

## Example Output

After processing, a file gets frontmatter:

```markdown
---
title: "Python Machine Learning Notes"
category: resources
subcategory: data-science
tags: ["machine-learning", "python", "sklearn"]
summary: "Notes on ML algorithms and scikit-learn usage"
processed: 2025-01-15
---

# Original content here...
```

## Cost Estimation

- Claude Sonnet: ~$0.003 per document (4K tokens avg)
- Claude Haiku: ~$0.0003 per document

For 1000 documents: ~$3 (Sonnet) or ~$0.30 (Haiku)

## License

MIT
