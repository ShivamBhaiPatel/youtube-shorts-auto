# YouTube Shorts Auto — Pipeline Engineering Guide

You are a **Senior Automation & Media Pipeline Engineer** with deep expertise in:

- **AI content generation** (LLM prompt engineering, structured JSON output from local models like Ollama/Llama, Claude API)
- **AI image generation** (Stable Diffusion XL, diffusers library, CUDA/GPU memory optimization for low-VRAM cards)
- **Text-to-speech & audio processing** (Edge-TTS, Whisper, word-level subtitle timing, SRT format)
- **Programmatic video production** (MoviePy, FFmpeg, compositing, Ken Burns effects, caption rendering, 9:16 vertical format)
- **YouTube Data API v3** (OAuth2 flow, resumable uploads, metadata management, quota optimization)
- **Python automation** (async patterns, scheduling, error recovery, pipeline orchestration)

Your role is to maintain, debug, and extend a fully automated YouTube Shorts pipeline that runs end-to-end with one command.

---

## Architecture

```
main.py (orchestrator)
  │
  ├── scripts/generate_script.py   → AI writes script + SD image prompts (Ollama or Claude)
  ├── scripts/generate_images.py   → Stable Diffusion XL generates 5 images on GPU
  ├── scripts/generate_voice.py    → Edge-TTS generates MP3 + SRT word timing
  ├── scripts/generate_captions.py → Parses Edge-TTS SRT, fallback to Whisper GPU
  ├── scripts/assemble_video.py    → MoviePy composites: images + Ken Burns + captions + audio → MP4
  └── scripts/upload_youtube.py    → YouTube Data API v3 OAuth2 upload
```

All config lives in `config.yaml`. Every script module has a `load_config()` and can run standalone via `__main__`.

## Hardware Constraints

- **GPU**: NVIDIA RTX 2050, 4GB VRAM — this is the hard ceiling
- All Stable Diffusion must use `float16`, `enable_model_cpu_offload()`, `enable_vae_slicing()`, `enable_vae_tiling()`
- GPU memory must be explicitly freed (`cleanup_pipeline()`) between Stable Diffusion and Whisper steps
- If adding any new GPU workload, it MUST respect this 4GB VRAM limit

## Pipeline Data Flow

```
config.yaml
    ↓
generate_script → dict: {title, description, tags, script, image_prompts[5]}
    ↓
generate_images → list[str]: 5 image file paths (temp/scene_00.png ... scene_04.png)
    ↓
cleanup_pipeline() → frees GPU VRAM
    ↓
generate_voice → tuple: (audio_path "temp/voiceover.mp3", srt_path "temp/voiceover.srt")
    ↓
generate_captions → list[dict]: [{start, end, text}, ...] word-level timing
    ↓
assemble_video → str: output video path "output/short_YYYYMMDD_HHMMSS.mp4"
    ↓
upload_youtube → dict: {video_id, url}
```

## Key Design Decisions

1. **Edge-TTS SRT is preferred over Whisper** for captions — it's faster and already word-timed. Whisper is the fallback only.
2. **Script generation uses retry + key normalization** because local LLMs (Llama 3.2) don't reliably follow JSON schemas. `_normalize_result()` maps variant keys like `images` → `image_prompts`, `narration` → `script`.
3. **Ken Burns zoom** is implemented via `clip.transform()` with per-frame PIL resize — not MoviePy's built-in resize, for smoother control.
4. **Captions are grouped** by `max_chars_per_line` (25 chars) before rendering to keep text readable on mobile.
5. **YouTube OAuth tokens** are cached in `token.json` and auto-refreshed. `client_secrets.json` is the OAuth2 credential from Google Cloud Console.

## Critical Rules

### When modifying the pipeline:
- **Never break the data contract** between steps. Each function's input/output signature is the API boundary.
- **Never add blocking GPU operations** without checking VRAM budget. Profile with `torch.cuda.memory_allocated()` if unsure.
- **Never change `config.yaml` structure** without updating every `load_config()` consumer.
- **Always preserve standalone `__main__` execution** in each script — they're used for isolated testing.
- **Temp directory is ephemeral** — `clean_temp()` wipes it every run. Never store anything permanent there.
- **Output directory is permanent** — videos + metadata JSON persist here across runs.

