# CEO Video Transcriber - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python CLI tool that transcribes YouTube CEO interviews, analyzes them with Claude API, and writes structured strategic insights to a Notion database.

**Architecture:** CLI entry point parses video/playlist URLs, a YouTube module fetches transcripts (captions first, local Whisper fallback), an analyzer sends transcripts to Claude for structured extraction, and a Notion module writes results as database rows.

**Tech Stack:** Python 3.11+, youtube-transcript-api, yt-dlp, openai-whisper, anthropic, notion-client, python-dotenv, pytest

---

### Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `src/__init__.py`
- Create: `src/config.py`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`

**Step 1: Create project structure**

```bash
mkdir -p src tests
```

**Step 2: Create pyproject.toml**

```toml
[project]
name = "ceo-video-transcriber"
version = "0.1.0"
description = "Transcribe and analyze CEO YouTube interviews for strategic intelligence"
requires-python = ">=3.11"
dependencies = [
    "youtube-transcript-api>=1.0.0",
    "yt-dlp>=2024.0.0",
    "openai-whisper>=20231117",
    "anthropic>=0.40.0",
    "notion-client>=2.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
]

[project.scripts]
ceo-transcriber = "src.main:main"
```

**Step 3: Create .gitignore**

```
__pycache__/
*.pyc
.env
*.mp3
*.wav
*.m4a
.venv/
dist/
*.egg-info/
```

**Step 4: Create .env.example**

```
ANTHROPIC_API_KEY=your-anthropic-api-key
NOTION_TOKEN=your-notion-integration-token
NOTION_PARENT_PAGE_ID=your-notion-page-id
```

**Step 5: Write failing test for config**

```python
# tests/test_config.py
import os
import pytest
from src.config import load_config


