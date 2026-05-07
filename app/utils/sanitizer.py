import re

INVALID_CHARS = r'[\\/:*?"<>|]'


def sanitize_filename(name: str) -> str:
    name = re.sub(INVALID_CHARS, "_", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()