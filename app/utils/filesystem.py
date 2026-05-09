from pathlib import Path

from app.utils.sanitizer import sanitize_filename
from app.core.config import CONFIG


ARTISTS_DIR = Path(CONFIG["music"]["artists_dir"])
PLAYLISTS_DIR = Path(CONFIG["music"]["playlists_dir"])

SERVER_ARTISTS_DIR = Path(CONFIG["music"]["server_artists_dir"])
SERVER_PLAYLISTS_DIR = Path(CONFIG["music"]["server_playlists_dir"])



def build_song_path(artist: str, album: str, title: str) -> Path:
    artist = sanitize_filename(artist or "Unknown Artist")

    # Unknown albums become Singles
    album = sanitize_filename(album or "Singles")

    title = sanitize_filename(title or "Unknown Track")

    extension = CONFIG.get("yt_dlp", {}).get("output_extension", "opus")

    return ARTISTS_DIR / artist / album / f"{title}.{extension}"



def build_server_song_path(local_track_path: str | Path) -> Path:
    local_track_path = Path(local_track_path)

    relative = local_track_path.relative_to(ARTISTS_DIR)

    return SERVER_ARTISTS_DIR / relative



def build_playlist_path(name: str) -> Path:
    return PLAYLISTS_DIR / f"{sanitize_filename(name)}.m3u"
