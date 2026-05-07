from pathlib import Path
import yt_dlp

from app.core.config import CONFIG

CACHE_DIR = Path(CONFIG["music"]["cache_dir"])



def extract_info(url: str):
    ydl_opts = {
        "quiet": True,
        "cookiesfrombrowser": (CONFIG["yt_dlp"]["cookies_browser"],)
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)



def download_audio(url: str, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temp_output = CACHE_DIR / "%(id)s.%(ext)s"

    ydl_opts = {
        "format": "bestaudio[ext=webm]/bestaudio",
        "quiet": False,
        "noplaylist": True,
        "cookiesfrombrowser": (
            CONFIG["yt_dlp"]["cookies_browser"],
        ),
        "outtmpl": str(temp_output),

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "opus",
                "preferredquality": "192",
            }
        ]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    downloaded_file = next(CACHE_DIR.glob("*.opus"))
    downloaded_file.rename(output_path)

    return output_path