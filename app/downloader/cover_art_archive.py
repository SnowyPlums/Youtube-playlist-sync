from app.core.config import CONFIG


def is_enabled() -> bool:
    return bool(CONFIG.get("cover_art_archive", {}).get("enabled", True))


def cache_ttl_days() -> int:
    return int(CONFIG.get("cover_art_archive", {}).get("cache_ttl_days", 3650))


def cover_art_url(release_id: str | None) -> str | None:
    if not is_enabled() or not release_id:
        return None

    return f"https://coverartarchive.org/release/{release_id}/front-500"
