#!/usr/bin/env python3
"""
MOC (Map of Content) Generator

Generates index hub files for navigating notes.
Works based on notes_index.json.

Usage:
    python3 generate_moc.py           # Generate all MOCs
    python3 generate_moc.py --preview # Show preview without writing
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent

# Configuration
CONFIG = {
    "index_file": PROJECT_ROOT / "data" / "notes_index.json",
    "moc_dir": PROJECT_ROOT / "output" / "_MOC",
    "min_notes_for_tag_moc": 5,  # Minimum notes to create MOC for tag
}


def load_index() -> list:
    """Load notes index"""
    if not CONFIG["index_file"].exists():
        print(f"Index not found: {CONFIG['index_file']}")
        print("First run: python3 build_index.py")
        return []

    with open(CONFIG["index_file"], "r") as f:
        data = json.load(f)
        return data.get("notes", [])


def group_notes(notes: list) -> dict:
    """Group notes by categories, subcategories and tags"""
    groups = {
        "by_subcategory": defaultdict(list),
        "by_tag": defaultdict(list),
    }

    for note in notes:
        # By subcategory
        key = f"{note['category']}/{note['subcategory']}"
        groups["by_subcategory"][key].append(note)

        # By tag
        for tag in note.get("tags", []):
            if tag:
                groups["by_tag"][tag].append(note)

    return groups


def generate_subcategory_moc(subcategory: str, notes: list) -> str:
    """Generate MOC for subcategory"""
    category, subcat = subcategory.split("/")
    title = subcat.replace("-", " ").title()

    lines = [
        f"# MOC: {title}",
        "",
        f"> Category: {category}",
        f"> Notes: {len(notes)}",
        f"> Updated: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## Notes",
        "",
    ]

    # Sort by title
    for note in sorted(notes, key=lambda x: x.get("title", x["file"])):
        title = note.get("title", note["file"].replace(".md", ""))
        path = f"../{note['path']}"
        summary = note.get("summary", "")

        if summary:
            lines.append(f"- [{title}]({path}) — {summary}")
        else:
            lines.append(f"- [{title}]({path})")

    # Related tags
    all_tags = defaultdict(int)
    for note in notes:
        for tag in note.get("tags", []):
            if tag:
                all_tags[tag] += 1

    if all_tags:
        lines.extend([
            "",
            "## Popular Tags",
            "",
        ])
        for tag, count in sorted(all_tags.items(), key=lambda x: -x[1])[:10]:
            lines.append(f"- #{tag} ({count})")

    return "\n".join(lines)


def generate_tag_moc(tag: str, notes: list) -> str:
    """Generate MOC for tag"""
    lines = [
        f"# MOC: #{tag}",
        "",
        f"> Notes: {len(notes)}",
        f"> Updated: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## Notes",
        "",
    ]

    # Group by category
    by_category = defaultdict(list)
    for note in notes:
        by_category[note["category"]].append(note)

    for category in sorted(by_category.keys()):
        cat_notes = by_category[category]
        lines.append(f"### {category.title()}")
        lines.append("")

        for note in sorted(cat_notes, key=lambda x: x.get("title", x["file"])):
            title = note.get("title", note["file"].replace(".md", ""))
            path = f"../{note['path']}"
            lines.append(f"- [{title}]({path})")

        lines.append("")

    return "\n".join(lines)


def generate_main_moc(groups: dict, notes: list) -> str:
    """Generate main MOC index"""
    lines = [
        "# MOC: Main Index",
        "",
        f"> Total notes: {len(notes)}",
        f"> Updated: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## By Category",
        "",
    ]

    # Group subcategories by category
    categories = defaultdict(list)
    for subcat, subcat_notes in groups["by_subcategory"].items():
        cat = subcat.split("/")[0]
        categories[cat].append((subcat, len(subcat_notes)))

    for cat in ["areas", "resources", "archive"]:
        if cat in categories:
            lines.append(f"### {cat.title()}")
            lines.append("")
            for subcat, count in sorted(categories[cat]):
                name = subcat.split("/")[1]
                moc_file = f"_MOC-{name}.md"
                lines.append(f"- [{name}](./{moc_file}) ({count} notes)")
            lines.append("")

    # Top tags
    lines.extend([
        "## Popular Tags",
        "",
    ])

    tag_counts = [(tag, len(tag_notes)) for tag, tag_notes in groups["by_tag"].items()]
    for tag, count in sorted(tag_counts, key=lambda x: -x[1])[:15]:
        if count >= CONFIG["min_notes_for_tag_moc"]:
            lines.append(f"- [#{tag}](./_MOC-tag-{tag}.md) ({count})")
        else:
            lines.append(f"- #{tag} ({count})")

    return "\n".join(lines)


def save_moc(filename: str, content: str, preview: bool = False):
    """Save MOC file"""
    filepath = CONFIG["moc_dir"] / filename

    if preview:
        print(f"\n{'='*50}")
        print(f"FILE: {filename}")
        print("="*50)
        print(content[:500] + "..." if len(content) > 500 else content)
        return

    CONFIG["moc_dir"].mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    print(f"  Created: {filename}")


def main():
    parser = argparse.ArgumentParser(description="Generate MOC files")
    parser.add_argument("--preview", action="store_true", help="Show preview without writing")
    args = parser.parse_args()

    print("Loading index...")
    notes = load_index()

    if not notes:
        print("\nNo notes in index. Run these commands first:")
        print("  python3 categorize.py --limit 10")
        print("  python3 build_index.py")
        return

    print(f"Loaded {len(notes)} notes")

    print("\nGrouping...")
    groups = group_notes(notes)

    print(f"\nGenerating MOC...")

    # Main index
    main_moc = generate_main_moc(groups, notes)
    save_moc("_MOC-index.md", main_moc, args.preview)

    # MOC by subcategory
    for subcat, subcat_notes in groups["by_subcategory"].items():
        if len(subcat_notes) > 0:
            name = subcat.split("/")[1]
            content = generate_subcategory_moc(subcat, subcat_notes)
            save_moc(f"_MOC-{name}.md", content, args.preview)

    # MOC by tag (popular only)
    for tag, tag_notes in groups["by_tag"].items():
        if len(tag_notes) >= CONFIG["min_notes_for_tag_moc"]:
            content = generate_tag_moc(tag, tag_notes)
            save_moc(f"_MOC-tag-{tag}.md", content, args.preview)

    if not args.preview:
        print(f"\nMOC files created in: {CONFIG['moc_dir']}")


if __name__ == "__main__":
    main()
