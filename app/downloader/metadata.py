from app.downloader.musicbrainz import search_recording


async def enrich_metadata(info: dict):
    title = info.get("track") or info.get("title")
    artist = info.get("artist") or info.get("uploader")

    # Unknown albums become Singles
    album = info.get("album") or "Singles"

    duration = info.get("duration")

    result = search_recording(artist, title, duration)

    if not result:
        return {
            "source": "youtube",
            "title": title,
            "artist": artist,
            "album": album,
            "duration": duration,
            "youtube_id": info["id"],
            "thumbnail": info.get("thumbnail")
        }

    recording = result.data

    release = None
    if recording.get("release-list"):
        release = recording["release-list"][0]

    return {
        "source": "musicbrainz",
        "title": recording.get("title"),
        "artist": recording["artist-credit"][0]["artist"]["name"],
        "album": release["title"] if release else album,
        "duration": duration,
        "youtube_id": info["id"],
        "thumbnail": info.get("thumbnail"),
        "musicbrainz_recording_id": recording.get("id"),
        "musicbrainz_release_id": release.get("id") if release else None,
        "musicbrainz_artist_id": recording["artist-credit"][0]["artist"].get("id")
    }