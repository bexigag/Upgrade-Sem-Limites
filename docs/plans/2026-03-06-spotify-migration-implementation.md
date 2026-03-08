# Podcast Support + Range Selector Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add "O CEO e o Limite" podcast support via iTunes API + Supadata transcription, plus range selector for both platforms.

**Architecture:** iTunes Lookup API provides all 167 episodes with direct MP3 URLs (free, no auth). Supadata transcribes audio by URL (no download). Streamlit UI gets platform toggle and range selector with two dropdowns.

**Tech Stack:** Python, Streamlit, iTunes Lookup API, Supadata API, Gemini, Notion API

---

### Task 1: Create `src/podcast.py` - iTunes API episode fetcher

**Files:**
- Create: `src/podcast.py`
- Create: `tests/test_podcast.py`

**Step 1: Write failing tests**

```python
# tests/test_podcast.py
from unittest.mock import patch, MagicMock
from src.podcast import get_ceo_episodes, get_episode_metadata

ITUNES_PODCAST_ID = "1662139036"


def test_get_ceo_episodes_returns_list():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "resultCount": 3,
        "results": [
            {"wrapperType": "collection", "collectionName": "O CEO e o limite"},
            {
                "wrapperType": "podcastEpisode",
                "trackName": "Carlos Ribeiro, CEO da Takeda",
                "episodeUrl": "https://traffic.omny.fm/audio1.mp3",
                "releaseDate": "2026-03-02T06:05:00Z",
                "trackViewUrl": "https://podcasts.apple.com/episode1",
            },
            {
                "wrapperType": "podcastEpisode",
                "trackName": "Filipa Pinto Coelho",
                "episodeUrl": "https://traffic.omny.fm/audio2.mp3",
                "releaseDate": "2026-02-23T06:05:00Z",
                "trackViewUrl": "https://podcasts.apple.com/episode2",
            },
        ],
    }

    with patch("src.podcast.requests.get", return_value=mock_resp):
        episodes = get_ceo_episodes()

    assert len(episodes) == 2
    assert episodes[0]["title"] == "Carlos Ribeiro, CEO da Takeda"
    assert episodes[0]["audio_url"] == "https://traffic.omny.fm/audio1.mp3"


def test_get_ceo_episodes_skips_collection_entry():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "resultCount": 2,
        "results": [
            {"wrapperType": "collection", "collectionName": "O CEO e o limite"},
            {
                "wrapperType": "podcastEpisode",
                "trackName": "Episode 1",
                "episodeUrl": "https://example.com/ep1.mp3",
                "releaseDate": "2026-01-01T00:00:00Z",
                "trackViewUrl": "https://example.com/ep1",
            },
        ],
    }

    with patch("src.podcast.requests.get", return_value=mock_resp):
        episodes = get_ceo_episodes()

    assert len(episodes) == 1


def test_get_episode_metadata():
    episode = {
        "title": "Carlos Ribeiro, CEO da Takeda",
        "audio_url": "https://traffic.omny.fm/audio1.mp3",
        "published": "2026-03-02T06:05:00Z",
        "link": "https://podcasts.apple.com/episode1",
    }
    metadata = get_episode_metadata(episode)
    assert metadata["title"] == "Carlos Ribeiro, CEO da Takeda"
    assert metadata["url"] == "https://podcasts.apple.com/episode1"
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_podcast.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# src/podcast.py
import requests

ITUNES_PODCAST_ID = "1662139036"


def get_ceo_episodes() -> list[dict]:
    """Fetch all episodes of 'O CEO e o Limite' from iTunes Lookup API."""
    resp = requests.get(
        "https://itunes.apple.com/lookup",
        params={
            "id": ITUNES_PODCAST_ID,
            "media": "podcast",
            "entity": "podcastEpisode",
            "limit": 300,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    episodes = []
    for item in data.get("results", []):
        if item.get("wrapperType") != "podcastEpisode":
            continue
        audio_url = item.get("episodeUrl")
        if not audio_url:
            continue
        episodes.append({
            "title": item.get("trackName", "Sem titulo"),
            "audio_url": audio_url,
            "published": item.get("releaseDate", ""),
            "link": item.get("trackViewUrl", ""),
        })

    return episodes


def get_episode_metadata(episode: dict) -> dict:
    """Format episode data for the analyzer module."""
    return {
        "title": episode.get("title", "Sem titulo"),
        "description": "",
        "uploader": "O CEO e o Limite",
        "upload_date": episode.get("published", ""),
        "url": episode.get("link", episode.get("audio_url", "")),
    }
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_podcast.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/podcast.py tests/test_podcast.py
git commit -m "feat: add podcast module with iTunes API integration"
```

---

