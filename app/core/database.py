import aiosqlite
from pathlib import Path
import sqlite3

from app.core.config import CONFIG

DB_PATH = CONFIG["database"]["path"]
SCHEMA_PATH = Path("app/models/schema.sql")

SONG_MIGRATIONS = {
    "album_date": "ALTER TABLE songs ADD COLUMN album_date TEXT",
    "album_year": "ALTER TABLE songs ADD COLUMN album_year INTEGER",
    "genres": "ALTER TABLE songs ADD COLUMN genres TEXT",
    "cover_art_url": "ALTER TABLE songs ADD COLUMN cover_art_url TEXT",
    "artist_artwork_url": "ALTER TABLE songs ADD COLUMN artist_artwork_url TEXT",
    "lastfm_url": "ALTER TABLE songs ADD COLUMN lastfm_url TEXT",
}


async def get_db():
    db = await aiosqlite.connect(DB_PATH)

    db.row_factory = aiosqlite.Row

    # Prevent immediate SQLITE_BUSY failures
    await db.execute("PRAGMA busy_timeout = 30000")

    # Better concurrent read/write behavior
    await db.execute("PRAGMA journal_mode=WAL")

    # Slightly safer durability/performance balance
    await db.execute("PRAGMA synchronous=NORMAL")

    return db


async def initialize_database():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as db:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        db.executescript(schema)

        cursor = db.execute("PRAGMA table_info(songs)")
        columns = {row[1] for row in cursor.fetchall()}

        for column, statement in SONG_MIGRATIONS.items():
            if column not in columns:
                db.execute(statement)

        db.commit()
