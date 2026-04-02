"""Generate voiceover using Edge-TTS (free Microsoft TTS)."""

import asyncio
import os
import yaml
import edge_tts


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


async def _generate_voice_async(text, output_path, config):
    """Async implementation of voice generation."""
    voice_config = config["voice"]

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice_config["voice_name"],
        rate=voice_config["rate"],
        pitch=voice_config["pitch"],
    )

    # Generate audio and subtitle data
    submaker = edge_tts.SubMaker()
    audio_chunks = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            submaker.feed(chunk)

    # Write audio file
    with open(output_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)

    # Write subtitle/timing data for word-level sync
    srt_path = output_path.replace(".mp3", ".srt")
    srt_content = submaker.generate_subs()
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    return output_path, srt_path


def generate_voice(script_text, config=None, output_dir=None):
    """Generate voiceover from script text.

    Args:
        script_text: The narration text to convert to speech.
        config: Config dict (loaded from config.yaml if None).
        output_dir: Directory to save audio (uses temp_dir if None).

    Returns:
        Tuple of (audio_path, srt_path).
    """
    if config is None:
        config = load_config()

    if output_dir is None:
        output_dir = config["paths"]["temp_dir"]

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "voiceover.mp3")

    print(f"  Voice: {config['voice']['voice_name']}")
    print(f"  Rate: {config['voice']['rate']}")

    audio_path, srt_path = asyncio.run(
        _generate_voice_async(script_text, output_path, config)
    )

    # Get audio duration
    from moviepy import AudioFileClip

    clip = AudioFileClip(audio_path)
    duration = clip.duration
    clip.close()

    print(f"  Audio duration: {duration:.1f}s")
    print(f"  Saved: {audio_path}")

    return audio_path, srt_path


def list_voices(language="en"):
    """List available Edge-TTS voices for a language."""

    async def _list():
        voices = await edge_tts.list_voices()
        return [v for v in voices if v["Locale"].startswith(language)]

    voices = asyncio.run(_list())
    for v in voices:
        print(f"  {v['ShortName']:40s} {v['Gender']:10s} {v['Locale']}")
    return voices


if __name__ == "__main__":
    config = load_config()
    test_text = (
        "Did you know that the first computer bug was an actual bug? "
        "In 1947, a moth got trapped inside a Harvard Mark II computer. "
        "Engineers literally had to debug the machine."
    )
    audio, srt = generate_voice(test_text, config)
    print(f"Audio: {audio}")
    print(f"Subtitles: {srt}")
