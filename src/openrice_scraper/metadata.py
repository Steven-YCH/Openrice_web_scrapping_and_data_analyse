"""Fetch and export OpenRice region / district metadata."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from .client import OpenRiceClient
from .config import ScraperSettings
from .models import DistrictMeta, parse_districts
from .storage import write_records

logger = logging.getLogger(__name__)


def fetch_districts(
    client: Optional[OpenRiceClient] = None,
    settings: Optional[ScraperSettings] = None,
) -> list[DistrictMeta]:
    """Download district metadata from the public region API."""
    owns_client = client is None
    client = client or OpenRiceClient(settings=settings)
    try:
        payload = client.fetch_metadata()
        districts = parse_districts(payload)
        logger.info("Fetched %s districts from metadata API", len(districts))
        return districts
    finally:
        if owns_client:
            client.close()


def export_districts(
    out_path: str | Path,
    *,
    client: Optional[OpenRiceClient] = None,
    settings: Optional[ScraperSettings] = None,
) -> list[DistrictMeta]:
    """Fetch districts and write them to JSONL/CSV/SQLite based on suffix."""
    districts = fetch_districts(client=client, settings=settings)
    write_records([d.to_dict() for d in districts], out_path)
    return districts
