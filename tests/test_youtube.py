import pytest
from unittest.mock import patch, MagicMock
from src.youtube import parse_youtube_url, extract_video_id, get_transcript, get_playlist_video_ids


def test_extract_video_id_standard_url():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


def test_extract_video_id_short_url():
    url = "https://youtu.be/dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


def test_extract_video_id_with_extra_params():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


def test_parse_youtube_url_single_video():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = parse_youtube_url(url)
    assert result["type"] == "video"
    assert result["video_id"] == "dQw4w9WgXcQ"


def test_parse_youtube_url_playlist():
    url = "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
    result = parse_youtube_url(url)
    assert result["type"] == "playlist"
    assert result["playlist_id"] == "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"


def test_parse_youtube_url_invalid():
    with pytest.raises(ValueError, match="Invalid YouTube URL"):
        parse_youtube_url("https://example.com/not-youtube")


def test_get_transcript_returns_text():
    mock_snippet_1 = MagicMock()
    mock_snippet_1.text = "Hello everyone"
    mock_snippet_2 = MagicMock()
    mock_snippet_2.text = "welcome to the show"
    mock_transcript = MagicMock()
    mock_transcript.__iter__ = MagicMock(return_value=iter([mock_snippet_1, mock_snippet_2]))

    with patch("src.youtube.YouTubeTranscriptApi") as mock_api_class:
        mock_api = MagicMock()
        mock_api.fetch.return_value = mock_transcript
        mock_api_class.return_value = mock_api
        result = get_transcript("fake_video_id")

    assert result == "Hello everyone welcome to the show"


def test_get_transcript_tries_multiple_languages():
    mock_snippet = MagicMock()
    mock_snippet.text = "Olá"
    mock_transcript = MagicMock()
    mock_transcript.__iter__ = MagicMock(return_value=iter([mock_snippet]))

    with patch("src.youtube.YouTubeTranscriptApi") as mock_api_class:
        mock_api = MagicMock()
        mock_api.fetch.return_value = mock_transcript
        mock_api_class.return_value = mock_api
        result = get_transcript("fake_video_id")

    mock_api.fetch.assert_called_once_with(
        "fake_video_id", languages=["pt", "en", "es"]
    )
    assert result == "Olá"


def test_get_transcript_returns_none_on_failure():
    with patch("src.youtube.YouTubeTranscriptApi") as mock_api_class:
        mock_api = MagicMock()
        mock_api.fetch.side_effect = Exception("No transcript")
        mock_api_class.return_value = mock_api
        result = get_transcript("fake_video_id")

    assert result is None


def test_get_playlist_video_ids():
    mock_info = {
        "entries": [
            {"id": "video1", "title": "Interview 1"},
            {"id": "video2", "title": "Interview 2"},
            {"id": "video3", "title": "Interview 3"},
        ]
    }

    with patch("src.youtube.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_info
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        result = get_playlist_video_ids("PLtest123")

    assert result == [
        {"id": "video1", "title": "Interview 1"},
        {"id": "video2", "title": "Interview 2"},
        {"id": "video3", "title": "Interview 3"},
    ]
