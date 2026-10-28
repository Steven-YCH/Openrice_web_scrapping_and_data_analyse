# OpenRice Restaurant Scraper

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

Scrape Hong Kong restaurant listings from OpenRice public JSON APIs and save them as JSONL, CSV, or SQLite (Parquet optional).

## How it works

Instead of parsing HTML pages, this project calls the same JSON endpoints the website uses:

1. **Metadata** — districts / regions  
   `GET https://www.openrice.com/api/v2/metadata/region/all?uiLang=zh&uiCity=hongkong`
2. **Search** — paginated POIs for a district  
   `GET https://www.openrice.com/api/v2/search?uiLang=zh&uiCity=hongkong&startAt=0&rows=N&districtId=XXXX`  
   Results live under `paginationResult.results[]`.

```text
cli.py ──► client.py ──► OpenRice JSON APIs
              │
              ▼
         models.py (Restaurant, DistrictMeta)
              │
              ▼
         storage.py ──► data/processed/*.{jsonl,csv,sqlite} (+ optional parquet)
```

Requests use a shared session with retries and a configurable delay between calls. Search results are deduplicated by `poiId`.

## Project layout

```text
src/openrice_scraper/     # installable package
  client.py               # requests.Session, retries, delay
  metadata.py             # region/district fetch
  search.py               # startAt pagination + poiId dedupe
  models.py               # dataclasses + parsers
  storage.py              # JSONL / CSV / SQLite / Parquet writers
  cli.py                  # console entrypoint
scripts/scrape_sample.py  # small demo scrape
analysis/                 # lightweight summaries
tests/                    # fixture-based unit tests (no network)
fixtures/                 # sample search JSON for tests
data/samples/             # sample CSV/Parquet extracts
archive/legacy/           # older notebooks / SQL / ML materials
```

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -U pip
# Core + tests (recommended). Default outputs: JSONL / CSV / SQLite.
pip install -e ".[dev]"
# Optional tabular helpers:
#   pip install -e ".[analysis]"
# Optional Parquet (needs a pyarrow wheel for your Python):
#   pip install -e ".[parquet]"
```

Requires Python 3.10+.

## Usage

### District metadata

```bash
python -m openrice_scraper.cli metadata
# or after install:
openrice-scraper metadata --out data/processed/districts.jsonl
```

### Scrape one district

```bash
python -m openrice_scraper.cli scrape \
  --district-id 1001 \
  --rows 20 \
  --max-pages 1 \
  --out data/processed/sample.jsonl
```

Useful flags:

- `--delay 1.0` — seconds between HTTP calls (default `1.0`)
- `--max-pages 0` — no page cap
- `--out path.csv` / `.sqlite` — choose storage format; `.parquet` needs optional pandas+pyarrow
- `-v` — debug logging

Shortcut demo:

```bash
python scripts/scrape_sample.py
python analysis/summarize_sample.py data/processed/sample.jsonl
```

### Tests

```bash
pytest -q
```

## Sample output fields

| Field | Source API key | Notes |
| --- | --- | --- |
| `poi_id` | `poiId` | Deduplication key |
| `name` / `name_other_lang` | `name` / `nameOtherLang` | Chinese / other-language labels |
| `address` / `address_other_lang` | `address` / `addressOtherLang` | |
| `map_latitude` / `map_longitude` | `mapLatitude` / `mapLongitude` | |
| `score_overall` | `scoreOverall` | Overall score |
| `bookmarked_user_count` | `bookmarkedUserCount` | Popularity proxy |
| `photo_count` / `review_count` | `photoCount` / `reviewCount` | |
| `score_smile` / `score_cry` | `scoreSmile` / `scoreCry` | Sentiment tallies |
| `price_range_id` | `priceRangeId` | Price bucket id |
| `district_id` / `district_name` | `district.*` | |
| `categories` / `category_ids` | `categories[]` | Cuisine / dish labels |
| `shorten_url` | `shortenUrl` | Relative listing URL |

Example JSONL line (truncated):

```json
{"poi_id": 123456, "name": "…", "district_id": 1001, "bookmarked_user_count": 1200, "categories": ["日本菜", "壽司/刺身"]}
```

## Legacy materials

Older notebooks, SQL ETL, Excel reports, and an XGBoost model JSON are under [`archive/legacy/`](archive/legacy/). Sample historical extracts live in [`data/samples/`](data/samples/).
