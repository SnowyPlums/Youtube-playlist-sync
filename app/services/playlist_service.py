from pathlib import Path
import logging

from app.core.database import get_db
from app.downloader.yt_dlp_client import extract_info
from app.services.song_service import download_song
from app.utils.filesystem import (
    build_playlist_path,
    build_server_song_path
)


async def sync_playlist(url: str):
    logging.info(f"Starting playlist sync: {url}")

    info = extract_info(url)

    playlist_title = info["title"]
    playlist_id = info["id"]

    logging.info(
        f"Resolved playlist: {playlist_title} ({playlist_id})"
    )

    playlist_path = build_playlist_path(playlist_title)

    db = await get_db()

    try:
        await db.execute(
            """
            INSERT OR IGNORE INTO playlists (
                youtube_playlist_id,
                title,
                m3u_path
            ) VALUES (?, ?, ?)
            """,
            (
                playlist_id,
                playlist_title,
                str(playlist_path)
            )
        )

        await db.commit()

        playlist_cursor = await db.execute(
            "SELECT id FROM playlists WHERE youtube_playlist_id = ?",
            (playlist_id,)
        )

        playlist_row = await playlist_cursor.fetchone()

        internal_playlist_id = playlist_row["id"]

        tracks = []

        total_entries = len(info["entries"])

        logging.info(f"Playlist contains {total_entries} entries")

        for position, entry in enumerate(info["entries"]):
            if not entry:
                continue

            logging.info(
                f"Processing track {position + 1}/{total_entries}: {entry['title']}"
            )

            video_url = f"https://www.youtube.com/watch?v={entry['id']}"

            filepath = await download_song(video_url)

            song_cursor = await db.execute(
                "SELECT id FROM songs WHERE youtube_id = ?",
                (entry["id"],)
            )

            song_row = await song_cursor.fetchone()

            await db.execute(
                """
                INSERT OR REPLACE INTO playlist_songs (
                    playlist_id,
                    song_id,
                    position
                ) VALUES (?, ?, ?)
                """,
                (
                    internal_playlist_id,
                    song_row["id"],
                    position
                )
            )

            await db.commit()

            tracks.append(filepath)

        logging.info("Regenerating M3U playlist")

        playlist_path.parent.mkdir(parents=True, exist_ok=True)

        with open(playlist_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")

            for track in tracks:
                server_track_path = build_server_song_path(track)
                f.write(f"{server_track_path}\n")


        logging.info(
            f"Finished playlist sync: {playlist_title} ({len(tracks)} tracks)"
        )

        return {
            "playlist": playlist_title,
            "songs": len(tracks)
        }

    finally:
        await db.close()