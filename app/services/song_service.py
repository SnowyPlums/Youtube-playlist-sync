from pathlib import Path
import logging

from app.core.database import get_db
from app.downloader.yt_dlp_client import extract_info, download_audio
from app.downloader.metadata import enrich_metadata
from app.downloader.tagging import write_tags
from app.downloader.artwork import download_artwork
from app.downloader.cover_art_archive import cover_art_url, cache_ttl_days
from app.utils.filesystem import build_song_path
from app.core.config import CONFIG


async def song_exists(youtube_id: str):
    db = await get_db()

    try:
        cursor = await db.execute(
            "SELECT * FROM songs WHERE youtube_id = ?",
            (youtube_id,)
        )

        row = await cursor.fetchone()

        return row

    finally:
        await db.close()
        

async def download_song(url: str):
    logging.info(f"Extracting metadata for: {url}")

    info = extract_info(url)

    youtube_id = info["id"]

    existing = await song_exists(youtube_id)

    if existing:
        logging.info(
            f"Song already exists, skipping download: {existing['filepath']}"
        )
        return existing["filepath"]

    logging.info("Enriching metadata using MusicBrainz")

    metadata = await enrich_metadata(info)

    logging.info(
        f"Resolved metadata: {metadata['artist']} - {metadata['title']}"
    )

    song_path = build_song_path(
        metadata["artist"],
        metadata["album"],
        metadata["title"]
    )

    song_path.parent.mkdir(parents=True, exist_ok=True)

    logging.info(f"Downloading audio to: {song_path}")

    download_audio(url, song_path)

    logging.info("Writing metadata tags")

    cover_path = song_path.parent / "cover.jpg"
    metadata["cover_art_url"] = cover_art_url(
        metadata.get("musicbrainz_release_id")
    )

    if not cover_path.exists():
        logging.info("Downloading album artwork")

        downloaded_cover = await download_artwork(
            metadata.get("cover_art_url"),
            cover_path,
            cache_key=f"cover:{metadata.get('musicbrainz_release_id')}",
            ttl_days=cache_ttl_days()
        )

        if not downloaded_cover:
            metadata["cover_art_url"] = metadata.get("thumbnail")
            await download_artwork(
                metadata.get("thumbnail"),
                cover_path,
                cache_key=f"youtube-thumbnail:{youtube_id}"
            )

    if (
        CONFIG.get("lastfm", {}).get("download_artist_artwork", True)
        and metadata.get("artist_artwork_url")
    ):
        artist_artwork_path = song_path.parent.parent / "artist.jpg"

        if not artist_artwork_path.exists():
            logging.info("Downloading artist artwork")
            await download_artwork(
                metadata.get("artist_artwork_url"),
                artist_artwork_path,
                cache_key=f"artist:{metadata.get('musicbrainz_artist_id') or metadata['artist']}"
            )

    logging.info("Writing metadata tags")

    write_tags(song_path, metadata, cover_path)

    db = await get_db()

    try:
        logging.info("Saving song to database")

        await db.execute(
            """
            INSERT INTO songs (
                youtube_id,
                title,
                artist,
                album,
                album_date,
                album_year,
                genres,
                duration,
                filepath,
                thumbnail_url,
                cover_art_url,
                artist_artwork_url,
                metadata_source,
                lastfm_url,
                musicbrainz_recording_id,
                musicbrainz_release_id,
                musicbrainz_artist_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                youtube_id,
                metadata["title"],
                metadata["artist"],
                metadata["album"],
                metadata.get("album_date"),
                metadata.get("album_year"),
                ", ".join(metadata.get("genres", [])),
                metadata["duration"],
                str(song_path),
                metadata.get("thumbnail"),
                metadata.get("cover_art_url"),
                metadata.get("artist_artwork_url"),
                metadata["source"],
                metadata.get("lastfm_url"),
                metadata.get("musicbrainz_recording_id"),
                metadata.get("musicbrainz_release_id"),
                metadata.get("musicbrainz_artist_id")
            )
        )

        await db.commit()

    finally:
        await db.close()

    logging.info(
        f"Finished processing: {metadata['artist']} - {metadata['title']}"
    )

    return str(song_path)
