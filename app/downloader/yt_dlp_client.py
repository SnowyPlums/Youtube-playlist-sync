from pathlib import Path
from uuid import uuid4
import yt_dlp

from app.core.config import CONFIG

CACHE_DIR = Path(CONFIG["music"]["cache_dir"])
YTDLP_CONFIG = CONFIG["yt_dlp"]



def extract_info(url: str):
    ydl_opts = {
        "quiet": YTDLP_CONFIG.get("quiet_extract", True),
        "ignoreerrors": YTDLP_CONFIG.get("ignore_errors", True),
        "extract_flat": YTDLP_CONFIG.get("extract_flat", False),
        "skip_unavailable_fragments": YTDLP_CONFIG.get(
            "skip_unavailable_fragments",
            True,
        ),
        "cookiesfrombrowser": (
            YTDLP_CONFIG["cookies_browser"],
        )
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)



def download_audio(url: str, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    temp_id = uuid4().hex
    temp_output = CACHE_DIR / f"{temp_id}.%(ext)s"
    output_extension = YTDLP_CONFIG.get(
        "output_extension",
        YTDLP_CONFIG.get("preferredcodec", "opus"),
    )

    ydl_opts = {
        "format": YTDLP_CONFIG.get("format", "bestaudio[ext=webm]/bestaudio"),
        "quiet": YTDLP_CONFIG.get("quiet_download", False),
        "noplaylist": YTDLP_CONFIG.get("noplaylist", True),
        "cookiesfrombrowser": (
            YTDLP_CONFIG["cookies_browser"],
        ),
        "outtmpl": str(temp_output),

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": YTDLP_CONFIG.get("preferredcodec", "opus"),
                "preferredquality": YTDLP_CONFIG.get(
                    "preferredquality",
                    "192",
                ),
            }
        ]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    downloaded_file = CACHE_DIR / f"{temp_id}.{output_extension}"
    downloaded_file.rename(output_path)

    return output_path
