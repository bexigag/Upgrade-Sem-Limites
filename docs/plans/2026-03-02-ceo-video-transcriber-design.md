# CEO Video Transcriber - Design Document

**Date:** 2026-03-02
**Status:** Approved

## Problem

Transform public CEO interviews and talks on YouTube into actionable strategic intelligence, without manual intervention beyond pasting a link.

## Solution (v1)

A local Python CLI tool that:

1. Takes a YouTube video URL or playlist URL as input
2. Extracts transcriptions (YouTube captions first, local Whisper as fallback)
3. Analyzes content with Claude API to extract structured strategic insights
4. Writes results to a Notion database

### v2 (future)

Deploy to Railway (~$5/month) with a polling loop that watches the Notion database for new links and auto-processes them. Same core code, just a scheduler wrapper.

## Architecture

```
CLI Input (video/playlist URL)
        |
        v
  URL Parser -- single video or playlist?
        |                    |
        v                    v
  Process 1 video    Fetch all video URLs from playlist
        |                    |
        v                    v
  YouTube Captions --> (fail?) --> Local Whisper fallback
        |
        v
  Claude API Analysis
  (structured JSON extraction)
        |
        v
  Notion Database
  (create/update row)
```

### Components

- **CLI entry point** (`main.py`) - Parses args, handles video vs playlist
- **YouTube module** (`youtube.py`) - Fetches captions via youtube-transcript-api, falls back to yt-dlp + local Whisper
- **Analyzer module** (`analyzer.py`) - Sends transcript to Claude API, returns structured JSON
- **Notion module** (`notion_client.py`) - Creates/updates rows in Notion database

### Key Libraries

- `youtube-transcript-api` - Free caption extraction from YouTube
- `yt-dlp` - Audio download for Whisper fallback
- `openai-whisper` - Local open-source transcription (free, GPU recommended)
- `anthropic` - Claude API for content analysis
- `notion-client` - Notion API for database operations
- `python-dotenv` - Environment variable management

## Notion Database Schema

| Column               | Type         | Auto-filled? | Description                                    |
|----------------------|--------------|--------------|------------------------------------------------|
| Nome                 | Title        | Yes          | Name of the CEO/speaker                        |
| Cargo                | Text         | Yes          | Position/role                                  |
| Link da Entrevista   | URL          | Yes          | YouTube video URL (input)                      |
| Usa IA               | Text         | Yes          | Current AI usage (yes/no + explanation)         |
| Vai Usar IA          | Text         | Yes          | Future AI adoption intent (yes/no + explanation)|
| Inovacao             | Text         | Yes          | Ongoing innovations mentioned                  |
| Estrategia Digital   | Text         | Yes          | Digital strategy insights                      |
| Tecnologias Mencionadas | Multi-select | Yes       | Specific technologies named                    |
| Principais Desafios  | Text         | Yes          | Key challenges discussed                       |
| Resumo Estrategico   | Text         | Yes          | Concise strategic summary                      |
| Apontamentos         | Text         | No           | Manual notes (not auto-filled)                 |
| Status               | Select       | Yes          | Processing / Done / Error                      |

## Claude Analysis

The system sends each transcript to Claude with a structured prompt requesting extraction of all fields in Portuguese. Claude returns a JSON object that maps directly to Notion columns.

Fields extracted:
- Nome and Cargo of the speaker (inferred from video title, description, and transcript)
- Usa IA - current AI usage
- Vai Usar IA - future AI adoption intent
- Inovacao - innovations discussed
- Estrategia Digital - digital strategy insights
- Tecnologias Mencionadas - specific technologies named
- Principais Desafios - key challenges
- Resumo Estrategico - concise strategic summary

## Usage

```bash
# Single video
python main.py "https://youtube.com/watch?v=abc123"

# Entire playlist
python main.py "https://youtube.com/playlist?list=xyz456"
```

## Setup (one-time)

1. Create a Notion integration at https://www.notion.so/my-integrations
2. Get a Claude API key from https://console.anthropic.com
3. Create a `.env` file with API keys
4. Run the tool once - it creates the Notion database automatically

## Cost

- **YouTube captions:** Free
- **Local Whisper (fallback):** Free (requires decent hardware)
- **Claude API:** A few cents per video depending on transcript length
- **Notion API:** Free

## Decisions

- Python chosen for best ecosystem (YouTube, Notion, Anthropic SDKs)
- CLI-first approach: simplest architecture, zero infrastructure cost
- YouTube captions preferred over Whisper for speed and reliability
- Local Whisper over Whisper API to keep costs at zero
- Notion as the single interface for viewing and managing data
- v2 automation deferred to keep v1 simple and free
