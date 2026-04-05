# Project Context

## Project Name

youtube-shorts-auto

## Tech Stack

- Language: Python 3.12
- Script gen: Gemini 2.5 Flash (primary), Ollama qwen3:4b (local), Claude Haiku 4.5, HuggingFace+TurboQuant
- Image gen: Gemini Imagen (primary), Pollinations (fallback), local SDXL (fallback)
- Voice: Edge-TTS (MP3 + SRT output)
- Captions: Edge-TTS SRT (primary), Whisper GPU (fallback)
- Video: MoviePy 2.x (compositing, Ken Burns, caption rendering)
- Upload: YouTube Data API v3 (OAuth2, resumable upload)
- Config: config.yaml (single source of truth)
- Key dependencies: torch, diffusers, transformers, moviepy, edge-tts, openai-whisper, google-genai, ollama, turboquant

## Repository Structure

```
youtube-shorts-auto/
├── main.py                      # Orchestrator, CLI args, pipeline runner, scheduler
├── config.yaml                  # All settings (content, images, voice, captions, video, youtube, schedule)
├── .env                         # API keys (GEMINI_API_KEY, ANTHROPIC_API_KEY)
├── scripts/
│   ├── generate_script.py       # LLM script gen (Ollama/Claude/Gemini/HuggingFace), topic picker
│   ├── generate_images.py       # Gemini/Pollinations/SDXL image gen with fallback
│   ├── generate_voice.py        # Edge-TTS async wrapper, MP3 + SRT output
│   ├── generate_captions.py     # SRT parser, Whisper fallback, caption grouping
│   ├── assemble_video.py        # MoviePy compositing, Ken Burns, caption rendering
│   └── upload_youtube.py        # YouTube OAuth2, resumable upload, metadata
├── client_secrets.json          # YouTube OAuth2 credentials (gitignored)
├── token.json                   # Cached OAuth2 token (auto-generated, gitignored)
├── output/                      # Final MP4 videos + metadata JSON (persistent)
├── temp/                        # Working files per run (wiped each run)
└── assets/fonts/                # Custom fonts for captions (optional)
```

## Data Flow (Pipeline Contract)

```
config.yaml
  → generate_script  → dict: {title, description, tags, script, image_prompts[5]}
  → generate_images  → list[str]: 5 image file paths
  → generate_voice   → tuple: (audio_path, srt_path)
  → generate_captions → list[dict]: [{start, end, text}, ...] word-level timing
  → assemble_video   → str: output video path
  → upload_youtube   → dict: {video_id, url}
```

## Key Design Decisions

- Edge-TTS SRT preferred over Whisper for captions (faster, already word-timed)
- Script gen uses retry + key normalization for unreliable local LLM JSON output
- Ken Burns zoom via clip.transform() with per-frame PIL resize
- Captions grouped by max_chars_per_line (25 chars) for mobile readability
- YouTube OAuth tokens cached in token.json, auto-refreshed
- GPU budget: 4GB VRAM (RTX 2050) — SDXL uses float16 + cpu_offload
- API keys loaded from .env via python-dotenv

## Known Gaps

- Gemini image gen free tier quota issues (limit: 0 sometimes)
- Pollinations fallback intermittent (502 errors)
- No Telegram bot integration yet (planned Phase 9)
- No multi-channel support yet (planned Phase 10)
- No thumbnail generation yet (planned Phase 11)
- HuggingFace+TurboQuant provider untested in production runs
