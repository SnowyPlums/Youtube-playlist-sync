from fastapi import APIRouter
from pydantic import BaseModel

from app.downloader.queue import queue

router = APIRouter()


class URLRequest(BaseModel):
    url: str


@router.post("/download")
async def download(req: URLRequest):
    await queue.put({
        "type": "song",
        "url": req.url
    })

    return {"status": "queued"}


@router.post("/sync_playlist")
async def sync_playlist(req: URLRequest):
    await queue.put({
        "type": "playlist",
        "url": req.url
    })

    return {"status": "queued"}


@router.get("/status")
async def status():
    return {
        "queue_size": queue.qsize()
    }