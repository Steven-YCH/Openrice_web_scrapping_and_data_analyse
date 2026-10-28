"""HTTP client with session, retries, and polite delay."""

from __future__ import annotations

import logging
import time
from typing import Any, Mapping, MutableMapping, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import METADATA_PATH, SEARCH_PATH, ScraperSettings

logger = logging.getLogger(__name__)


class OpenRiceClient:
    """Thin wrapper around requests.Session for OpenRice JSON APIs."""

    def __init__(self, settings: Optional[ScraperSettings] = None) -> None:
        self.settings = settings or ScraperSettings()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.settings.user_agent,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
            }
        )
        retry = Retry(
            total=self.settings.max_retries,
            connect=self.settings.max_retries,
            read=self.settings.max_retries,
            status=self.settings.max_retries,
            backoff_factor=0.8,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self._last_request_at: float = 0.0

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "OpenRiceClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _throttle(self) -> None:
        delay = float(self.settings.delay_seconds)
        if delay <= 0:
            return
        elapsed = time.monotonic() - self._last_request_at
        remaining = delay - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def get_json(
        self,
        path: str,
        params: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        """GET a JSON endpoint under the configured base URL."""
        self._throttle()
        url = urljoin(self.settings.base_url.rstrip("/") + "/", path.lstrip("/"))
        logger.debug("GET %s params=%s", url, dict(params or {}))
        response = self.session.get(
            url,
            params=dict(params or {}),
            timeout=self.settings.timeout_seconds,
        )
        self._last_request_at = time.monotonic()
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object from {url}, got {type(payload).__name__}")
        return payload

    def fetch_metadata(self, extra_params: Optional[MutableMapping[str, Any]] = None) -> dict[str, Any]:
        params: dict[str, Any] = {
            "uiLang": self.settings.ui_lang,
            "uiCity": self.settings.ui_city,
        }
        if extra_params:
            params.update(extra_params)
        return self.get_json(METADATA_PATH, params=params)

    def fetch_search(
        self,
        *,
        district_id: int,
        start_at: int = 0,
        rows: int = 20,
        extra_params: Optional[MutableMapping[str, Any]] = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "uiLang": self.settings.ui_lang,
            "uiCity": self.settings.ui_city,
            "startAt": start_at,
            "rows": rows,
            "districtId": district_id,
        }
        if extra_params:
            params.update(extra_params)
        return self.get_json(SEARCH_PATH, params=params)
