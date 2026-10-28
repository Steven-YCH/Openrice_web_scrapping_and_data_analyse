"""Paginated OpenRice search scraping with poiId deduplication."""

from __future__ import annotations

import logging
from typing import Iterator, Optional

from .client import OpenRiceClient
from .config import DEFAULT_ROWS, ScraperSettings
from .models import Restaurant, dedupe_by_poi_id, parse_search_page

logger = logging.getLogger(__name__)


def iter_search_pages(
    client: OpenRiceClient,
    *,
    district_id: int,
    rows: int = DEFAULT_ROWS,
    max_pages: Optional[int] = None,
    start_at: int = 0,
) -> Iterator[list[Restaurant]]:
    """Yield pages of Restaurant results using startAt pagination."""
    if rows <= 0:
        raise ValueError("rows must be > 0")
    if max_pages is not None and max_pages <= 0:
        return

    offset = start_at
    page_idx = 0
    while True:
        if max_pages is not None and page_idx >= max_pages:
            break

        payload = client.fetch_search(
            district_id=district_id,
            start_at=offset,
            rows=rows,
        )
        page = parse_search_page(payload, start_at=offset)
        logger.info(
            "district=%s page=%s startAt=%s returned=%s total_hint=%s",
            district_id,
            page_idx + 1,
            offset,
            page.returned,
            page.count,
        )
        if page.returned == 0:
            break

        yield page.results
        page_idx += 1
        offset += rows

        # Stop when API reports we have exhausted known results.
        if page.count is not None and offset >= page.count:
            break
        if page.returned < rows:
            break


def scrape_district(
    district_id: int,
    *,
    rows: int = DEFAULT_ROWS,
    max_pages: Optional[int] = 1,
    client: Optional[OpenRiceClient] = None,
    settings: Optional[ScraperSettings] = None,
) -> list[Restaurant]:
    """Scrape one district with optional page cap; dedupe by poiId."""
    owns_client = client is None
    client = client or OpenRiceClient(settings=settings)
    try:
        collected: list[Restaurant] = []
        for page in iter_search_pages(
            client,
            district_id=district_id,
            rows=rows,
            max_pages=max_pages,
        ):
            collected.extend(page)
        unique = dedupe_by_poi_id(collected)
        logger.info(
            "district=%s scraped=%s unique=%s",
            district_id,
            len(collected),
            len(unique),
        )
        return unique
    finally:
        if owns_client:
            client.close()
