# YouTube Shorts Auto

Fully automated YouTube Shorts pipeline for tech content. One command generates a complete 60-second video — AI script, AI visuals, voiceover, captions — and uploads it directly to YouTube.

Built to run on a local GPU (NVIDIA RTX 2050+). No paid APIs required.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     python main.py                          │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  1. Script Gen  │    │  2. Image Gen   │    │  3. Voiceover   │
│  Ollama/Claude  │───▶│Stable Diffusion │───▶│   Edge-TTS      │
│  (AI writes it) │    │ (RTX 2050 GPU)  │    │   (free TTS)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                      │
         ┌────────────────────────────────────────────┘
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  4. Captions    │    │  5. Assemble    │    │  6. Upload      │
│  Whisper (GPU)  │───▶│ MoviePy+FFmpeg  │───▶│  YouTube API   │
│  (auto-sync)    │    │  (9:16 video)   │    │  (auto-upload)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## Features

- **Zero cost** — all tools run locally, no paid APIs required
- **One command** — `python main.py` does everything end to end
- **Daily scheduler** — set it and forget it, uploads automatically
- **Tech niche** — configurable topics: AI, cybersecurity, programming, gadgets, space tech, and more
- **AI-generated visuals** — Stable Diffusion creates unique images for every video
- **Word-level captions** — Edge-TTS + Whisper for accurate, synced subtitles
- **Ken Burns effect** — smooth zoom animation on images
- **GPU accelerated** — Stable Diffusion + Whisper both use CUDA
- **9:16 format** — proper vertical video for Shorts (1080x1920)

---

## Tech Stack

| Component | Tool | Cost |
|---|---|---|
| Script generation | [Ollama](https://ollama.com) (Llama 3.2 / Mistral) | Free |
| Image generation | [Stable Diffusion XL](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0) | Free |
| Voiceover | [Edge-TTS](https://github.com/rany2/edge-tts) (Microsoft Neural TTS) | Free |
| Captions | [Whisper](https://github.com/openai/whisper) | Free |
| Video assembly | [MoviePy](https://zulko.github.io/moviepy/) + FFmpeg | Free |
| YouTube upload | [YouTube Data API v3](https://developers.google.com/youtube/v3) | Free |

---

## Requirements

- Python 3.10+
- NVIDIA GPU with 4GB+ VRAM (RTX 2050 / GTX 1650+)
- CUDA 12.1+
- FFmpeg
- Ollama

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/youtube-shorts-auto.git
cd youtube-shorts-auto
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install PyTorch with CUDA

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Install FFmpeg

```bash
# Windows (winget)
winget install FFmpeg

# Verify
ffmpeg -version
```

### 6. Install Ollama + pull a model

```bash
# Download from https://ollama.com and install, then:
ollama pull llama3.2
```

### 7. YouTube API setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **YouTube Data API v3**
3. Create **OAuth 2.0 Client ID** (Desktop app)
4. Download JSON → save as `client_secrets.json` in project root
5. First run opens a browser for Google authorization → `token.json` is saved automatically

---

## Usage

```bash
# Generate + upload one video
python main.py

# Generate only, no upload (for testing)
python main.py --no-upload

# Specific topic
python main.py --topic "quantum computing"

# Daily scheduler (runs at time set in config.yaml)
python main.py --schedule
```

### Example output

```
╭──────────────────────────────────────╮
│  YouTube Shorts Auto Pipeline        │
╰──────────────────────────────────────╯

Step 1/6: Generating script...
  Topic: The hidden truth about AI chips
  Provider: ollama
  Title: Why AI Needs Its Own Brain
  Words: 132

Step 2/6: Generating images (Stable Diffusion)...
  Loading model: stabilityai/stable-diffusion-xl-base-1.0
  GPU: NVIDIA GeForce RTX 2050
  Generating image 1/5...
  Generating image 2/5...
  ...

Step 3/6: Generating voiceover (Edge-TTS)...
  Voice: en-US-ChristopherNeural
  Audio duration: 52.3s

Step 4/6: Generating captions...
  Parsed 134 caption entries from SRT.

Step 5/6: Assembling video...
  Rendering video...

Step 6/6: Uploading to YouTube...
  Upload complete!
  URL: https://youtube.com/shorts/xxxxxxxxxx

╭─────────────────────────────────────────────────────────────╮
│  Pipeline Complete!                                         │
│  Video: output/short_20260403_100032.mp4                    │
│  YouTube: https://youtube.com/shorts/xxxxxxxxxx             │
│  Duration: 187s                                             │
╰─────────────────────────────────────────────────────────────╯
```

---

## Configuration

Edit `config.yaml` to customize everything:

```yaml
content:
  niche: "tech"
  topics:
    - "AI and machine learning"
    - "cybersecurity"
    - "programming languages"
    # add more...

voice:
  voice_name: "en-US-ChristopherNeural"  # change TTS voice
  rate: "+5%"                             # speaking speed

images:
  num_images: 5          # scenes per video
  num_inference_steps: 30  # quality (higher = slower)

captions:
  font_size: 60
  position: "center"     # top / center / bottom
  style: "word_highlight"

schedule:
  upload_time: "10:00"   # daily upload time
  videos_per_day: 1
```

### Switching AI providers

```yaml
script_generation:
  provider: "ollama"   # free, local
  # provider: "claude" # paid, better quality
```

---

## Project Structure

```
youtube-shorts-auto/
├── main.py                      # Orchestrator — run this
├── config.yaml                  # All settings
├── requirements.txt
├── client_secrets.json          # YouTube OAuth (you add this)
├── token.json                   # Auto-generated after first auth
├── scripts/
│   ├── generate_script.py       # AI script + image prompts
│   ├── generate_images.py       # Stable Diffusion pipeline
│   ├── generate_voice.py        # Edge-TTS voiceover
│   ├── generate_captions.py     # Whisper word-level captions
│   ├── assemble_video.py        # MoviePy + Ken Burns + captions
│   └── upload_youtube.py        # YouTube Data API v3
├── output/                      # Final videos + metadata JSON
├── temp/                        # Working files (auto-cleaned)
└── assets/
    └── fonts/                   # Custom fonts (optional)
```

---

## Troubleshooting

### CUDA out of memory (RTX 2050 / 4GB VRAM)

Switch to a smaller model in `config.yaml`:
```yaml
images:
  model_id: "stabilityai/stable-diffusion-2-1"  # lighter model
  num_inference_steps: 20                         # fewer steps
```

### Ollama not responding

```bash
# Make sure Ollama service is running
ollama serve

# Check available models
ollama list
```

### YouTube upload quota exceeded

YouTube Data API has a default daily quota of **10,000 units** (~6 video uploads/day) for unverified apps. To increase:
- Submit your app for Google verification, or
- Use multiple Google Cloud projects (each gets its own quota)

### First run is slow

Stable Diffusion downloads the model (~6GB) on first run. Subsequent runs use the cached model.

---

## License

MIT
