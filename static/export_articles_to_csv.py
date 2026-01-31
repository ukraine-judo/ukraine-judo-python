#!/usr/bin/env python3
"""
Export Articles to CSV
======================

Utility script for one-time conversion of local JSON articles (stored in
`database/articles/`) to a single CSV file.  Fields are flattened for easy
import into other systems (e.g., Supabase, spreadsheets).

Usage (from project root)::

    # Export from directory
    python scripts/utils/export_articles_to_csv.py --input-dir database/articles --output-file exported_articles.csv
    
    # Export from single JSON file
    python scripts/utils/export_articles_to_csv.py --input-file all_articles.json --output-file exported_articles.csv

    python export_articles_to_csv.py --input-file news.json --output-file exported_articles.csv
 python export_articles_to_csv.py --input-file out.json --output-file exported_articles.csv
If arguments are omitted, you must specify either --input-dir or --input-file.

This script respects the user's rule of keeping the codebase tidy by living in
`scripts/utils/` and being self-contained.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# --------------------------- Helper Functions ----------------------------- #

def _flatten_article(article: Dict[str, Any]) -> Dict[str, Any] | None:
    """Validate and flatten a single article dict."""
    required = {"id", "title", "date"}
    if not required.issubset(article):
        return None
    return {
        "id": article.get("id", ""),
        "title": article.get("title", ""),
        "category": article.get("category", ""),
        "author_name": article.get("author_name", ""),
        "publishedAt": article.get("date", ""),
        "excerpt": article.get("excerpt", ""),
        "featured": article.get("featured", False),
        "image_url": article.get("image", ""),
        "tags": ";".join(article.get("tags", [])) if article.get("tags") else "",
        "content": article.get("html", ""),
    }


def load_articles(path: Path) -> List[Dict[str, Any]]:
    """Load JSON file that may contain one article object or a list."""
    try:
        with path.open(encoding="utf-8") as fp:
            data = json.load(fp)
    except (json.JSONDecodeError, OSError) as exc:
        logging.error("Failed to load %s: %s", path.name, exc)
        return []

    articles: List[Dict[str, Any]] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                flat = _flatten_article(item)
                if flat:
                    articles.append(flat)
    elif isinstance(data, dict):
        flat = _flatten_article(data)
        if flat:
            articles.append(flat)
    else:
        logging.warning("%s has unsupported JSON structure; skipped", path.name)
    return articles


def gather_articles(directory: Path) -> List[Dict[str, Any]]:
    """Recursively collect and load all *.json articles inside *directory*."""
    combined: List[Dict[str, Any]] = []
    for json_path in directory.rglob("*.json"):
        combined.extend(load_articles(json_path))
    return combined


def write_csv(articles: List[Dict[str, Any]], output_file: Path) -> None:
    """Write list of *articles* dictionaries to *output_file* as CSV."""
    if not articles:
        logging.warning("No valid articles found — CSV not created.")
        return

    # CSV header order for consistency
    preferred = [
        "id",
        "title",
        "category",
        "author_name",
        "publishedAt",
        "excerpt",
        "featured",
        "image_url",
        "tags",
        "content",
    ]
    fieldnames = preferred + [k for k in articles[0].keys() if k not in preferred]

    with output_file.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(articles)
    logging.info("CSV exported: %s (%d rows)", output_file, len(articles))

# ------------------------------ Main Logic -------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description="Export local JSON news articles to CSV.")
    
    # Create mutually exclusive group for input
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input-dir", 
        type=Path,
        help="Directory with JSON article files"
    )
    input_group.add_argument(
        "--input-file", 
        type=Path,
        help="Single JSON file with all articles"
    )
    
    parser.add_argument(
        "--output-file", 
        default="exported_articles.csv", 
        type=Path,
        help="Output CSV path (default: exported_articles.csv)"
    )
    
    args = parser.parse_args()

    output_file = args.output_file.expanduser().resolve()
    articles: List[Dict[str, Any]] = []

    if args.input_file:
        # Load from single file
        input_file = args.input_file.expanduser().resolve()
        if not input_file.exists():
            parser.error(f"Input file not found: {input_file}")
        if not input_file.is_file():
            parser.error(f"Input path is not a file: {input_file}")
        
        logging.info("Loading articles from file: %s", input_file)
        articles = load_articles(input_file)
        
    elif args.input_dir:
        # Load from directory
        input_dir = args.input_dir.expanduser().resolve()
        if not input_dir.exists():
            parser.error(f"Input directory not found: {input_dir}")
        if not input_dir.is_dir():
            parser.error(f"Input path is not a directory: {input_dir}")
        
        logging.info("Scanning %s for JSON articles…", input_dir)
        articles = gather_articles(input_dir)

    write_csv(articles, output_file)


if __name__ == "__main__":
    main()