"""Persist scraped records to JSONL, CSV, or SQLite (no MySQL passwords)."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Sequence


SUPPORTED_SUFFIXES = {".jsonl", ".json", ".csv", ".sqlite", ".db", ".parquet"}


def write_records(records: Sequence[dict[str, Any]], out_path: str | Path) -> Path:
    """Write records based on file extension."""
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()

    if suffix in {".jsonl", ".json"}:
        _write_jsonl(records, path)
    elif suffix == ".csv":
        _write_csv(records, path)
    elif suffix in {".sqlite", ".db"}:
        _write_sqlite(records, path)
    elif suffix == ".parquet":
        _write_parquet(records, path)
    else:
        raise ValueError(
            f"Unsupported output format '{suffix}'. "
            f"Use one of: {sorted(SUPPORTED_SUFFIXES)}"
        )
    return path


def _write_jsonl(records: Sequence[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in records:
            handle.write(json.dumps(_jsonable(row), ensure_ascii=False) + "\n")


def _write_csv(records: Sequence[dict[str, Any]], path: Path) -> None:
    if not records:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(records[0].keys())
    for row in records[1:]:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in records:
            writer.writerow({k: _csv_cell(row.get(k)) for k in fieldnames})


def _write_sqlite(records: Sequence[dict[str, Any]], path: Path) -> None:
    """Store each record as JSON. Use restaurants table when poi_id is present."""
    conn = sqlite3.connect(path)
    try:
        has_poi = bool(records) and all("poi_id" in row for row in records)
        if has_poi:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS restaurants (
                    poi_id INTEGER PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute("DELETE FROM restaurants")
            conn.executemany(
                "INSERT OR REPLACE INTO restaurants (poi_id, payload) VALUES (?, ?)",
                [
                    (int(row["poi_id"]), json.dumps(_jsonable(row), ensure_ascii=False))
                    for row in records
                ],
            )
        else:
            conn.execute("DROP TABLE IF EXISTS records")
            conn.execute(
                """
                CREATE TABLE records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.executemany(
                "INSERT INTO records (payload) VALUES (?)",
                [(json.dumps(_jsonable(row), ensure_ascii=False),) for row in records],
            )
        conn.commit()
    finally:
        conn.close()


def _write_parquet(records: Sequence[dict[str, Any]], path: Path) -> None:
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise ImportError(
            "Writing parquet requires pandas (and a parquet engine). "
            "Default formats are JSONL/CSV/SQLite. For Parquet, install pandas "
            "plus a pyarrow binary wheel (avoid source builds on unsupported Pythons) "
            "via: pip install -e '.[parquet]'"
        ) from exc

    flat = [_flatten_for_tabular(row) for row in records]
    pd.DataFrame(flat).to_parquet(path, index=False)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _csv_cell(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return value


def _flatten_for_tabular(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, (list, dict)):
            out[key] = json.dumps(value, ensure_ascii=False)
        else:
            out[key] = value
    return out


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load JSONL records (helper for analysis scripts)."""
    records: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def append_jsonl(records: Iterable[dict[str, Any]], path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as handle:
        for row in records:
            handle.write(json.dumps(_jsonable(row), ensure_ascii=False) + "\n")
    return out
