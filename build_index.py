#!/usr/bin/env python3
"""
Notes Index Builder

Builds an index of categorized notes from PARA structure.
Works independently of categorizer - can run anytime.

Usage:
    python3 build_index.py           # Build full index
    python3 build_index.py --stats   # Show statistics only
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict

try:
    import yaml
except ImportError:
    yaml = None
    print("Warning: PyYAML not installed. Frontmatter parsing will be limited.")
    print("Install with: pip install pyyaml")

PROJECT_ROOT = Path(__file__).parent

# Configuration
CONFIG = {
    "base_dirs": [
        PROJECT_ROOT / "output" / "areas",
        PROJECT_ROOT / "output" / "resources",
        PROJECT_ROOT / "output" / "archive",
    ],
    "index_file": PROJECT_ROOT / "data" / "notes_index.json",
    "stats_file": PROJECT_ROOT / "data" / "notes_stats.json",
}


def extract_frontmatter(content: str) -> dict:
    """Extract frontmatter from markdown file"""
    if not content.startswith("---"):
        return {}

    try:
        # Find end of frontmatter
        end_idx = content.find("---", 3)
        if end_idx == -1:
            return {}

        frontmatter_text = content[3:end_idx].strip()

        if yaml:
            return yaml.safe_load(frontmatter_text) or {}
        else:
            # Simple fallback parsing without yaml
            result = {}
            for line in frontmatter_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    result[key.strip()] = value.strip().strip('"')
            return result
    except:
        return {}


def scan_notes(base_dirs: list) -> list:
    """Scan all notes in specified directories"""
    notes = []

    for base_dir in base_dirs:
        if not base_dir.exists():
            continue

        for md_file in base_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                frontmatter = extract_frontmatter(content)

                # Determine category from path
                rel_path = md_file.relative_to(PROJECT_ROOT / "output")
                parts = rel_path.parts

                # Handle processed date - convert to string if needed
                processed = frontmatter.get("processed", "")
                if hasattr(processed, 'isoformat'):
                    processed = processed.isoformat()
                elif processed and not isinstance(processed, str):
                    processed = str(processed)

                # Handle tags - might be string or list
                tags = frontmatter.get("tags", [])
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except:
                        tags = [tags]

                note = {
                    "file": md_file.name,
                    "path": str(rel_path),
                    "category": parts[0] if len(parts) > 0 else "unknown",
                    "subcategory": parts[1] if len(parts) > 1 else "unknown",
                    "title": frontmatter.get("title", md_file.stem),
                    "tags": tags,
                    "summary": frontmatter.get("summary", ""),
                    "processed": processed,
                    "size": len(content),
                }
                notes.append(note)
            except Exception as e:
                print(f"Error reading {md_file}: {e}")

    return notes


def build_stats(notes: list) -> dict:
    """Build statistics for notes"""
    stats = {
        "total": len(notes),
        "by_category": defaultdict(int),
        "by_subcategory": defaultdict(int),
        "by_tag": defaultdict(int),
        "total_size_mb": sum(n["size"] for n in notes) / (1024 * 1024),
    }

    for note in notes:
        stats["by_category"][note["category"]] += 1
        stats["by_subcategory"][f"{note['category']}/{note['subcategory']}"] += 1

        for tag in note.get("tags", []):
            if tag:  # Skip empty tags
                stats["by_tag"][tag] += 1

    # Convert defaultdict to regular dict for JSON
    stats["by_category"] = dict(stats["by_category"])
    stats["by_subcategory"] = dict(stats["by_subcategory"])
    stats["by_tag"] = dict(sorted(stats["by_tag"].items(), key=lambda x: -x[1])[:50])

    return stats


def save_index(notes: list, stats: dict):
    """Save index and statistics"""
    CONFIG["index_file"].parent.mkdir(parents=True, exist_ok=True)

    # Index
    with open(CONFIG["index_file"], "w") as f:
        json.dump({
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
            "total": len(notes)
        }, f, ensure_ascii=False, indent=2)

    # Statistics
    with open(CONFIG["stats_file"], "w") as f:
        json.dump({
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)

    print(f"Index saved: {CONFIG['index_file']}")
    print(f"Statistics: {CONFIG['stats_file']}")


def print_stats(stats: dict):
    """Print statistics"""
    print("\n" + "="*50)
    print("NOTES STATISTICS")
    print("="*50)

    print(f"\nTotal notes: {stats['total']}")
    print(f"Total size: {stats['total_size_mb']:.1f} MB")

    print("\nBy category:")
    for cat, count in sorted(stats["by_category"].items()):
        print(f"  {cat}: {count}")

    print("\nBy subcategory:")
    for subcat, count in sorted(stats["by_subcategory"].items(), key=lambda x: -x[1]):
        print(f"  {subcat}: {count}")

    if stats["by_tag"]:
        print("\nTop 20 tags:")
        for i, (tag, count) in enumerate(list(stats["by_tag"].items())[:20], 1):
            print(f"  {i}. {tag}: {count}")


def main():
    parser = argparse.ArgumentParser(description="Build notes index")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    args = parser.parse_args()

    print("Scanning notes...")
    notes = scan_notes(CONFIG["base_dirs"])

    print(f"Found {len(notes)} notes")

    if len(notes) == 0:
        print("\nNo notes found. Make sure you have categorized some documents first:")
        print("  python3 categorize.py --limit 10")
        return

    stats = build_stats(notes)

    if args.stats:
        print_stats(stats)
    else:
        save_index(notes, stats)
        print_stats(stats)


if __name__ == "__main__":
    main()
