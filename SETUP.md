# YouTube Shorts Auto - Setup Guide

## Prerequisites

- Python 3.10+
- NVIDIA GPU with CUDA (RTX 2050 4GB works)
- FFmpeg installed and in PATH
- Ollama installed (for free local AI script generation)

## Step 1: Install FFmpeg

Download from https://ffmpeg.org/download.html or use:
```bash
winget install FFmpeg
```
Verify: `ffmpeg -version`

## Step 2: Install Ollama (Free Local AI)

Download from https://ollama.com and install.
Then pull a model:
```bash
ollama pull llama3.2
```

## Step 3: Install Python Dependencies

```bash
cd D:\WorkingProjects\youtube-shorts-auto

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install PyTorch with CUDA (RTX 2050)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Install all dependencies
pip install -r requirements.txt
```

## Step 4: YouTube API Setup (for auto-upload)

1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Enable **YouTube Data API v3**
4. Go to **Credentials** > **Create Credentials** > **OAuth 2.0 Client ID**
5. Application type: **Desktop app**
6. Download the JSON and save as `client_secrets.json` in project root
7. First run will open a browser for Google account authorization

## Step 5: Test Run

```bash
# Generate video without uploading (test)
python main.py --no-upload

# Generate and upload
python main.py

# Run on daily schedule
python main.py --schedule

# Specific topic
python main.py --topic "quantum computing" --no-upload
```

## Configuration

Edit `config.yaml` to customize:
- Topics and niche
- Voice (change TTS voice)
- Image style (SD model, quality)
- Caption style (font, position, color)
- Upload settings (tags, privacy, schedule)
- AI provider (ollama free vs claude paid)

## Folder Structure

```
youtube-shorts-auto/
├── config.yaml           # All settings
├── main.py               # Run this
├── client_secrets.json   # YouTube OAuth (you create this)
├── token.json            # Auto-generated after first auth
├── scripts/
│   ├── generate_script.py    # AI writes the script
│   ├── generate_images.py    # Stable Diffusion makes visuals
│   ├── generate_voice.py     # Edge-TTS voiceover
│   ├── generate_captions.py  # Whisper auto-captions
│   ├── assemble_video.py     # MoviePy assembles video
│   └── upload_youtube.py     # YouTube API upload
├── output/               # Final videos saved here
├── temp/                 # Working files (auto-cleaned)
└── assets/fonts/         # Custom fonts (optional)
```

## Troubleshooting

### CUDA out of memory
- In `config.yaml`, change `model_id` to `"stabilityai/stable-diffusion-2-1"` (uses less VRAM)
- Reduce `num_inference_steps` to 20
- Reduce image `width`/`height`

### Ollama not responding
- Make sure Ollama is running: `ollama serve`
- Check model is pulled: `ollama list`

### YouTube upload fails
- Delete `token.json` and re-authenticate
- Make sure YouTube Data API is enabled in Google Cloud Console
- Check daily upload quota (default: 6 videos/day for unverified apps)