def test_load_config_returns_all_keys(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("NOTION_TOKEN", "test-token")
    monkeypatch.setenv("NOTION_PARENT_PAGE_ID", "test-page-id")

    config = load_config()

    assert config["anthropic_api_key"] == "test-key"
    assert config["notion_token"] == "test-token"
    assert config["notion_parent_page_id"] == "test-page-id"


def test_load_config_raises_on_missing_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.delenv("NOTION_PARENT_PAGE_ID", raising=False)

    with pytest.raises(ValueError, match="Missing required"):
        load_config()
```

**Step 6: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError" or "ImportError"

**Step 7: Implement config module**

```python
# src/__init__.py
```

```python
# src/config.py
import os
from dotenv import load_dotenv


def load_config() -> dict:
    load_dotenv()

    required_keys = [
        "ANTHROPIC_API_KEY",
        "NOTION_TOKEN",
        "NOTION_PARENT_PAGE_ID",
    ]

    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return {
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "notion_token": os.getenv("NOTION_TOKEN"),
        "notion_parent_page_id": os.getenv("NOTION_PARENT_PAGE_ID"),
    }
```

**Step 8: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS

**Step 9: Install dependencies**

```bash
pip install -e ".[dev]"
```

**Step 10: Commit**

```bash
git add -A && git commit -m "feat: project setup with config module"
```

---

### Task 2: YouTube Module - URL Parsing

**Files:**
- Create: `src/youtube.py`
- Create: `tests/test_youtube.py`

**Step 1: Write failing tests for URL parsing**

```python
# tests/test_youtube.py
import pytest
from src.youtube import parse_youtube_url, extract_video_id


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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_youtube.py -v`
Expected: FAIL with "ImportError"

**Step 3: Implement URL parsing**

```python
# src/youtube.py
import re
from urllib.parse import urlparse, parse_qs


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
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_youtube.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/youtube.py tests/test_youtube.py && git commit -m "feat: YouTube URL parsing (video and playlist)"
```

---

### Task 3: YouTube Module - Transcript Fetching

**Files:**
- Modify: `src/youtube.py`
- Modify: `tests/test_youtube.py`

**Step 1: Write failing tests for transcript fetching**

Add to `tests/test_youtube.py`:

```python
from unittest.mock import patch, MagicMock
from src.youtube import get_transcript


def test_get_transcript_returns_text():
    mock_transcript = [
        {"text": "Hello everyone", "start": 0.0, "duration": 2.0},
        {"text": "welcome to the show", "start": 2.0, "duration": 3.0},
    ]

    with patch("src.youtube.YouTubeTranscriptApi") as mock_api:
        mock_api.get_transcript.return_value = mock_transcript
        result = get_transcript("fake_video_id")

    assert result == "Hello everyone welcome to the show"


def test_get_transcript_tries_multiple_languages():
    mock_transcript = [{"text": "Olá", "start": 0.0, "duration": 1.0}]

    with patch("src.youtube.YouTubeTranscriptApi") as mock_api:
        mock_api.get_transcript.return_value = mock_transcript
        result = get_transcript("fake_video_id")

    mock_api.get_transcript.assert_called_once_with(
        "fake_video_id", languages=["pt", "en", "es"]
    )
    assert result == "Olá"


def test_get_transcript_returns_none_on_failure():
    with patch("src.youtube.YouTubeTranscriptApi") as mock_api:
        mock_api.get_transcript.side_effect = Exception("No transcript")
        result = get_transcript("fake_video_id")

    assert result is None
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_youtube.py::test_get_transcript_returns_text -v`
Expected: FAIL with "ImportError"

**Step 3: Implement transcript fetching**

Add to `src/youtube.py`:

```python
from youtube_transcript_api import YouTubeTranscriptApi


def get_transcript(video_id: str) -> str | None:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["pt", "en", "es"]
        )
        return " ".join(entry["text"] for entry in transcript)
    except Exception:
        return None
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_youtube.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/youtube.py tests/test_youtube.py && git commit -m "feat: YouTube transcript fetching with language fallback"
```

---

### Task 4: YouTube Module - Playlist Video Extraction

**Files:**
- Modify: `src/youtube.py`
- Modify: `tests/test_youtube.py`

**Step 1: Write failing tests for playlist extraction**

Add to `tests/test_youtube.py`:

```python
from src.youtube import get_playlist_video_ids


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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_youtube.py::test_get_playlist_video_ids -v`
Expected: FAIL with "ImportError"

**Step 3: Implement playlist extraction**

Add to `src/youtube.py`:

```python
from yt_dlp import YoutubeDL


def get_playlist_video_ids(playlist_id: str) -> list[dict]:
    ydl_opts = {"extract_flat": True, "quiet": True}

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/playlist?list={playlist_id}",
            download=False,
        )

    return [{"id": entry["id"], "title": entry.get("title", "")} for entry in info["entries"]]
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_youtube.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/youtube.py tests/test_youtube.py && git commit -m "feat: playlist video ID extraction via yt-dlp"
```

---

### Task 5: YouTube Module - Video Metadata

**Files:**
- Modify: `src/youtube.py`
- Modify: `tests/test_youtube.py`

**Step 1: Write failing test for video metadata**

Add to `tests/test_youtube.py`:

```python
from src.youtube import get_video_metadata


def test_get_video_metadata():
    mock_info = {
        "title": "CEO talks about AI strategy",
        "description": "John Smith, CEO of TechCorp, discusses...",
        "uploader": "TechCorp Channel",
        "upload_date": "20260215",
        "webpage_url": "https://www.youtube.com/watch?v=abc123",
    }

    with patch("src.youtube.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_info
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        result = get_video_metadata("abc123")

    assert result["title"] == "CEO talks about AI strategy"
    assert result["description"] == "John Smith, CEO of TechCorp, discusses..."
    assert result["url"] == "https://www.youtube.com/watch?v=abc123"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_youtube.py::test_get_video_metadata -v`
Expected: FAIL

**Step 3: Implement video metadata**

Add to `src/youtube.py`:

```python
def get_video_metadata(video_id: str) -> dict:
    ydl_opts = {"quiet": True, "no_warnings": True}

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/watch?v={video_id}",
            download=False,
        )

    return {
        "title": info.get("title", ""),
        "description": info.get("description", ""),
        "uploader": info.get("uploader", ""),
        "upload_date": info.get("upload_date", ""),
        "url": info.get("webpage_url", f"https://www.youtube.com/watch?v={video_id}"),
    }
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_youtube.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/youtube.py tests/test_youtube.py && git commit -m "feat: video metadata extraction"
```

---

### Task 6: Whisper Fallback Module

**Files:**
- Create: `src/whisper_fallback.py`
- Create: `tests/test_whisper_fallback.py`

**Step 1: Write failing tests**

```python
# tests/test_whisper_fallback.py
import os
from unittest.mock import patch, MagicMock
from src.whisper_fallback import transcribe_with_whisper


