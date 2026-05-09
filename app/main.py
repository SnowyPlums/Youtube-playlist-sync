from pathlib import Path

from fastapi import FastAPI

from app.api.routes import router
from app.downloader.queue import start_workers
from app.core.config import CONFIG
from app.core.database import initialize_database

app = FastAPI()

app.include_router(router)


@app.on_event("startup")
async def startup():
    Path(CONFIG["music"]["artists_dir"]).mkdir(parents=True, exist_ok=True)
    Path(CONFIG["music"]["playlists_dir"]).mkdir(parents=True, exist_ok=True)
    Path(CONFIG["music"]["cache_dir"]).mkdir(parents=True, exist_ok=True)

    await initialize_database()

    await start_workers(
        CONFIG["downloads"]["concurrent_downloads"]
    )
