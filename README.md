# YouTube Music to Navidrome Sync

A small Linux-focused FastAPI service for downloading YouTube / YouTube Music songs and playlists, organizing them into a Navidrome-friendly music library, tagging the audio files, and generating `.m3u` playlists.

The project is intended for a setup where Navidrome is hosted elsewhere, such as an Unraid server, and this app writes files into a mounted music directory that Navidrome can scan.

## Features

- Download individual YouTube / YouTube Music tracks.
- Sync YouTube playlists into local audio files.
- Generate `.m3u` playlists for Navidrome.
- Store artists and albums in a folder structure under the configured music directory.
- Use MusicBrainz to improve title, artist, album, release date, and MusicBrainz IDs.
- Use Cover Art Archive for album artwork when a MusicBrainz release ID is found.
- Fall back to YouTube thumbnails when Cover Art Archive has no cover.
- Optionally use Last.fm for genre-like tags, Last.fm URLs, and artist artwork.
- Cache Last.fm responses and artwork downloads aggressively.
- Embed metadata and cover art into downloaded Opus or MP3 files.
- Skip songs that already exist in the local sync database.
- Optional Tampermonkey integration through a `tampermonkey-script` folder.

## Requirements

- Linux
- Python 3.11+
- `ffmpeg`
- `sqlite3`
- A browser supported by `yt-dlp` cookie extraction, such as Firefox
- A mounted music path that this app can write to
- Navidrome pointed at the same music library, or the matching server-side path

Install system dependencies with your distro package manager. For Debian / Ubuntu-like systems:

```bash
sudo apt install python3 python3-venv ffmpeg sqlite3
```

## Setup

Clone the project and enter the directory:

```bash
git clone https://github.com/SnowyPlums/Youtube-playlist-sync.git
cd Youtube-playlist-sync
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Create the database:

```bash
mkdir -p data
sqlite3 data/sync.db < app/models/schema.sql
```

Create the configured music directories if they do not already exist. Replace `/YOUR-ROOT-PATH` with the folder you want to use for your own library:

```bash
mkdir -p /YOUR-ROOT-PATH/artists
mkdir -p /YOUR-ROOT-PATH/playlists
mkdir -p /YOUR-ROOT-PATH/.cache
```

Edit `config.toml` for your machine before starting the service.

## Configuration

The main settings live in `config.toml`.

### Music paths

```toml
[music]
root = "/YOUR-ROOT-PATH"
artists_dir = "/YOUR-ROOT-PATH/artists"
playlists_dir = "/YOUR-ROOT-PATH/playlists"
cache_dir = "/YOUR-ROOT-PATH/.cache"

server_music_root = "/music"
server_artists_dir = "/music/artists"
server_playlists_dir = "/music/playlists"
```

The local paths are where this app writes files. The checked-in `/YOUR-ROOT-PATH` values are placeholders, so change them before running the app.

The server paths are what Navidrome sees. For example, if Unraid maps your local music folder to `/music` inside the Navidrome container, keep the server paths as `/music/...`.

### Downloads

```toml
[downloads]
concurrent_downloads = 2
```

This controls how many queued downloads can run at the same time. Keep this modest to avoid hammering YouTube, MusicBrainz, Last.fm, or artwork services.

### yt-dlp

```toml
[yt_dlp]
cookies_browser = "firefox"

quiet_extract = true
ignore_errors = true
extract_flat = false
skip_unavailable_fragments = true

format = "bestaudio[ext=webm]/bestaudio"
quiet_download = false
noplaylist = true

preferredcodec = "opus"
preferredquality = "192"
output_extension = "opus"
```

`cookies_browser` tells `yt-dlp` where to read YouTube cookies from. Common values include `firefox`, `chrome`, `chromium`, `brave`, and `edge`. Make sure that browser is installed and logged into YouTube if your playlists need account access.

Opus is the recommended default. MP3 tag writing is also supported if you set `preferredcodec = "mp3"` and `output_extension = "mp3"`. Other codecs may download, but embedded metadata support is not implemented yet.

Common codec examples:

```toml
# Recommended default
preferredcodec = "opus"
preferredquality = "192"
output_extension = "opus"

# MP3 alternative
preferredcodec = "mp3"
preferredquality = "320"
output_extension = "mp3"
```

Common `format` examples:

```toml
# Good default for Opus output
format = "bestaudio[ext=webm]/bestaudio"

# Let yt-dlp choose the best available audio source
format = "bestaudio/best"
```

### MusicBrainz

```toml
[musicbrainz]
app_name = "youtube-navidrome-sync"
version = "1.0"
contact = "local@localhost"
```

MusicBrainz is used for cleaner track metadata, release IDs, artist IDs, and album dates. Set `contact` to an email address or local identifier you are comfortable sending in the MusicBrainz user agent.

### Cover Art Archive

```toml
[cover_art_archive]
enabled = true
cache_ttl_days = 3650
```

When enabled, the app uses MusicBrainz release IDs to try Cover Art Archive before falling back to the YouTube thumbnail.

### Last.fm

```toml
[lastfm]
enabled = false
api_key = ""
cache_ttl_days = 365
top_tags_limit = 5
request_delay_seconds = 0.25
download_artist_artwork = true
```

Last.fm is optional. Create an API key at:

```text
https://www.last.fm/api/account/create
```

Then set:

```toml
enabled = true
api_key = "your_api_key"
```

Do not publish your real API key.

## Running

Start the service:

```bash
./run.sh
```

By default it listens on:

```text
http://127.0.0.1:9999
```

## API

Queue a single song:

```bash
curl -X POST http://127.0.0.1:9999/download \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=VIDEO_ID"}'
```

Queue a playlist sync:

```bash
curl -X POST http://127.0.0.1:9999/sync_playlist \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/playlist?list=PLAYLIST_ID"}'
```

Check queue status:

```bash
curl http://127.0.0.1:9999/status
```

## Tampermonkey

This project expects a Tampermonkey helper script to be provided separately inside a `tampermonkey-script` folder. That script can call the local API endpoints above to queue songs or playlists from the browser.

## Output layout

Songs are written under:

```text
artists/<Artist>/<Album>/<Track>.opus
```

Album artwork is written as:

```text
artists/<Artist>/<Album>/cover.jpg
```

Artist artwork is written as:

```text
artists/<Artist>/artist.jpg
```

Playlists are written under:

```text
playlists/<Playlist Name>.m3u
```

The `.m3u` entries use the configured `server_artists_dir`, so Navidrome sees paths from its own container/server perspective.

## Cache

The cache directory stores:

- Last.fm JSON responses
- Artwork downloads
- Artwork failure markers, such as known missing Cover Art Archive images
- Temporary yt-dlp files during download

The cache is intentionally aggressive to reduce repeated calls to external APIs.

## Notes

- Existing songs are skipped based on their YouTube ID in `data/sync.db`.
- Metadata enrichment is best-effort. If MusicBrainz, Last.fm, or artwork services fail temporarily, the app should still download the track using YouTube metadata.
- If you delete `data/sync.db`, the app will no longer know which YouTube IDs have already been downloaded.
- If you move or delete music files manually, update or recreate the database as needed.
