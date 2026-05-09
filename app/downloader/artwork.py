from pathlib import Path
import logging
import httpx

from app.downloader.cache import cache_path, is_fresh


async def download_artwork(
    url: str | None,
    output_path: Path,
    cache_key: str | None = None,
    ttl_days: int = 3650,
) -> bool:
    if not url:
        return False

    cached_path = cache_path("artwork", cache_key or url, "jpg")
    failure_path = cache_path("artwork", f"failure:{cache_key or url}", "txt")

    if is_fresh(cached_path, ttl_days):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(cached_path.read_bytes())
        return True

    if is_fresh(failure_path, ttl_days):
        return False

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True, timeout=30)

        if response.status_code == 404:
            failure_path.parent.mkdir(parents=True, exist_ok=True)
            failure_path.write_text("404", encoding="utf-8")
            return False

        response.raise_for_status()

    except httpx.HTTPError as exc:
        logging.warning("Artwork download failed for %s: %s", url, exc)
        return False

    cached_path.parent.mkdir(parents=True, exist_ok=True)
    cached_path.write_bytes(response.content)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    return True
