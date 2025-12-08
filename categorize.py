#!/usr/bin/env python3
"""
Document Categorizer

LLM-powered document categorizer that organizes markdown files into PARA structure.
Uses Claude API to analyze content and automatically categorize documents.

Usage:
    python3 categorize.py --dry-run              # Test without changes
    python3 categorize.py --limit 10             # Process 10 files
    python3 categorize.py                        # Process all files
    python3 categorize.py --resume               # Continue from checkpoint

Requirements:
    - ANTHROPIC_API_KEY in .env file or environment variable
    - pip install anthropic python-dotenv
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional
import time

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional if key is in env

try:
    import anthropic
except ImportError:
    print("Install anthropic: pip install anthropic")
    sys.exit(1)

# Check API key
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("Error: ANTHROPIC_API_KEY not found")
    print("Add key to .env file:")
    print("  echo 'ANTHROPIC_API_KEY=sk-ant-...' >> .env")
    sys.exit(1)


# Configuration - customize these paths for your setup
PROJECT_ROOT = Path(__file__).parent
CONFIG = {
    "source_dir": PROJECT_ROOT / "input",           # Source markdown files
    "target_base": PROJECT_ROOT / "output",         # Target directory (PARA structure)
    "log_file": PROJECT_ROOT / "data" / "categorization.json",
    "checkpoint_file": PROJECT_ROOT / "data" / "checkpoint.json",
    "model": "claude-sonnet-4-20250514",            # Or claude-3-haiku-20240307 for cost savings
    "batch_size": 10,
    "max_content_length": 4000,                     # Truncate long notes
    "retry_attempts": 3,
    "retry_delay": 2,
}

# Categories and subcategories (PARA methodology)
CATEGORIES = {
    "areas": ["health", "finance", "career", "family"],
    "resources": ["data-science", "programming", "business", "personal-dev"],
    "archive": ["old-projects", "completed", "outdated"],
}

# Classification prompt
CLASSIFICATION_PROMPT_TEMPLATE = """You are a document classifier. Analyze the note and return ONLY JSON without markdown formatting.

CATEGORIES:
- areas: ongoing responsibilities (health, finance, family, career)
- resources: reference material, knowledge (data science, programming, business, personal development)
- archive: outdated, completed projects, temporary notes

SUBCATEGORIES:
areas → health | finance | career | family
resources → data-science | programming | business | personal-dev
archive → old-projects | completed | outdated

RULES:
1. If note is about health, fitness, medicine → areas/health
2. If note is about money, investments → areas/finance
3. If note is about work, career, skills → areas/career
4. If note is about family, children → areas/family
5. If note is about ML, Python, SQL, analytics → resources/data-science
6. If note is about code, architecture → resources/programming
7. If note is about business, sales → resources/business
8. If note is about personal growth, values → resources/personal-dev
9. If note is outdated, temporary, empty → archive

