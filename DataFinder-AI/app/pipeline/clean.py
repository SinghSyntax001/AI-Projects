import logging
from collections.abc import Iterable


logger = logging.getLogger("datafinder.pipeline.clean")


def _normalize_whitespace(value: str | None) -> str:
    return " ".join((value or "").split())


def normalize_tags(tags: Iterable[str] | str | None) -> list[str]:
    if tags is None:
        return []
    if isinstance(tags, str):
        raw_tags = tags.replace("|", ",").split(",")
    else:
        raw_tags = list(tags)

    normalized: list[str] = []
    for tag in raw_tags:
        clean_tag = _normalize_whitespace(str(tag)).lower()
        if clean_tag and clean_tag not in normalized:
            normalized.append(clean_tag)
    return normalized


def remove_null_fields(item: dict) -> dict:
    return {key: value for key, value in item.items() if value not in (None, "", [], {})}


def remove_duplicates(items: list[dict]) -> list[dict]:
    seen_urls: set[str] = set()
    unique_items: list[dict] = []

    for item in items:
        url = item.get("url")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        unique_items.append(item)

    return unique_items


def clean_datasets(items: list[dict]) -> list[dict]:
    cleaned: list[dict] = []
    for item in remove_duplicates(items):
        normalized = {
            "name": _normalize_whitespace(item.get("name") or item.get("title")),
            "description": _normalize_whitespace(item.get("description")),
            "source": _normalize_whitespace(item.get("source")),
            "tags": normalize_tags(item.get("tags")),
            "url": _normalize_whitespace(item.get("url")),
            "size": _normalize_whitespace(item.get("size")) or "unknown",
        }
        cleaned.append(remove_null_fields(normalized))
    logger.info("cleaned dataset metadata", extra={"event_data": {"input_count": len(items), "output_count": len(cleaned)}})
    return cleaned