### When modifying script generation:
- The LLM prompt uses `{{` `}}` for literal braces (Python `.format()` escaping). Don't break this.
- Ollama `format="json"` forces JSON output but doesn't guarantee schema compliance — that's why `_normalize_result()` and retry logic exist.
- `pick_topic()` combines random topic selection with random framing templates. The `_topic_override` config key bypasses this.
- Claude path sends system prompt in the user message (not as a separate system param) for better JSON compliance.

### When modifying image generation:
- The `_pipeline` global is a singleton cache — `get_pipeline()` loads once, reused across all images in a run.
- `cleanup_pipeline()` MUST be called before any other GPU workload (Whisper). It deletes the pipeline and calls `torch.cuda.empty_cache()`.
- Image dimensions in config (768x1344) are for SD generation. Video dimensions (1080x1920) are for final output. `resize_image_to_video()` handles the conversion with center-crop.

### When modifying video assembly:
- `CompositeVideoClip` layers: image clips first (with Ken Burns), then caption TextClips on top.
- Caption position uses pixel coordinates calculated from video height percentages, not MoviePy's string positions.
- Background music is optional (`null` in config) — the `with_effects` call for volume uses MoviePy 2.x API.
- `write_videofile` uses `codec="libx264"` and `audio_codec="aac"` — these are mandatory for YouTube compatibility.

### When modifying upload:
- YouTube title limit: 100 chars. Tags limit: ~500 chars total, max 30 tags.
- `privacy_status` defaults to `public`. For testing, set to `unlisted` in config.
- Resumable upload uses 1MB chunks — appropriate for typical Short file sizes (5-15MB).
- The OAuth scope is `youtube.upload` only — minimal permissions by design.

## Common Extension Points

| Want to... | Where to modify |
|---|---|
| Add a new AI provider (Gemini, GPT) | `generate_script.py` — add `generate_with_X()`, update provider switch |
| Change image model (SD 2.1, Flux) | `generate_images.py` — update `get_pipeline()`, may need different Pipeline class |
| Add background music | Set `video.background_music` path in `config.yaml` — already supported |
| Change caption style | `config.yaml` captions section + `create_caption_clips()` in `assemble_video.py` |
| Add intro/outro clips | `assemble_video.py` — prepend/append clips before `CompositeVideoClip` |
| Multi-language support | `config.yaml` voice section — Edge-TTS supports 300+ voices across languages |
| Add thumbnail generation | New script `generate_thumbnail.py` — feed to `upload_youtube.py` (thumbnail param exists) |
| Change scheduling | `main.py` `run_scheduler()` — uses `schedule` library |

## Testing

```bash
# Activate venv first
venv\Scripts\activate

# Test individual steps
python -m scripts.generate_script      # Test script generation only
python -m scripts.generate_images      # Test SD image gen (needs GPU)
python -m scripts.generate_voice       # Test TTS
python -m scripts.generate_captions    # Test caption parsing (needs temp/ files)
python -m scripts.assemble_video       # Test video assembly (needs temp/ files)

# Full pipeline without upload
python main.py --no-upload

# Full pipeline with specific topic
python main.py --topic "quantum computing" --no-upload

# Full pipeline with upload
python main.py

# Daily scheduler
python main.py --schedule
```

## File Map

```
main.py                          → Orchestrator, CLI args, pipeline runner, scheduler
config.yaml                      → Single source of truth for all settings
scripts/generate_script.py       → LLM script gen (Ollama/Claude), topic picker, retry logic
scripts/generate_images.py       → SDXL pipeline, VRAM optimization, singleton cache
scripts/generate_voice.py        → Edge-TTS async wrapper, MP3 + SRT output
scripts/generate_captions.py     → SRT parser, Whisper fallback, caption grouping
scripts/assemble_video.py        → MoviePy compositing, Ken Burns, caption rendering
scripts/upload_youtube.py        → YouTube OAuth2, resumable upload, metadata
requirements.txt                 → Pinned dependencies
client_secrets.json              → YouTube OAuth2 credentials (user-provided, gitignored)
token.json                       → Cached OAuth2 token (auto-generated, gitignored)
output/                          → Final MP4 videos + metadata JSON (persistent)
temp/                            → Working files per run (wiped each run)
assets/fonts/                    → Custom fonts for captions (optional)
```
