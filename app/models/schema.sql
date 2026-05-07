CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    youtube_id TEXT UNIQUE NOT NULL,

    title TEXT,
    artist TEXT,
    album TEXT,

    track_number INTEGER,
    duration INTEGER,

    filepath TEXT NOT NULL,
    audio_hash TEXT,

    thumbnail_url TEXT,

    metadata_source TEXT,

    musicbrainz_recording_id TEXT,
    musicbrainz_release_id TEXT,
    musicbrainz_artist_id TEXT,

    downloaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    youtube_playlist_id TEXT UNIQUE NOT NULL,

    title TEXT NOT NULL,

    m3u_path TEXT NOT NULL,

    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS playlist_songs (
    playlist_id INTEGER NOT NULL,
    song_id INTEGER NOT NULL,
    position INTEGER NOT NULL,

    PRIMARY KEY (playlist_id, song_id),

    FOREIGN KEY (playlist_id) REFERENCES playlists(id),
    FOREIGN KEY (song_id) REFERENCES songs(id)
);

CREATE TABLE IF NOT EXISTS failed_downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    youtube_id TEXT,
    playlist_id TEXT,

    error TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);