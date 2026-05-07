import aiosqlite
from pathlib import Path

from app.core.config import CONFIG

DB_PATH = CONFIG["database"]["path"]


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