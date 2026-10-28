#!/usr/bin/env python3
"""Lightweight summary of a JSONL scrape (replaces notebook/SQL exploration ideas)."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize OpenRice JSONL scrape")
    parser.add_argument(
        "path",
        nargs="?",
        default="data/processed/sample.jsonl",
        help="JSONL file to summarize",
    )
    args = parser.parse_args()
    path = Path(args.path)
    if not path.exists():
        print(f"File not found: {path}")
        return 1

    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    print(f"records: {len(rows)}")
    if not rows:
        return 0

    bookmarks = [r.get("bookmarked_user_count") or 0 for r in rows]
    reviews = [r.get("review_count") or 0 for r in rows]
    print(f"bookmark mean: {sum(bookmarks) / len(bookmarks):.1f}")
    print(f"review mean: {sum(reviews) / len(reviews):.1f}")

    cat_counts: Counter[str] = Counter()
    for row in rows:
        for name in row.get("categories") or []:
            cat_counts[name] += 1
    print("top categories:")
    for name, count in cat_counts.most_common(10):
        print(f"  {count:4d}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
