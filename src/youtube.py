import re
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi
from yt_dlp import YoutubeDL


def extract_video_id(url: str) -> str:
    parsed = urlparse(url)

    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/")

    if parsed.hostname in ("www.youtube.com", "youtube.com"):
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]

    raise ValueError(f"Cannot extract video ID from: {url}")


def parse_youtube_url(url: str) -> dict:
    parsed = urlparse(url)

    if parsed.hostname not in ("www.youtube.com", "youtube.com", "youtu.be"):
        raise ValueError(f"Invalid YouTube URL: {url}")

    qs = parse_qs(parsed.query)

    if "list" in qs and parsed.path == "/playlist":
        return {"type": "playlist", "playlist_id": qs["list"][0]}

    video_id = extract_video_id(url)
    return {"type": "video", "video_id": video_id}


def get_transcript(video_id: str) -> str | None:
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=["pt", "en", "es"])
        return " ".join(snippet.text for snippet in transcript)
    except Exception:
        return None


def get_playlist_video_ids(playlist_id: str) -> list[dict]:
    ydl_opts = {"extract_flat": True, "quiet": True}

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/playlist?list={playlist_id}",
            download=False,
        )

    return [{"id": entry["id"], "title": entry.get("title", "")} for entry in info["entries"]]