### Task 2: Add Supadata file URL transcription function

**Files:**
- Modify: `streamlit_app.py` (add new function after `get_transcript_supadata`)

**Step 1: Write failing tests**

```python
# tests/test_podcast.py (append to existing)

def test_get_transcript_supadata_file_success():
    from streamlit_app import get_transcript_supadata_file

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"content": "transcribed text here", "lang": "pt"}

    with patch("streamlit_app.requests.get", return_value=mock_resp):
        result = get_transcript_supadata_file("https://example.com/ep.mp3", "fake-key")
        assert result == "transcribed text here"


def test_get_transcript_supadata_file_async_job():
    from streamlit_app import get_transcript_supadata_file

    mock_resp_202 = MagicMock()
    mock_resp_202.status_code = 202
    mock_resp_202.json.return_value = {"jobId": "job123"}

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {"content": "async result", "lang": "pt"}

    with patch("streamlit_app.requests.get", side_effect=[mock_resp_202, mock_resp_200]):
        with patch("streamlit_app.time.sleep"):
            result = get_transcript_supadata_file("https://example.com/ep.mp3", "fake-key")
            assert result == "async result"


def test_get_transcript_supadata_file_empty_returns_none():
    from streamlit_app import get_transcript_supadata_file

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"content": "   ", "lang": "pt"}

    with patch("streamlit_app.requests.get", return_value=mock_resp):
        result = get_transcript_supadata_file("https://example.com/ep.mp3", "fake-key")
        assert result is None
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_podcast.py::test_get_transcript_supadata_file_success -v`
Expected: FAIL

**Step 3: Write implementation**

Add to `streamlit_app.py` after the existing `get_transcript_supadata` function (line 33):

```python
def get_transcript_supadata_file(audio_url: str, api_key: str, max_polls: int = 30) -> str | None:
    """Transcribe an audio file URL using Supadata API. Handles async jobs for large files."""
    try:
        resp = requests.get(
            "https://api.supadata.ai/v1/transcript",
            params={"url": audio_url, "text": "true"},
            headers={"x-api-key": api_key},
            timeout=60,
        )

        if resp.status_code == 200:
            data = resp.json()
            content = data.get("content", "")
            return content if content.strip() else None

        if resp.status_code == 202:
            job_id = resp.json().get("jobId")
            if not job_id:
                return None
            for _ in range(max_polls):
                time.sleep(10)
                poll_resp = requests.get(
                    f"https://api.supadata.ai/v1/transcript/{job_id}",
                    headers={"x-api-key": api_key},
                    timeout=30,
                )
                if poll_resp.status_code == 200:
                    data = poll_resp.json()
                    content = data.get("content", "")
                    return content if content.strip() else None
            return None

        return None
    except Exception:
        return None
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_podcast.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add streamlit_app.py tests/test_podcast.py
git commit -m "feat: add Supadata file URL transcription with async polling"
```

---

### Task 3: Add `process_single_episode` function

**Files:**
- Modify: `streamlit_app.py` (add new function after `process_single_video`)

**Step 1: Write the function**

Add to `streamlit_app.py` after `process_single_video` (after line 129):

```python
def process_single_episode(episode: dict, gemini_key: str, notion_token: str, database_id: str):
    """Process one podcast episode. Returns (success: bool, analysis: dict | None, page_id: str | None)."""
    from src.podcast import get_episode_metadata

    with st.status("A processar o episodio...", expanded=True) as status:
        metadata = get_episode_metadata(episode)
        st.write(f"**{metadata['title']}**")

        if not episode.get("audio_url"):
            st.error("Episodio sem URL de audio.")
            status.update(label="Sem audio", state="error")
            return False, None, None

        st.write("A transcrever via Supadata...")
        supadata_key = st.secrets.get("SUPADATA_API_KEY")
        if not supadata_key:
            st.error("SUPADATA_API_KEY nao configurada.")
            status.update(label="Sem chave Supadata", state="error")
            return False, None, None

        transcript = get_transcript_supadata_file(episode["audio_url"], supadata_key)
        if transcript is None:
            st.error("Nao foi possivel transcrever o episodio.")
            page_id = add_row(
                token=notion_token,
                database_id=database_id,
                video_url=metadata["url"],
                analysis=None,
                status="Erro",
            )
            status.update(label="Erro na transcricao", state="error")
            return False, None, page_id
        st.write(f"Transcricao: {len(transcript)} caracteres")

        st.write("A analisar com Gemini...")
        gemini_keys = [k.strip() for k in gemini_key.split(",") if k.strip()]
        gemini_keys.reverse()
        analysis = None
        for i, key in enumerate(gemini_keys):
            try:
                analysis = analyze_transcript(transcript, metadata, key)
                if analysis:
                    break
            except Exception as e:
                if i < len(gemini_keys) - 1:
                    st.warning(f"Gemini key {i + 1} falhou, a tentar a seguinte...")
                else:
                    st.warning(f"Erro do Gemini: {e}")
        if analysis is None:
            st.error("A analise do Gemini falhou.")
            page_id = add_row(
                token=notion_token,
                database_id=database_id,
                video_url=metadata["url"],
                analysis=None,
                status="Erro",
            )
            status.update(label="Erro na analise", state="error")
            return False, None, page_id

        st.write("A escrever no Notion...")
        try:
            page_id = add_row(
                token=notion_token,
                database_id=database_id,
                video_url=metadata["url"],
                analysis=analysis,
            )
        except Exception as e:
            st.error(f"Erro ao escrever no Notion: {e}")
            status.update(label="Erro no Notion", state="error")
            return False, None, None
        status.update(label="Concluido!", state="complete")

    return True, analysis, page_id
```

