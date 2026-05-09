import logging
import asyncio
import time

import httpx

from app.core.config import CONFIG
from app.downloader.cache import cache_path, is_fresh, read_json, write_json


LASTFM_API_URL = "https://ws.audioscrobbler.com/2.0/"
PLACEHOLDER_IMAGE_HASH = "2a96cbd8b46e442fc41c2b86b821562f"
_request_lock = asyncio.Lock()
_last_request_at = 0.0


def get_lastfm_config():
    return CONFIG.get("lastfm", {})


def is_enabled() -> bool:
    cfg = get_lastfm_config()
    return bool(cfg.get("enabled") and cfg.get("api_key"))


def _cache_ttl_days() -> int:
    return int(get_lastfm_config().get("cache_ttl_days", 365))


async def _rate_limit():
    global _last_request_at

    delay = float(get_lastfm_config().get("request_delay_seconds", 0.25))

    async with _request_lock:
        elapsed = time.monotonic() - _last_request_at
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        _last_request_at = time.monotonic()


async def _request(method: str, params: dict):
    cfg = get_lastfm_config()
    request_params = {
        "method": method,
        "api_key": cfg["api_key"],
        "format": "json",
        "autocorrect": 1,
        **{key: value for key, value in params.items() if value},
    }

    cache_key = f"{method}:{request_params}"
    path = cache_path("lastfm", cache_key, "json")

    if is_fresh(path, _cache_ttl_days()):
        return read_json(path)

    try:
        await _rate_limit()

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(LASTFM_API_URL, params=request_params)

        if response.status_code == 404:
            data = {}
        else:
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPError as exc:
        logging.warning("Last.fm %s request failed: %s", method, exc)
        return {}

    if data.get("error"):
        logging.warning(
            "Last.fm %s failed: %s - %s",
            method,
            data.get("error"),
            data.get("message"),
        )
        data = {}

    write_json(path, data)
    return data


def _tag_names(payload: dict, root_key: str) -> list[str]:
    tags = payload.get(root_key, {}).get("tag", [])

    if isinstance(tags, dict):
        tags = [tags]

    names = []
    for tag in tags:
        name = tag.get("name")
        if name:
            names.append(name)

    return names


def _track_info_tags(payload: dict) -> list[str]:
    tags_payload = {"toptags": payload.get("track", {}).get("toptags", {})}
    return _tag_names(tags_payload, "toptags")


def _artist_info_tags(payload: dict) -> list[str]:
    tags_payload = {"tags": payload.get("artist", {}).get("tags", {})}
    return _tag_names(tags_payload, "tags")


def _best_image_url(images: list[dict]) -> str | None:
    for image in reversed(images or []):
        url = image.get("#text")
        if url and PLACEHOLDER_IMAGE_HASH not in url:
            return url

    return None


async def enrich_with_lastfm(metadata: dict) -> dict:
    if not is_enabled():
        return metadata

    if not metadata.get("artist") or not metadata.get("title"):
        return metadata

    limit = int(get_lastfm_config().get("top_tags_limit", 5))

    track_params = {
        "artist": metadata.get("artist"),
        "track": metadata.get("title"),
        "mbid": metadata.get("musicbrainz_recording_id"),
    }
    artist_params = {
        "artist": metadata.get("artist"),
        "mbid": metadata.get("musicbrainz_artist_id"),
    }

    track_info = await _request("track.getInfo", track_params)
    track_tags = _track_info_tags(track_info)

    if not track_tags:
        top_tags = await _request("track.getTopTags", track_params)
        track_tags = _tag_names(top_tags, "toptags")

    artist_info = await _request("artist.getInfo", artist_params)
    artist_tags = _artist_info_tags(artist_info)

    genres = []
    for tag in [*track_tags, *artist_tags]:
        normalized = tag.strip()
        if normalized and normalized.lower() not in {g.lower() for g in genres}:
            genres.append(normalized)
        if len(genres) >= limit:
            break

    if genres:
        metadata["genres"] = genres

    track = track_info.get("track", {})
    if track.get("url"):
        metadata["lastfm_url"] = track["url"]

    artist = artist_info.get("artist", {})
    artist_artwork_url = _best_image_url(artist.get("image", []))
    if artist_artwork_url:
        metadata["artist_artwork_url"] = artist_artwork_url

    return metadata
