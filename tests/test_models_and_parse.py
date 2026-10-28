"""Unit tests for parsers / storage — fixture JSON only, no live network."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from openrice_scraper.models import (
    Restaurant,
    dedupe_by_poi_id,
    parse_districts,
    parse_search_page,
)
from openrice_scraper.storage import read_jsonl, write_records

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "sample_search_result.json"


@pytest.fixture(scope="module")
def sample_payload() -> dict:
    with FIXTURE.open(encoding="utf-8") as handle:
        return json.load(handle)


def test_fixture_exists() -> None:
    assert FIXTURE.is_file()


def test_parse_search_page(sample_payload: dict) -> None:
    page = parse_search_page(sample_payload, start_at=0)
    assert page.returned >= 1
    first = page.results[0]
    assert isinstance(first, Restaurant)
    assert first.poi_id > 0
    assert first.name
    assert first.district_id == 1001
    assert isinstance(first.categories, list)


def test_restaurant_to_dict_roundtrip(sample_payload: dict) -> None:
    page = parse_search_page(sample_payload)
    row = page.results[0].to_dict()
    assert row["poi_id"] == page.results[0].poi_id
    assert "categories" in row
    assert "shorten_url" in row


def test_dedupe_by_poi_id(sample_payload: dict) -> None:
    page = parse_search_page(sample_payload)
    doubled = page.results + page.results
    unique = dedupe_by_poi_id(doubled)
    assert len(unique) == len(page.results)
    assert len({r.poi_id for r in unique}) == len(unique)


def test_parse_districts_minimal() -> None:
    payload = {
        "districts": [
            {
                "districtId": 1001,
                "searchKey": "districtId=1001",
                "nameLangDict": {"en": "Sheung Wan", "tc-tw": "上環"},
            }
        ]
    }
    districts = parse_districts(payload)
    assert len(districts) == 1
    assert districts[0].district_id == 1001
    assert districts[0].eng_name == "Sheung Wan"
    assert districts[0].zh_name == "上環"


def test_write_jsonl_and_csv(tmp_path: Path, sample_payload: dict) -> None:
    records = [r.to_dict() for r in parse_search_page(sample_payload).results]
    jsonl_path = tmp_path / "out.jsonl"
    csv_path = tmp_path / "out.csv"

    write_records(records, jsonl_path)
    write_records(records, csv_path)

    loaded = read_jsonl(jsonl_path)
    assert len(loaded) == len(records)
    assert loaded[0]["poi_id"] == records[0]["poi_id"]
    assert csv_path.read_text(encoding="utf-8").splitlines()[0].startswith("poi_id")


def test_write_sqlite(tmp_path: Path, sample_payload: dict) -> None:
    records = [r.to_dict() for r in parse_search_page(sample_payload).results]
    db_path = tmp_path / "out.sqlite"
    write_records(records, db_path)

    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0]
        assert count == len(records)
    finally:
        conn.close()


def test_missing_poi_id_raises() -> None:
    with pytest.raises(ValueError):
        Restaurant.from_api({"name": "no id"})
