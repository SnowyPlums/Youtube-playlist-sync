from mutagen.oggopus import OggOpus
from mutagen.flac import Picture
from mutagen.mp3 import MP3
from mutagen.id3 import APIC, TALB, TCON, TDRC, TIT2, TPE1, TXXX

from pathlib import Path
import base64
import logging


def write_tags(filepath, metadata, cover_path=None):
    suffix = Path(filepath).suffix.lower()

    if suffix == ".mp3":
        return write_mp3_tags(filepath, metadata, cover_path)

    if suffix not in {".opus", ".ogg"}:
        logging.warning("Tag writing is not supported for %s files", suffix)
        return

    return write_ogg_tags(filepath, metadata, cover_path)


def write_ogg_tags(filepath, metadata, cover_path=None):
    audio = OggOpus(filepath)

    audio["TITLE"] = metadata["title"]
    audio["ARTIST"] = metadata["artist"]
    audio["ALBUM"] = metadata["album"]

    audio["YOUTUBE_ID"] = metadata["youtube_id"]

    if metadata.get("album_date"):
        audio["DATE"] = metadata["album_date"]

    if metadata.get("genres"):
        audio["GENRE"] = metadata["genres"]

    if metadata.get("lastfm_url"):
        audio["LASTFM_URL"] = metadata["lastfm_url"]

    if metadata.get("musicbrainz_recording_id"):
        audio["MUSICBRAINZ_TRACKID"] = metadata["musicbrainz_recording_id"]

    if metadata.get("musicbrainz_release_id"):
        audio["MUSICBRAINZ_ALBUMID"] = metadata["musicbrainz_release_id"]

    if metadata.get("musicbrainz_artist_id"):
        audio["MUSICBRAINZ_ARTISTID"] = metadata["musicbrainz_artist_id"]

    # Embed cover art into opus
    if cover_path and Path(cover_path).exists():
        picture = Picture()
        picture.type = 3
        picture.mime = "image/jpeg"
        picture.desc = "Cover"

        picture.data = Path(cover_path).read_bytes()

        encoded = base64.b64encode(
            picture.write()
        ).decode("ascii")

        audio["METADATA_BLOCK_PICTURE"] = [encoded]

    audio.save()


def write_mp3_tags(filepath, metadata, cover_path=None):
    audio = MP3(filepath)

    if audio.tags is None:
        audio.add_tags()

    tags = audio.tags

    tags.setall("TIT2", [TIT2(encoding=3, text=metadata["title"])])
    tags.setall("TPE1", [TPE1(encoding=3, text=metadata["artist"])])
    tags.setall("TALB", [TALB(encoding=3, text=metadata["album"])])

    if metadata.get("album_date"):
        tags.setall("TDRC", [TDRC(encoding=3, text=metadata["album_date"])])

    if metadata.get("genres"):
        tags.setall("TCON", [TCON(encoding=3, text=metadata["genres"])])

    tags.setall(
        "TXXX:YOUTUBE_ID",
        [TXXX(encoding=3, desc="YOUTUBE_ID", text=metadata["youtube_id"])],
    )

    optional_text_tags = {
        "LASTFM_URL": metadata.get("lastfm_url"),
        "MUSICBRAINZ_TRACKID": metadata.get("musicbrainz_recording_id"),
        "MUSICBRAINZ_ALBUMID": metadata.get("musicbrainz_release_id"),
        "MUSICBRAINZ_ARTISTID": metadata.get("musicbrainz_artist_id"),
    }

    for description, value in optional_text_tags.items():
        if value:
            tags.setall(
                f"TXXX:{description}",
                [TXXX(encoding=3, desc=description, text=value)],
            )

    if cover_path and Path(cover_path).exists():
        tags.setall(
            "APIC",
            [
                APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,
                    desc="Cover",
                    data=Path(cover_path).read_bytes(),
                )
            ],
        )

    audio.save(v2_version=3)