def test_transcribe_with_whisper_downloads_and_transcribes():
    with patch("src.whisper_fallback.YoutubeDL") as mock_ydl_class, \
         patch("src.whisper_fallback.whisper") as mock_whisper:

        mock_ydl = MagicMock()
        mock_ydl.prepare_filename.return_value = "/tmp/video.webm"
        mock_ydl.extract_info.return_value = {"title": "test"}
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "Hello from Whisper"}
        mock_whisper.load_model.return_value = mock_model

        with patch("os.path.exists", return_value=True), \
             patch("os.remove"):
            result = transcribe_with_whisper("fake_video_id")

    assert result == "Hello from Whisper"


def test_transcribe_with_whisper_returns_none_on_error():
    with patch("src.whisper_fallback.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = Exception("Download failed")
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        result = transcribe_with_whisper("fake_video_id")

    assert result is None
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_whisper_fallback.py -v`
Expected: FAIL

**Step 3: Implement Whisper fallback**

```python
# src/whisper_fallback.py
import os
import tempfile
import whisper
from yt_dlp import YoutubeDL


def transcribe_with_whisper(video_id: str, model_size: str = "base") -> str | None:
    tmp_dir = tempfile.mkdtemp()
    audio_path = None

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "outtmpl": os.path.join(tmp_dir, "%(id)s.%(ext)s"),
            "quiet": True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}",
                download=True,
            )
            audio_path = os.path.join(tmp_dir, f"{video_id}.mp3")

        model = whisper.load_model(model_size)
        result = model.transcribe(audio_path)
        return result["text"]

    except Exception:
        return None

    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_whisper_fallback.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/whisper_fallback.py tests/test_whisper_fallback.py && git commit -m "feat: Whisper fallback transcription for videos without captions"
```

---

### Task 7: Claude Analyzer Module

**Files:**
- Create: `src/analyzer.py`
- Create: `tests/test_analyzer.py`

**Step 1: Write failing tests**

```python
# tests/test_analyzer.py
import json
from unittest.mock import patch, MagicMock
from src.analyzer import analyze_transcript, build_prompt


def test_build_prompt_includes_transcript_and_metadata():
    prompt = build_prompt(
        transcript="The CEO said AI is transforming our business...",
        metadata={"title": "CEO Interview", "description": "John Smith talks AI"}
    )

    assert "The CEO said AI is transforming our business" in prompt
    assert "CEO Interview" in prompt
    assert "John Smith talks AI" in prompt


def test_analyze_transcript_returns_structured_data():
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = json.dumps({
        "nome": "John Smith",
        "cargo": "CEO of TechCorp",
        "usa_ia": "Sim - utiliza IA para automação de processos internos",
        "vai_usar_ia": "Sim - planeia expandir uso de IA generativa",
        "inovacao": "Desenvolvimento de plataforma interna de IA",
        "estrategia_digital": "Transformação digital focada em cloud e IA",
        "tecnologias_mencionadas": ["ChatGPT", "AWS", "Kubernetes"],
        "principais_desafios": "Regulamentação e talento técnico",
        "resumo_estrategico": "TechCorp aposta forte em IA generativa..."
    })

    with patch("src.analyzer.Anthropic") as mock_client_class:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = analyze_transcript(
            transcript="The CEO said AI is transforming...",
            metadata={"title": "CEO Interview", "description": "John Smith, CEO"},
            api_key="test-key",
        )

    assert result["nome"] == "John Smith"
    assert result["cargo"] == "CEO of TechCorp"
    assert "ChatGPT" in result["tecnologias_mencionadas"]
    assert result["usa_ia"].startswith("Sim")


