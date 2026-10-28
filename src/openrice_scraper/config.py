"""Configuration defaults for the OpenRice scraper."""

from __future__ import annotations

from dataclasses import dataclass


BASE_URL = "https://www.openrice.com"
METADATA_PATH = "/api/v2/metadata/region/all"
SEARCH_PATH = "/api/v2/search"

DEFAULT_UI_LANG = "zh"
DEFAULT_UI_CITY = "hongkong"
DEFAULT_ROWS = 20
DEFAULT_DELAY_SECONDS = 1.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_USER_AGENT = (
    "OpenRiceScraper/0.1 (+https://github.com/Steven-YCH/"
    "Openrice_web_scrapping_and_data_analyse)"
)


@dataclass(frozen=True)
class ScraperSettings:
    """Runtime settings shared by metadata and search clients."""

    ui_lang: str = DEFAULT_UI_LANG
    ui_city: str = DEFAULT_UI_CITY
    delay_seconds: float = DEFAULT_DELAY_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    user_agent: str = DEFAULT_USER_AGENT
    base_url: str = BASE_URL
