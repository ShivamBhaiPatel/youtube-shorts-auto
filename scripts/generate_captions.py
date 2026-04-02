"""Generate word-level captions using Whisper (GPU accelerated)."""

import os
import re
import yaml


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def parse_srt(srt_path):
    """Parse SRT file into list of {start, end, text} dicts."""
    captions = []
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        # Parse timestamp line: 00:00:01,000 --> 00:00:02,000
        time_line = lines[1]
        match = re.match(
            r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})",
            time_line,
        )
        if not match:
            continue

        start = _srt_time_to_seconds(match.group(1))
        end = _srt_time_to_seconds(match.group(2))
        text = " ".join(lines[2:]).strip()

        captions.append({"start": start, "end": end, "text": text})

    return captions


def _srt_time_to_seconds(time_str):
    """Convert SRT timestamp to seconds."""
    time_str = time_str.replace(",", ".")
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def generate_captions_whisper(audio_path, config=None):
    """Generate word-level captions using Whisper.

    Falls back to this when Edge-TTS SRT is not available or
    when more accurate timing is needed.
    """
    import whisper
    import torch

    if config is None:
        config = load_config()

    caption_config = config["captions"]
    model_name = caption_config["whisper_model"]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Whisper model: {model_name} on {device}")

    model = whisper.load_model(model_name, device=device)
    result = model.transcribe(audio_path, word_timestamps=True)

    captions = []
    for segment in result["segments"]:
        if "words" in segment:
            for word_info in segment["words"]:
                captions.append(
                    {
                        "start": word_info["start"],
                        "end": word_info["end"],
                        "text": word_info["word"].strip(),
                    }
                )
        else:
            captions.append(
                {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                }
            )

    return captions


def generate_captions(audio_path, srt_path=None, config=None):
    """Generate captions - prefer SRT from Edge-TTS, fallback to Whisper.

    Args:
        audio_path: Path to the audio file.
        srt_path: Path to SRT file from Edge-TTS (optional).
        config: Config dict.

    Returns:
        List of caption dicts with {start, end, text} keys.
    """
    if config is None:
        config = load_config()

    if not config["captions"]["enabled"]:
        print("  Captions disabled in config.")
        return []

    # Try Edge-TTS SRT first (already has word timing)
    if srt_path and os.path.exists(srt_path):
        print("  Using Edge-TTS word timing data...")
        captions = parse_srt(srt_path)
        if captions:
            print(f"  Parsed {len(captions)} caption entries from SRT.")
            return captions
        print("  SRT parsing failed, falling back to Whisper...")

    # Fallback to Whisper
    print("  Generating captions with Whisper...")
    captions = generate_captions_whisper(audio_path, config)
    print(f"  Generated {len(captions)} word-level captions.")

    return captions


def group_captions(captions, max_chars=25):
    """Group word-level captions into display-friendly chunks.

    Args:
        captions: List of word-level caption dicts.
        max_chars: Max characters per display line.

    Returns:
        List of grouped caption dicts.
    """
    grouped = []
    current_words = []
    current_chars = 0
    start_time = None

    for cap in captions:
        word = cap["text"]
        if start_time is None:
            start_time = cap["start"]

        if current_chars + len(word) + 1 > max_chars and current_words:
            grouped.append(
                {
                    "start": start_time,
                    "end": cap["start"],
                    "text": " ".join(current_words),
                }
            )
            current_words = [word]
            current_chars = len(word)
            start_time = cap["start"]
        else:
            current_words.append(word)
            current_chars += len(word) + 1

    # Last group
    if current_words:
        grouped.append(
            {
                "start": start_time,
                "end": captions[-1]["end"],
                "text": " ".join(current_words),
            }
        )

    return grouped


if __name__ == "__main__":
    config = load_config()
    # Test with a sample audio
    test_srt = "temp/voiceover.srt"
    test_audio = "temp/voiceover.mp3"
    if os.path.exists(test_srt):
        caps = generate_captions(test_audio, test_srt, config)
        grouped = group_captions(caps, config["captions"]["max_chars_per_line"])
        for g in grouped:
            print(f"  [{g['start']:.2f} - {g['end']:.2f}] {g['text']}")
