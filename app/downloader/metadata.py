import logging

from app.downloader.musicbrainz import search_recording
from app.downloader.lastfm import enrich_with_lastfm


async def _safe_lastfm_enrich(metadata: dict) -> dict:
    try:
        return await enrich_with_lastfm(metadata)
    except Exception:
        logging.exception(
            "Last.fm enrichment failed for %s - %s",
            metadata.get("artist"),
            metadata.get("title"),
        )
        return metadata


async def enrich_metadata(info: dict):
    title = info.get("track") or info.get("title")
    artist = info.get("artist") or info.get("uploader")

    # Unknown albums become Singles
    album = info.get("album") or "Singles"

    duration = info.get("duration")

    try:
        result = search_recording(artist, title, duration)
    except Exception:
        logging.exception(
            "MusicBrainz lookup failed for %s - %s",
            artist,
            title,
        )
        result = None

    if not result:
        metadata = {
            "source": "youtube",
            "title": title,
            "artist": artist,
            "album": album,
            "duration": duration,
            "youtube_id": info["id"],
            "thumbnail": info.get("thumbnail")
        }
        return await _safe_lastfm_enrich(metadata)

    recording = result.data

    release = None
    if recording.get("release-list"):
        release = recording["release-list"][0]

    release_date = release.get("date") if release else None

    metadata = {
        "source": "musicbrainz",
        "title": recording.get("title"),
        "artist": recording["artist-credit"][0]["artist"]["name"],
        "album": release["title"] if release else album,
        "album_date": release_date,
        "album_year": int(release_date[:4]) if release_date and release_date[:4].isdigit() else None,
        "duration": duration,
        "youtube_id": info["id"],
        "thumbnail": info.get("thumbnail"),
        "musicbrainz_recording_id": recording.get("id"),
        "musicbrainz_release_id": release.get("id") if release else None,
        "musicbrainz_artist_id": recording["artist-credit"][0]["artist"].get("id")
    }

    return await _safe_lastfm_enrich(metadata)