RESPONSE FORMAT (JSON only, no ```json):
{"category": "resources", "subcategory": "data-science", "tags": ["machine-learning", "python"], "summary": "Brief description"}

NOTE:
---
File: $FILENAME$
---
$CONTENT$"""


class DocumentCategorizer:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.client = anthropic.Anthropic()
        self.results = []
        self.errors = []
        self.processed_files = set()

        # Load checkpoint if exists
        self._load_checkpoint()

    def _load_checkpoint(self):
        """Load checkpoint to continue processing"""
        if CONFIG["checkpoint_file"].exists():
            with open(CONFIG["checkpoint_file"], "r") as f:
                data = json.load(f)
                self.processed_files = set(data.get("processed", []))
                print(f"Loaded checkpoint: {len(self.processed_files)} files already processed")

    def _save_checkpoint(self):
        """Save checkpoint"""
        CONFIG["checkpoint_file"].parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG["checkpoint_file"], "w") as f:
            json.dump({
                "processed": list(self.processed_files),
                "timestamp": datetime.now().isoformat(),
                "total_processed": len(self.processed_files),
                "last_file": list(self.processed_files)[-1] if self.processed_files else None
            }, f, ensure_ascii=False, indent=2)

        self._save_results()

    def _save_results(self):
        """Save results to JSON"""
        CONFIG["log_file"].parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG["log_file"], "w") as f:
            json.dump({
                "results": self.results,
                "errors": self.errors,
                "timestamp": datetime.now().isoformat(),
                "total_processed": len(self.results),
                "total_errors": len(self.errors)
            }, f, ensure_ascii=False, indent=2)
        print(f"Results saved to {CONFIG['log_file']}")

    def get_files_to_process(self, limit: Optional[int] = None) -> list[Path]:
        """Get list of files to process"""
        source = CONFIG["source_dir"]
        if not source.exists():
            print(f"Directory not found: {source}")
            print(f"Create it and add your markdown files: mkdir -p {source}")
            return []

        files = sorted(source.glob("*.md"))

        # Exclude already processed
        files = [f for f in files if f.name not in self.processed_files]

        if limit:
            files = files[:limit]

        return files

    def classify_note(self, filepath: Path) -> Optional[dict]:
        """Classify a single note via Claude API"""
        try:
            content = filepath.read_text(encoding="utf-8")

            # Truncate long content
            if len(content) > CONFIG["max_content_length"]:
                content = content[:CONFIG["max_content_length"]] + "\n...[truncated]..."

            prompt = CLASSIFICATION_PROMPT_TEMPLATE.replace(
                "$FILENAME$", filepath.name
            ).replace(
                "$CONTENT$", content
            )

            for attempt in range(CONFIG["retry_attempts"]):
                try:
                    response = self.client.messages.create(
                        model=CONFIG["model"],
                        max_tokens=500,
                        messages=[{"role": "user", "content": prompt}]
                    )

                    result_text = response.content[0].text.strip()

                    # Remove markdown formatting if present
                    result_text = re.sub(r"^```json?\s*", "", result_text)
                    result_text = re.sub(r"\s*```$", "", result_text)

                    # Find JSON object in text
                    start_idx = result_text.find("{")
                    end_idx = result_text.rfind("}") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        result_text = result_text[start_idx:end_idx]

                    result = json.loads(result_text)

                    # Validate result
                    if not self._validate_result(result):
                        raise ValueError(f"Invalid result: {result}")

                    return result

                except (json.JSONDecodeError, ValueError) as e:
                    if attempt < CONFIG["retry_attempts"] - 1:
                        print(f"  Attempt {attempt + 1} failed: {e}")
                        time.sleep(CONFIG["retry_delay"])
                    else:
                        raise

        except Exception as e:
            print(f"  Error classifying {filepath.name}: {e}")
            return None

    def _validate_result(self, result: dict) -> bool:
        """Validate classification result"""
        if "category" not in result or "subcategory" not in result:
            return False

        category = result["category"]
        subcategory = result["subcategory"]

        if category not in CATEGORIES:
            return False

        if subcategory not in CATEGORIES[category]:
            return False

        return True

    def add_frontmatter(self, filepath: Path, classification: dict) -> str:
        """Add frontmatter to file content"""
        content = filepath.read_text(encoding="utf-8")

        # Check if frontmatter already exists
        if content.startswith("---"):
            return content

        frontmatter = f"""---
title: "{filepath.stem}"
category: {classification['category']}
subcategory: {classification['subcategory']}
tags: {json.dumps(classification.get('tags', []), ensure_ascii=False)}
summary: "{classification.get('summary', '')}"
processed: {datetime.now().strftime('%Y-%m-%d')}
---

"""
        return frontmatter + content

    def process_file(self, filepath: Path) -> bool:
        """Process a single file: classify, add frontmatter, move"""
        print(f"Processing: {filepath.name}")

        # Classification
        classification = self.classify_note(filepath)
        if not classification:
            self.errors.append({
                "file": filepath.name,
                "error": "classification_failed"
            })
            return False

        print(f"  → {classification['category']}/{classification['subcategory']}")
        print(f"  → tags: {classification.get('tags', [])}")

        if self.dry_run:
            print("  [DRY RUN] Skipping write")
            self.results.append({
                "file": filepath.name,
                "classification": classification,
                "moved_to": f"output/{classification['category']}/{classification['subcategory']}/",
                "dry_run": True
            })
            return True

        # Add frontmatter
        new_content = self.add_frontmatter(filepath, classification)

        # Determine target folder
        target_dir = CONFIG["target_base"] / classification["category"] / classification["subcategory"]
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filepath.name

        # Write file with frontmatter
        target_path.write_text(new_content, encoding="utf-8")

        # Remove original
        filepath.unlink()

        self.results.append({
            "file": filepath.name,
            "classification": classification,
            "moved_to": str(target_path.relative_to(PROJECT_ROOT))
        })

        self.processed_files.add(filepath.name)

        return True

    def run(self, limit: Optional[int] = None, resume: bool = False):
        """Run processing"""
        if not resume:
            self.processed_files = set()

        files = self.get_files_to_process(limit)
        total = len(files)

        if total == 0:
            print("No files to process")
            return

        print(f"\nFound {total} files to process")
        if self.dry_run:
            print("DRY RUN MODE - files will not be changed\n")

        for i, filepath in enumerate(files, 1):
            print(f"\n[{i}/{total}] ", end="")
            self.process_file(filepath)

            # Save checkpoint every 10 files
            if i % 10 == 0:
                self._save_checkpoint()
                print(f"  [Checkpoint saved]")

            # Small delay between requests
            if not self.dry_run and i < total:
                time.sleep(0.5)

        # Final save
        self._save_checkpoint()

        print(f"\n{'='*50}")
        print(f"Processed: {len(self.results)}")
        print(f"Errors: {len(self.errors)}")
        print(f"Results: {CONFIG['log_file']}")


def main():
    parser = argparse.ArgumentParser(description="LLM Document Categorizer")
    parser.add_argument("--dry-run", action="store_true", help="Test mode without changes")
    parser.add_argument("--limit", type=int, help="Limit number of files")
    parser.add_argument("--resume", action="store_true", help="Continue from checkpoint")

    args = parser.parse_args()

    categorizer = DocumentCategorizer(dry_run=args.dry_run)
    categorizer.run(limit=args.limit, resume=args.resume)


if __name__ == "__main__":
    main()