def test_analyze_transcript_handles_invalid_json():
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = "This is not JSON"

    with patch("src.analyzer.Anthropic") as mock_client_class:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = analyze_transcript(
            transcript="text",
            metadata={"title": "t", "description": "d"},
            api_key="test-key",
        )

    assert result is None
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_analyzer.py -v`
Expected: FAIL

**Step 3: Implement analyzer**

```python
# src/analyzer.py
import json
from anthropic import Anthropic


SYSTEM_PROMPT = """És um analista de inteligência estratégica. Analisa transcrições de entrevistas de CEOs e extrai informação estruturada.

Responde APENAS com um objeto JSON válido, sem texto adicional. O JSON deve ter exatamente estes campos:

{
  "nome": "Nome completo do CEO/entrevistado",
  "cargo": "Cargo e empresa",
  "usa_ia": "Sim/Não - breve explicação de como usa IA atualmente",
  "vai_usar_ia": "Sim/Não - breve explicação da intenção futura",
  "inovacao": "Inovações em curso mencionadas",
  "estrategia_digital": "Insights sobre estratégia digital",
  "tecnologias_mencionadas": ["lista", "de", "tecnologias"],
  "principais_desafios": "Desafios principais discutidos",
  "resumo_estrategico": "Resumo estratégico conciso (2-3 frases)"
}

Se algum campo não puder ser determinado a partir da transcrição, usa "Não mencionado".
Responde sempre em Português."""


def build_prompt(transcript: str, metadata: dict) -> str:
    return f"""Analisa a seguinte entrevista de CEO.

Título do vídeo: {metadata.get('title', 'Desconhecido')}
Descrição: {metadata.get('description', 'Sem descrição')}

Transcrição:
{transcript}"""


def analyze_transcript(transcript: str, metadata: dict, api_key: str) -> dict | None:
    client = Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": build_prompt(transcript, metadata)}
        ],
    )

    try:
        response_text = message.content[0].text
        # Handle case where Claude wraps JSON in markdown code block
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(response_text)
    except (json.JSONDecodeError, IndexError):
        return None
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_analyzer.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/analyzer.py tests/test_analyzer.py && git commit -m "feat: Claude-powered transcript analysis with structured extraction"
```

---

### Task 8: Notion Module - Database Creation

**Files:**
- Create: `src/notion_db.py`
- Create: `tests/test_notion_db.py`

**Step 1: Write failing tests**

```python
# tests/test_notion_db.py
from unittest.mock import patch, MagicMock, call
from src.notion_db import create_database, SCHEMA


def test_create_database_returns_id():
    mock_notion = MagicMock()
    mock_notion.databases.create.return_value = {"id": "db-123"}

    with patch("src.notion_db.Client", return_value=mock_notion):
        db_id = create_database(
            token="test-token",
            parent_page_id="page-456",
        )

    assert db_id == "db-123"
    mock_notion.databases.create.assert_called_once()


def test_create_database_has_correct_schema():
    mock_notion = MagicMock()
    mock_notion.databases.create.return_value = {"id": "db-123"}

    with patch("src.notion_db.Client", return_value=mock_notion):
        create_database(token="test-token", parent_page_id="page-456")

    call_kwargs = mock_notion.databases.create.call_args[1]
    properties = call_kwargs["properties"]

    assert "Nome" in properties
    assert "Cargo" in properties
    assert "Link da Entrevista" in properties
    assert "Usa IA" in properties
    assert "Vai Usar IA" in properties
    assert "Inovação" in properties
    assert "Estratégia Digital" in properties
    assert "Tecnologias Mencionadas" in properties
    assert "Principais Desafios" in properties
    assert "Resumo Estratégico" in properties
    assert "Apontamentos" in properties
    assert "Status" in properties
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_notion_db.py -v`
Expected: FAIL

**Step 3: Implement Notion database creation**

```python
# src/notion_db.py
from notion_client import Client


