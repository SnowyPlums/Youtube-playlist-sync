import asyncio
import logging

from app.services.song_service import download_song
from app.services.playlist_service import sync_playlist

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s"
)

queue = asyncio.Queue()


async def worker(worker_id: int):
    while True:
        task = await queue.get()

        logging.info(
            f"[Worker {worker_id}] Starting task: {task['type']} -> {task['url']}"
        )

        try:
            if task["type"] == "song":
                await download_song(task["url"])
                logging.info(
                    f"[Worker {worker_id}] Finished song download"
                )

            elif task["type"] == "playlist":
                await sync_playlist(task["url"])
                logging.info(
                    f"[Worker {worker_id}] Finished playlist sync"
                )

        except Exception:
            logging.exception(
                f"[Worker {worker_id}] Worker failed"
            )

        finally:
            logging.info(
                f"[Worker {worker_id}] Queue remaining: {queue.qsize()}"
            )
            queue.task_done()


async def start_workers(count=2):
    for i in range(count):
        logging.info(f"Starting worker {i}")
        asyncio.create_task(worker(i))