from mutagen.oggopus import OggOpus
from mutagen.flac import Picture

from pathlib import Path
import base64


def write_tags(filepath, metadata, cover_path=None):
    audio = OggOpus(filepath)

    audio["TITLE"] = metadata["title"]
    audio["ARTIST"] = metadata["artist"]
    audio["ALBUM"] = metadata["album"]

    audio["YOUTUBE_ID"] = metadata["youtube_id"]

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