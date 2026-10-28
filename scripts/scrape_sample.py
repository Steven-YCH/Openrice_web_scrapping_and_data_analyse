#!/usr/bin/env python3
"""Demo: scrape one page for one district into data/processed/sample.jsonl."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running without install when src/ is on PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from openrice_scraper.client import OpenRiceClient
from openrice_scraper.config import ScraperSettings
from openrice_scraper.search import scrape_district
from openrice_scraper.storage import write_records


def main() -> int:
    out = ROOT / "data" / "processed" / "sample.jsonl"
    settings = ScraperSettings(delay_seconds=1.0)
    with OpenRiceClient(settings=settings) as client:
        restaurants = scrape_district(
            1001,
            rows=20,
            max_pages=1,
            client=client,
        )
    write_records([r.to_dict() for r in restaurants], out)
    print(f"Wrote {len(restaurants)} restaurants -> {out}")
    return 0 if restaurants else 1


if __name__ == "__main__":
    raise SystemExit(main())