**Step 2: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: add process_single_episode for podcast episodes"
```

---

### Task 4: Rewrite main UI with platform selector and range selector

**Files:**
- Modify: `streamlit_app.py` (replace everything from `# --- Main UI ---` line 185 to end of file)

**Step 1: Delete the old `process_playlist` function (lines 136-183)**

This function is replaced by the range selector logic in the main UI. Remove it entirely.

**Step 2: Replace the main UI section**

Replace everything from `# --- Main UI ---` to end of file with:

```python
# --- Main UI ---

st.title("CEO Video Transcriber")

platform = st.radio("Plataforma", ["O CEO e o Limite", "YouTube"], horizontal=True)

if platform == "O CEO e o Limite":
    st.markdown("Podcast da Catia Mateus no Expresso. Os episodios sao carregados automaticamente.")

    if "ceo_episodes" not in st.session_state:
        if st.button("Carregar episodios"):
            with st.spinner("A carregar episodios..."):
                from src.podcast import get_ceo_episodes
                try:
                    episodes = get_ceo_episodes()
                except Exception as e:
                    st.error(f"Erro ao carregar episodios: {e}")
                    st.stop()
            if not episodes:
                st.error("Nenhum episodio encontrado.")
                st.stop()
            st.session_state.ceo_episodes = episodes
            st.rerun()
        st.stop()

    episodes = st.session_state.ceo_episodes
    st.success(f"**{len(episodes)}** episodios encontrados.")

    options = [f"{i + 1}. {ep['title'][:80]}" for i, ep in enumerate(episodes)]

    col1, col2 = st.columns(2)
    with col1:
        from_idx = st.selectbox("De", range(len(options)), format_func=lambda i: options[i], index=0)
    with col2:
        default_to = min(from_idx + 4, len(options) - 1)
        to_idx = st.selectbox("Ate", range(len(options)), format_func=lambda i: options[i], index=default_to)

    if from_idx > to_idx:
        st.error("O episodio 'De' deve ser anterior ou igual ao 'Ate'.")
        st.stop()

    selected = episodes[from_idx:to_idx + 1]
    st.info(f"**{len(selected)}** episodios selecionados (~{len(selected) * GEMINI_WAIT_SECONDS // 60} minutos estimados).")

    gemini_key = st.secrets["GEMINI_API_KEY"]
    notion_token = st.secrets["NOTION_TOKEN"]
    database_id = st.secrets["NOTION_DATABASE_ID"]

    if st.button("Processar", type="primary"):
        progress = st.progress(0, text="A iniciar...")
        success_count = 0
        error_count = 0
        results = []

        for i, episode in enumerate(selected):
            progress.progress(i / len(selected), text=f"Episodio {i + 1}/{len(selected)}: {episode['title'][:50]}")
            st.subheader(f"Episodio {i + 1}: {episode['title'][:80]}")

            ok, analysis, page_id = process_single_episode(episode, gemini_key, notion_token, database_id)

            if ok:
                success_count += 1
                results.append({"episodio": episode["title"][:50], "status": "OK", "nome": analysis.get("nome", "—")})
            else:
                error_count += 1
                results.append({"episodio": episode["title"][:50], "status": "Erro", "nome": "—"})

            if i < len(selected) - 1:
                wait_msg = st.empty()
                for sec in range(GEMINI_WAIT_SECONDS, 0, -1):
                    wait_msg.info(f"A aguardar {sec}s antes do proximo episodio (limite Gemini)...")
                    time.sleep(1)
                wait_msg.empty()

        progress.progress(1.0, text="Concluido!")
        st.divider()
        st.subheader("Resumo")
        st.success(f"**{success_count}** processados com sucesso, **{error_count}** erros")
        st.table(results)

else:
    st.markdown("Cola um link do YouTube (video ou playlist) para analisar entrevistas de CEOs.")
    url = st.text_input("URL do YouTube", placeholder="https://www.youtube.com/watch?v=...")

    if not url:
        st.stop()

    gemini_key = st.secrets["GEMINI_API_KEY"]
    notion_token = st.secrets["NOTION_TOKEN"]
    database_id = st.secrets["NOTION_DATABASE_ID"]

    try:
        parsed = parse_youtube_url(url)
    except ValueError as e:
        st.error(f"URL invalido: {e}")
        st.stop()

    if parsed["type"] == "video":
        if st.button("Processar", type="primary"):
            ok, analysis, page_id = process_single_video(
                parsed["video_id"], gemini_key, notion_token, database_id
            )
            if ok:
                st.success("Video processado com sucesso!")
                clean_id = page_id.replace("-", "")
                st.markdown(f"[Abrir no Notion](https://notion.so/{clean_id})")
                st.subheader("Resultado da Analise")
                st.json(analysis)

    elif parsed["type"] == "playlist":
        if "yt_videos" not in st.session_state or st.session_state.get("yt_playlist_id") != parsed["playlist_id"]:
            if st.button("Carregar videos"):
                with st.spinner("A obter lista de videos da playlist..."):
                    videos = get_playlist_video_ids(parsed["playlist_id"])
                if not videos:
                    st.error("Nenhum video encontrado na playlist.")
                    st.stop()
                st.session_state.yt_videos = videos
                st.session_state.yt_playlist_id = parsed["playlist_id"]
                st.rerun()
            st.stop()

        videos = st.session_state.yt_videos
        st.success(f"**{len(videos)}** videos encontrados.")

        yt_options = [f"{i + 1}. {v['title'][:80]}" for i, v in enumerate(videos)]

        col1, col2 = st.columns(2)
        with col1:
            from_idx = st.selectbox("De", range(len(yt_options)), format_func=lambda i: yt_options[i], index=0)
        with col2:
            default_to = min(from_idx + 4, len(yt_options) - 1)
            to_idx = st.selectbox("Ate", range(len(yt_options)), format_func=lambda i: yt_options[i], index=default_to)

        if from_idx > to_idx:
            st.error("O video 'De' deve ser anterior ou igual ao 'Ate'.")
            st.stop()

        selected = videos[from_idx:to_idx + 1]
        st.info(f"**{len(selected)}** videos selecionados (~{len(selected) * GEMINI_WAIT_SECONDS // 60} minutos estimados).")

        if st.button("Processar", type="primary"):
            progress = st.progress(0, text="A iniciar...")
            success_count = 0
            error_count = 0
            results = []

            for i, video in enumerate(selected):
                progress.progress(i / len(selected), text=f"Video {i + 1}/{len(selected)}: {video['title'][:50]}")
                st.subheader(f"Video {i + 1}: {video['title'][:80]}")

                ok, analysis, page_id = process_single_video(video["id"], gemini_key, notion_token, database_id)

                if ok:
                    success_count += 1
                    results.append({"video": video["title"][:50], "status": "OK", "nome": analysis.get("nome", "—")})
                else:
                    error_count += 1
                    results.append({"video": video["title"][:50], "status": "Erro", "nome": "—"})

                if i < len(selected) - 1:
                    wait_msg = st.empty()
                    for sec in range(GEMINI_WAIT_SECONDS, 0, -1):
                        wait_msg.info(f"A aguardar {sec}s antes do proximo video (limite Gemini)...")
                        time.sleep(1)
                    wait_msg.empty()

            progress.progress(1.0, text="Concluido!")
            st.divider()
            st.subheader("Resumo")
            st.success(f"**{success_count}** processados com sucesso, **{error_count}** erros")
            st.table(results)
```

**Step 3: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: add podcast platform selector and range selector UI"
```

---

### Task 5: Manual end-to-end test

**Step 1: Test podcast flow**

1. Run `streamlit run streamlit_app.py`
2. Platform should default to "O CEO e o Limite"
3. Click "Carregar episodios"
4. Verify 167 episodes load
5. Select a range of 1-2 episodes (De/Ate)
6. Click "Processar"
7. Verify: Supadata transcription works with MP3 URL, Gemini analysis works, Notion row created

**Step 2: Test YouTube single video**

1. Switch to "YouTube"
2. Paste a single YouTube video URL
3. Click "Processar"
4. Verify existing pipeline works

**Step 3: Test YouTube playlist with range**

1. Paste a YouTube playlist URL
2. Click "Carregar videos"
3. Select a range
4. Click "Processar"
5. Verify range selector works correctly
