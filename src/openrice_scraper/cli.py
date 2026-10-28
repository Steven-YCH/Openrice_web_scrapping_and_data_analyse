"""Command-line interface for OpenRice metadata + search scraping."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .client import OpenRiceClient
from .config import DEFAULT_DELAY_SECONDS, DEFAULT_ROWS, ScraperSettings
from .metadata import export_districts
from .search import scrape_district
from .storage import write_records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openrice-scraper",
        description=(
            "Scrape Hong Kong restaurant listings from OpenRice public JSON APIs "
            "(portfolio / educational use)."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help=f"Seconds between requests (default: {DEFAULT_DELAY_SECONDS})",
    )
    parser.add_argument(
        "--ui-lang",
        default="zh",
        help="uiLang query param (default: zh)",
    )
    parser.add_argument(
        "--ui-city",
        default="hongkong",
        help="uiCity query param (default: hongkong)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    meta = sub.add_parser("metadata", help="Download district metadata")
    meta.add_argument(
        "--out",
        default="data/processed/districts.jsonl",
        help="Output path (.jsonl/.csv/.sqlite)",
    )

    scrape = sub.add_parser("scrape", help="Scrape restaurants for a district")
    scrape.add_argument(
        "--district-id",
        type=int,
        required=True,
        help="OpenRice districtId (e.g. 1001 for Sheung Wan)",
    )
    scrape.add_argument(
        "--rows",
        type=int,
        default=DEFAULT_ROWS,
        help=f"Page size / rows per request (default: {DEFAULT_ROWS})",
    )
    scrape.add_argument(
        "--max-pages",
        type=int,
        default=1,
        help="Maximum pages to fetch (default: 1). Use 0 for no cap.",
    )
    scrape.add_argument(
        "--out",
        default="data/processed/restaurants.jsonl",
        help="Output path (.jsonl/.csv/.sqlite/.parquet)",
    )

    return parser


def _settings_from_args(args: argparse.Namespace) -> ScraperSettings:
    return ScraperSettings(
        ui_lang=args.ui_lang,
        ui_city=args.ui_city,
        delay_seconds=args.delay,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    settings = _settings_from_args(args)
    out = Path(args.out)

    if args.command == "metadata":
        with OpenRiceClient(settings=settings) as client:
            districts = export_districts(out, client=client)
        print(f"Wrote {len(districts)} districts -> {out}")
        return 0

    if args.command == "scrape":
        max_pages = None if args.max_pages == 0 else args.max_pages
        with OpenRiceClient(settings=settings) as client:
            restaurants = scrape_district(
                args.district_id,
                rows=args.rows,
                max_pages=max_pages,
                client=client,
            )
        write_records([r.to_dict() for r in restaurants], out)
        print(f"Wrote {len(restaurants)} restaurants -> {out}")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
