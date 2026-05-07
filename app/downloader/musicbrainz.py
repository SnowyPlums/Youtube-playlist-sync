import musicbrainzngs
from difflib import SequenceMatcher

from app.core.config import CONFIG

cfg = CONFIG["musicbrainz"]

musicbrainzngs.set_useragent(
    cfg["app_name"],
    cfg["version"],
    cfg["contact"]
)


class MusicBrainzResult:
    def __init__(self, data, score):
        self.data = data
        self.score = score



def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()



def search_recording(artist: str, title: str, duration: int | None):
    result = musicbrainzngs.search_recordings(
        recording=title,
        artist=artist,
        limit=5
    )

    recordings = result.get("recording-list", [])

    best_match = None
    best_score = 0

    for rec in recordings:
        score = 0

        rec_title = rec.get("title", "")
        rec_artist = rec["artist-credit"][0]["artist"]["name"]

        title_similarity = similarity(title, rec_title)
        artist_similarity = similarity(artist, rec_artist)

        score += title_similarity * 40
        score += artist_similarity * 40

        if duration and rec.get("length"):
            mb_duration = int(rec["length"]) // 1000
            if abs(mb_duration - duration) <= 3:
                score += 15

        if rec.get("release-list"):
            score += 10

        if score > best_score:
            best_score = score
            best_match = rec

    if best_score < 70:
        return None

    return MusicBrainzResult(best_match, best_score)