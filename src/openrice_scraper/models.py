"""Typed models and parsers for OpenRice API payloads."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class DistrictRef:
    district_id: Optional[int]
    name: Optional[str]
    search_key: Optional[str] = None

    @classmethod
    def from_api(cls, raw: Any) -> Optional["DistrictRef"]:
        if not isinstance(raw, dict):
            return None
        return cls(
            district_id=_as_int(raw.get("districtId")),
            name=_as_str(raw.get("name")),
            search_key=_as_str(raw.get("searchKey")),
        )


@dataclass(frozen=True)
class CategoryRef:
    category_id: Optional[int]
    name: Optional[str]
    category_type_id: Optional[int] = None
    search_key: Optional[str] = None

    @classmethod
    def from_api(cls, raw: Any) -> Optional["CategoryRef"]:
        if not isinstance(raw, dict):
            return None
        return cls(
            category_id=_as_int(raw.get("categoryId")),
            name=_as_str(raw.get("name")),
            category_type_id=_as_int(raw.get("categoryTypeId")),
            search_key=_as_str(raw.get("searchKey")),
        )


@dataclass
class Restaurant:
    """Normalized restaurant / POI record from search results."""

    poi_id: int
    name: Optional[str] = None
    name_other_lang: Optional[str] = None
    address: Optional[str] = None
    address_other_lang: Optional[str] = None
    map_latitude: Optional[float] = None
    map_longitude: Optional[float] = None
    score_overall: Optional[float] = None
    bookmarked_user_count: Optional[int] = None
    photo_count: Optional[int] = None
    review_count: Optional[int] = None
    score_smile: Optional[int] = None
    score_cry: Optional[int] = None
    price_range_id: Optional[int] = None
    district_id: Optional[int] = None
    district_name: Optional[str] = None
    categories: list[str] = field(default_factory=list)
    category_ids: list[int] = field(default_factory=list)
    shorten_url: Optional[str] = None

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> "Restaurant":
        if "poiId" not in raw:
            raise ValueError("search result missing required field poiId")

        district = DistrictRef.from_api(raw.get("district"))
        category_objs: list[CategoryRef] = []
        for item in raw.get("categories") or []:
            parsed = CategoryRef.from_api(item)
            if parsed is not None:
                category_objs.append(parsed)

        return cls(
            poi_id=int(raw["poiId"]),
            name=_as_str(raw.get("name")),
            name_other_lang=_as_str(raw.get("nameOtherLang")),
            address=_as_str(raw.get("address")),
            address_other_lang=_as_str(raw.get("addressOtherLang")),
            map_latitude=_as_float(raw.get("mapLatitude")),
            map_longitude=_as_float(raw.get("mapLongitude")),
            score_overall=_as_float(raw.get("scoreOverall")),
            bookmarked_user_count=_as_int(raw.get("bookmarkedUserCount")),
            photo_count=_as_int(raw.get("photoCount")),
            review_count=_as_int(raw.get("reviewCount")),
            score_smile=_as_int(raw.get("scoreSmile")),
            score_cry=_as_int(raw.get("scoreCry")),
            price_range_id=_as_int(raw.get("priceRangeId")),
            district_id=district.district_id if district else None,
            district_name=district.name if district else None,
            categories=[c.name for c in category_objs if c.name],
            category_ids=[c.category_id for c in category_objs if c.category_id is not None],
            shorten_url=_as_str(raw.get("shortenUrl")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DistrictMeta:
    district_id: int
    eng_name: Optional[str]
    zh_name: Optional[str]
    search_key: Optional[str]

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> "DistrictMeta":
        names = raw.get("nameLangDict") or {}
        return cls(
            district_id=int(raw["districtId"]),
            eng_name=_as_str(names.get("en")),
            zh_name=_as_str(names.get("tc-tw") or names.get("zh") or raw.get("name")),
            search_key=_as_str(raw.get("searchKey")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SearchPage:
    results: list[Restaurant]
    count: Optional[int] = None
    total_return_count: Optional[int] = None
    start_at: int = 0

    @property
    def returned(self) -> int:
        return len(self.results)


def parse_search_page(payload: dict[str, Any], *, start_at: int = 0) -> SearchPage:
    """Parse a search API response into Restaurant models."""
    pagination = payload.get("paginationResult") or {}
    raw_results = pagination.get("results") or []
    restaurants: list[Restaurant] = []
    for item in raw_results:
        if isinstance(item, dict) and item.get("poiId") is not None:
            restaurants.append(Restaurant.from_api(item))
    return SearchPage(
        results=restaurants,
        count=_as_int(pagination.get("count")),
        total_return_count=_as_int(pagination.get("totalReturnCount")),
        start_at=start_at,
    )


def parse_districts(payload: dict[str, Any]) -> list[DistrictMeta]:
    """Parse metadata/region/all districts list."""
    districts: list[DistrictMeta] = []
    for item in payload.get("districts") or []:
        if isinstance(item, dict) and item.get("districtId") is not None:
            districts.append(DistrictMeta.from_api(item))
    return districts


def dedupe_by_poi_id(items: Iterable[Restaurant]) -> list[Restaurant]:
    """Keep first occurrence of each poi_id."""
    seen: set[int] = set()
    out: list[Restaurant] = []
    for item in items:
        if item.poi_id in seen:
            continue
        seen.add(item.poi_id)
        out.append(item)
    return out


def _as_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
