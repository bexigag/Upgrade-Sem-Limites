# Podcast Support + Range Selector - Design Document

**Date:** 2026-03-06 (updated 2026-03-08)
**Status:** Approved

## Problem

The current app only supports YouTube as a source for CEO interviews. The podcast "O CEO e o Limite" has 167 episodes but only 19 are visible on YouTube (149 are hidden). We need to access all episodes via another source.

## Solution

Use the Apple Podcasts (iTunes) Lookup API to list all episodes of "O CEO e o Limite" with direct MP3 URLs. Transcribe via Supadata file URL endpoint. Add a range selector for both platforms.

## Architecture

```
Streamlit UI
  |
  v
Platform selector: [O CEO e o Limite | YouTube]
  |                              |
  v                              v
iTunes Lookup API             yt-dlp (existing)
(hardcoded podcast ID)
  |                              |
  v                              v
167 episodes with MP3 URLs    Video list
  |                              |
  v                              v
Range selector (De / Ate dropdowns)
  |
  v
For each selected item:
  |
  +--> Podcast: Supadata /v1/transcript with MP3 URL
  +--> YouTube: youtube-transcript-api (existing) -> Supadata fallback
  |
  v
Gemini analysis (existing)
  |
  v
Notion database (existing)
```

## Podcast Integration Details

### Listing Episodes (iTunes Lookup API)

The iTunes Lookup API is public, free, and requires no authentication.

Endpoint:
```
GET https://itunes.apple.com/lookup?id=1662139036&media=podcast&entity=podcastEpisode&limit=300
```

Returns JSON with all 167 episodes including:
- `trackName` - episode title
- `episodeUrl` - direct MP3 URL (traffic.omny.fm)
- `releaseDate` - publication date
- `trackViewUrl` - Apple Podcasts link

The podcast ID (1662139036) is hardcoded since this is a dedicated tool for one specific podcast.

### Transcription

Supadata accepts public file URLs (MP3, M4A, etc. up to 1GB).

Endpoint: `GET https://api.supadata.ai/v1/transcript`
- Params: `url` (MP3 URL), `text=true`
- Returns 200 with `{"content": "..."}` for small files
- Returns 202 with `{"jobId": "..."}` for large files (need polling)

### Why not RSS / Spotify API

- RSS feed (Omny.fm) only shows 22 most recent episodes (out of 167)
- Spotify API requires Premium subscription
- Spotify embed API only shows 1 episode at a time
- SpotifyScraper library doesn't support podcasts
- iTunes API returns ALL episodes for free, no auth needed

## YouTube Integration (Existing)

No changes to the existing YouTube pipeline. Only addition is the range selector UI.

## UI Changes

### Platform Selector

Radio buttons: "O CEO e o Limite" (default) | "YouTube"

### Podcast flow

No URL input needed - the podcast is hardcoded. User clicks "Carregar episodios", sees the full list, selects a range, and processes.

### YouTube flow

Same as before but with range selector for playlists.

### Range Selector

Two dropdowns (De / Ate) shown after loading episode/video list:
1. Fetch full list
2. Display two selectboxes with episode/video titles
3. Show count of selected items
4. "Processar" button

## New Dependencies

None - only uses `requests` (already installed) for iTunes API.

## New Module

`src/podcast.py`:
- `get_ceo_episodes()` - fetch all episodes from iTunes API
- `get_episode_metadata(episode)` - format episode data for analyzer

## Files to Modify

- `streamlit_app.py` - main UI changes
- No changes to requirements.txt needed

## Files to Create

- `src/podcast.py` - podcast module
