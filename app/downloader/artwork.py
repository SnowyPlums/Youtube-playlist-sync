from pathlib import Path
import httpx


async def download_artwork(url: str, output_path: Path):
    if not url:
        return

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

    output_path.write_bytes(response.content)