SCHEMA = {
    "Nome": {"title": {}},
    "Cargo": {"rich_text": {}},
    "Link da Entrevista": {"url": {}},
    "Usa IA": {"rich_text": {}},
    "Vai Usar IA": {"rich_text": {}},
    "Inovação": {"rich_text": {}},
    "Estratégia Digital": {"rich_text": {}},
    "Tecnologias Mencionadas": {"multi_select": {"options": []}},
    "Principais Desafios": {"rich_text": {}},
    "Resumo Estratégico": {"rich_text": {}},
    "Apontamentos": {"rich_text": {}},
    "Status": {
        "select": {
            "options": [
                {"name": "A Processar", "color": "yellow"},
                {"name": "Concluído", "color": "green"},
                {"name": "Erro", "color": "red"},
            ]
        }
    },
}


def create_database(token: str, parent_page_id: str) -> str:
    notion = Client(auth=token)

    database = notion.databases.create(
        parent={"page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "CEO Video Transcriber"}}],
        properties=SCHEMA,
    )

    return database["id"]
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_notion_db.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/notion_db.py tests/test_notion_db.py && git commit -m "feat: Notion database creation with full schema"
```

---

### Task 9: Notion Module - Add Row

**Files:**
- Modify: `src/notion_db.py`
- Modify: `tests/test_notion_db.py`

**Step 1: Write failing tests**

Add to `tests/test_notion_db.py`:

```python
from src.notion_db import add_row


def test_add_row_creates_page():
    mock_notion = MagicMock()
    mock_notion.pages.create.return_value = {"id": "page-789"}

    analysis = {
        "nome": "John Smith",
        "cargo": "CEO of TechCorp",
        "usa_ia": "Sim - usa ChatGPT",
        "vai_usar_ia": "Sim - planeia expandir",
        "inovacao": "Plataforma interna de IA",
        "estrategia_digital": "Cloud-first",
        "tecnologias_mencionadas": ["ChatGPT", "AWS"],
        "principais_desafios": "Regulamentação",
        "resumo_estrategico": "Aposta forte em IA",
    }

    with patch("src.notion_db.Client", return_value=mock_notion):
        page_id = add_row(
            token="test-token",
            database_id="db-123",
            video_url="https://youtube.com/watch?v=abc",
            analysis=analysis,
        )

    assert page_id == "page-789"
    mock_notion.pages.create.assert_called_once()

    call_kwargs = mock_notion.pages.create.call_args[1]
    props = call_kwargs["properties"]
    assert props["Nome"]["title"][0]["text"]["content"] == "John Smith"
    assert props["Status"]["select"]["name"] == "Concluído"


def test_add_row_with_error_status():
    mock_notion = MagicMock()
    mock_notion.pages.create.return_value = {"id": "page-err"}

    with patch("src.notion_db.Client", return_value=mock_notion):
        page_id = add_row(
            token="test-token",
            database_id="db-123",
            video_url="https://youtube.com/watch?v=abc",
            analysis=None,
            status="Erro",
        )

    call_kwargs = mock_notion.pages.create.call_args[1]
    assert call_kwargs["properties"]["Status"]["select"]["name"] == "Erro"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_notion_db.py::test_add_row_creates_page -v`
Expected: FAIL

**Step 3: Implement add_row**

Add to `src/notion_db.py`:

```python
def _rich_text(content: str) -> dict:
    return {"rich_text": [{"type": "text", "text": {"content": content[:2000]}}]}


def add_row(
    token: str,
    database_id: str,
    video_url: str,
    analysis: dict | None,
    status: str = "Concluído",
) -> str:
    notion = Client(auth=token)

    properties = {
        "Link da Entrevista": {"url": video_url},
        "Status": {"select": {"name": status}},
    }

    if analysis:
        properties["Nome"] = {
            "title": [{"type": "text", "text": {"content": analysis.get("nome", "Desconhecido")}}]
        }
        properties["Cargo"] = _rich_text(analysis.get("cargo", ""))
        properties["Usa IA"] = _rich_text(analysis.get("usa_ia", ""))
        properties["Vai Usar IA"] = _rich_text(analysis.get("vai_usar_ia", ""))
        properties["Inovação"] = _rich_text(analysis.get("inovacao", ""))
        properties["Estratégia Digital"] = _rich_text(analysis.get("estrategia_digital", ""))
        properties["Principais Desafios"] = _rich_text(analysis.get("principais_desafios", ""))
        properties["Resumo Estratégico"] = _rich_text(analysis.get("resumo_estrategico", ""))

        techs = analysis.get("tecnologias_mencionadas", [])
        if isinstance(techs, list):
            properties["Tecnologias Mencionadas"] = {
                "multi_select": [{"name": t} for t in techs]
            }
    else:
        properties["Nome"] = {
            "title": [{"type": "text", "text": {"content": "Erro no processamento"}}]
        }

    page = notion.pages.create(
        parent={"database_id": database_id},
        properties=properties,
    )

    return page["id"]
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_notion_db.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/notion_db.py tests/test_notion_db.py && git commit -m "feat: Notion row creation with analysis results"
```

---

### Task 10: CLI Entry Point - Main Pipeline

**Files:**
- Create: `src/main.py`
- Create: `tests/test_main.py`

**Step 1: Write failing tests**

```python
# tests/test_main.py
import sys
from unittest.mock import patch, MagicMock
from src.main import process_video, main


def test_process_video_full_pipeline():
    mock_config = {
        "anthropic_api_key": "test-key",
        "notion_token": "test-token",
        "notion_parent_page_id": "page-id",
    }

    with patch("src.main.get_video_metadata") as mock_meta, \
         patch("src.main.get_transcript") as mock_transcript, \
         patch("src.main.analyze_transcript") as mock_analyze, \
         patch("src.main.add_row") as mock_add_row:

        mock_meta.return_value = {
            "title": "CEO Interview",
            "description": "About AI",
            "url": "https://youtube.com/watch?v=abc",
        }
        mock_transcript.return_value = "CEO talks about AI strategy"
        mock_analyze.return_value = {"nome": "John", "cargo": "CEO"}
        mock_add_row.return_value = "page-123"

        result = process_video("abc", "db-id", mock_config)

    assert result == "page-123"
    mock_transcript.assert_called_once_with("abc")
    mock_analyze.assert_called_once()


def test_process_video_uses_whisper_fallback():
    mock_config = {
        "anthropic_api_key": "test-key",
        "notion_token": "test-token",
        "notion_parent_page_id": "page-id",
    }

    with patch("src.main.get_video_metadata") as mock_meta, \
         patch("src.main.get_transcript", return_value=None), \
         patch("src.main.transcribe_with_whisper") as mock_whisper, \
         patch("src.main.analyze_transcript") as mock_analyze, \
         patch("src.main.add_row") as mock_add_row:

        mock_meta.return_value = {"title": "T", "description": "D", "url": "http://y.com"}
        mock_whisper.return_value = "Whisper transcription"
        mock_analyze.return_value = {"nome": "Jane"}
        mock_add_row.return_value = "page-456"

        result = process_video("abc", "db-id", mock_config)

    assert result == "page-456"
    mock_whisper.assert_called_once_with("abc")
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_main.py -v`
Expected: FAIL

**Step 3: Implement main pipeline**

```python
# src/main.py
import sys

from src.config import load_config
from src.youtube import (
    parse_youtube_url,
    get_transcript,
    get_playlist_video_ids,
    get_video_metadata,
)
from src.whisper_fallback import transcribe_with_whisper
from src.analyzer import analyze_transcript
from src.notion_db import create_database, add_row


def process_video(video_id: str, database_id: str, config: dict) -> str:
    print(f"  Fetching metadata for {video_id}...")
    metadata = get_video_metadata(video_id)

    print(f"  Title: {metadata['title']}")
    print(f"  Fetching transcript...")

    transcript = get_transcript(video_id)
    if transcript is None:
        print(f"  No captions found. Trying Whisper fallback...")
        transcript = transcribe_with_whisper(video_id)

    if transcript is None:
        print(f"  ERROR: Could not get transcript for {video_id}")
        return add_row(
            token=config["notion_token"],
            database_id=database_id,
            video_url=metadata["url"],
            analysis=None,
            status="Erro",
        )

    print(f"  Transcript: {len(transcript)} characters. Analyzing with Claude...")

    analysis = analyze_transcript(
        transcript=transcript,
        metadata=metadata,
        api_key=config["anthropic_api_key"],
    )

    if analysis is None:
        print(f"  ERROR: Claude analysis failed for {video_id}")
        return add_row(
            token=config["notion_token"],
            database_id=database_id,
            video_url=metadata["url"],
            analysis=None,
            status="Erro",
        )

    print(f"  Analysis complete. Writing to Notion...")

    return add_row(
        token=config["notion_token"],
        database_id=database_id,
        video_url=metadata["url"],
        analysis=analysis,
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.main <youtube-url> [--db-id <notion-database-id>]")
        sys.exit(1)

    url = sys.argv[1]
    config = load_config()

    # Check for existing database ID or create new one
    db_id = None
    if "--db-id" in sys.argv:
        db_id = sys.argv[sys.argv.index("--db-id") + 1]
    else:
        print("No --db-id provided. Creating new Notion database...")
        db_id = create_database(
            token=config["notion_token"],
            parent_page_id=config["notion_parent_page_id"],
        )
        print(f"Created database: {db_id}")
        print(f"Re-run with: --db-id {db_id}")

    parsed = parse_youtube_url(url)

    if parsed["type"] == "video":
        print(f"\nProcessing single video: {parsed['video_id']}")
        page_id = process_video(parsed["video_id"], db_id, config)
        print(f"Done! Notion page: {page_id}")

    elif parsed["type"] == "playlist":
        print(f"\nFetching playlist: {parsed['playlist_id']}")
        videos = get_playlist_video_ids(parsed["playlist_id"])
        print(f"Found {len(videos)} videos\n")

        for i, video in enumerate(videos, 1):
            print(f"[{i}/{len(videos)}] Processing: {video['title']}")
            try:
                page_id = process_video(video["id"], db_id, config)
                print(f"  Notion page: {page_id}\n")
            except Exception as e:
                print(f"  ERROR: {e}\n")

    print("All done!")


if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_main.py -v`
Expected: PASS

**Step 5: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add src/main.py tests/test_main.py && git commit -m "feat: CLI entry point with full video/playlist processing pipeline"
```

---

### Task 11: End-to-End Manual Test

**Step 1: Create .env file with real keys**

```bash
cp .env.example .env
# Edit .env with real API keys
```

**Step 2: Test with a single video**

Run: `python -m src.main "https://www.youtube.com/watch?v=<a-real-video-id>"`

Expected: Creates a Notion database and row with analysis results.

**Step 3: Test with a playlist**

Run: `python -m src.main "https://www.youtube.com/playlist?list=<a-real-playlist-id>" --db-id <db-id-from-step-2>`

Expected: Processes all videos in the playlist and creates Notion rows.

**Step 4: Verify in Notion**

Open Notion and check:
- Database exists with correct columns
- Rows are populated with analysis data
- Status column shows "Concluído" for successful entries

**Step 5: Final commit**

```bash
git add -A && git commit -m "chore: finalize v1 - ready for use"
```
