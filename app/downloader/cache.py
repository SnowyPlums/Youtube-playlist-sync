from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import json

from app.core.config import CONFIG


CACHE_DIR = Path(CONFIG["music"]["cache_dir"])


def cache_path(namespace: str, key: str, suffix: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return CACHE_DIR / namespace / f"{digest}.{suffix}"


def is_fresh(path: Path, ttl_days: int) -> bool:
    if not path.exists():
        return False

    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return datetime.now(timezone.utc) - modified < timedelta(days=ttl_days)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
