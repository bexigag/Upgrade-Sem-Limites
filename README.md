# CEO Video Transcriber

A Python CLI tool that transcribes YouTube CEO interviews, analyzes them with Claude, and writes structured strategic insights to a Notion database.

Given a YouTube video or playlist URL, it:

1. Fetches the video transcript (captions first, local Whisper fallback)
2. Sends the transcript to Claude for structured analysis
3. Writes the results as a row in a Notion database

The analysis extracts: CEO name, role, whether they use AI, innovation initiatives, digital strategy, technologies mentioned, key challenges, and a strategic summary — all in Portuguese.

## Notion Database Schema

Each processed video creates a row with these columns:

| Column | Type | Description |
|---|---|---|
| Nome | Title | CEO / interviewee name |
| Cargo | Text | Role and company |
| Link da Entrevista | URL | YouTube video link |
| Usa IA | Text | Whether they currently use AI |
| Vai Usar IA | Text | Future AI plans |
| Inovação | Text | Innovation initiatives mentioned |
| Estratégia Digital | Text | Digital strategy insights |
| Tecnologias Mencionadas | Multi-select | Technologies referenced |
| Principais Desafios | Text | Key challenges discussed |
| Resumo Estratégico | Text | 2-3 sentence strategic summary |
| Apontamentos | Text | Free-form notes |
| Status | Select | A Processar / Concluído / Erro |

## Setup

### Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)
- A [Notion integration token](https://www.notion.so/my-integrations) with write access
- A Notion page ID where the database will be created

### 1. Clone and create virtual environment

```bash
git clone <repo-url>
cd ceo-video-transcriber
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -e ".[dev]"
```

To enable Whisper fallback (for videos without captions), also install:

```bash
pip install -e ".[whisper]"
```

> **Note:** The whisper extra installs PyTorch (~2GB). It's only needed if you process videos that have no YouTube captions available.

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your real keys:

```
ANTHROPIC_API_KEY=sk-ant-...
NOTION_TOKEN=ntn_...
NOTION_PARENT_PAGE_ID=abc123def456...
```

#### How to get the Notion parent page ID

1. Go to Notion and open the page where you want the database created
2. Click "Share" and "Copy link"
3. The URL looks like: `https://www.notion.so/Your-Page-Title-abc123def456...`
4. The ID is the last 32-character hex string (add dashes if needed: `abc123de-f456-...`)

Make sure your Notion integration has access to this page (Share > Invite integration).

## Usage

### Process a single video

```bash
python -m src.main "https://www.youtube.com/watch?v=VIDEO_ID"
```

On the first run, this creates a new Notion database and prints its ID:

```
No --db-id provided. Creating new Notion database...
Created database: abc123-def456-...
Re-run with: --db-id abc123-def456-...
```

### Process more videos into the same database

```bash
python -m src.main "https://www.youtube.com/watch?v=ANOTHER_ID" --db-id abc123-def456-...
```

### Process an entire playlist

```bash
python -m src.main "https://www.youtube.com/playlist?list=PLxxxxxx" --db-id abc123-def456-...
```

This iterates through every video in the playlist and creates one Notion row per video.

## Running Tests

```bash
python -m pytest tests/ -v
```

All 24 tests use mocks and require no API keys or network access.

## Project Structure

```
src/
  config.py            # Loads and validates env vars
  youtube.py           # URL parsing, transcript fetching, metadata, playlists
  whisper_fallback.py  # Audio download + Whisper transcription (optional)
  analyzer.py          # Claude API call for structured extraction
  notion_db.py         # Notion database creation and row insertion
  main.py              # CLI entry point and pipeline orchestration
tests/
  test_config.py
  test_youtube.py
  test_whisper_fallback.py
  test_analyzer.py
  test_notion_db.py
  test_main.py
```

## How It Works

```
YouTube URL
    |
    v
parse_youtube_url()  -->  single video or playlist?
    |                          |
    v                          v
get_video_metadata()     get_playlist_video_ids()
    |                          |
    v                     for each video:
get_transcript()               |
    |                          v
    |-- captions found? --> analyze_transcript() --> add_row()
    |
    |-- no captions? --> transcribe_with_whisper() --> analyze_transcript() --> add_row()
    |
    |-- no transcript at all? --> add_row(status="Erro")
```
