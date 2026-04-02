"""Assemble final video from images, voiceover, and captions using MoviePy."""

import os
import yaml
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    TextClip,
    concatenate_videoclips,
)
from scripts.generate_captions import group_captions


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def resize_image_to_video(image_path, width, height):
    """Resize and crop image to fit video dimensions (9:16)."""
    img = Image.open(image_path)
    img_ratio = img.width / img.height
    target_ratio = width / height

    if img_ratio > target_ratio:
        # Image is wider - crop sides
        new_width = int(img.height * target_ratio)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, img.height))
    else:
        # Image is taller - crop top/bottom
        new_height = int(img.width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, img.width, top + new_height))

    img = img.resize((width, height), Image.LANCZOS)
    return np.array(img)


def create_ken_burns_clip(image_path, duration, config):
    """Create an image clip with Ken Burns (zoom) effect."""
    video_config = config["video"]
    w = video_config["width"]
    h = video_config["height"]

    img_array = resize_image_to_video(image_path, w, h)
    clip = ImageClip(img_array).with_duration(duration)

    if video_config.get("zoom_effect", False):
        zoom_start, zoom_end = video_config["zoom_range"]

        def zoom_func(get_frame, t):
            frame = get_frame(t)
            progress = t / duration
            zoom = zoom_start + (zoom_end - zoom_start) * progress

            # Calculate crop dimensions
            fh, fw = frame.shape[:2]
            crop_w = int(fw / zoom)
            crop_h = int(fh / zoom)
            x = (fw - crop_w) // 2
            y = (fh - crop_h) // 2

            cropped = frame[y : y + crop_h, x : x + crop_w]
            # Resize back to original dimensions
            from PIL import Image

            pil_img = Image.fromarray(cropped)
            pil_img = pil_img.resize((fw, fh), Image.LANCZOS)
            return np.array(pil_img)

        clip = clip.transform(zoom_func)

    return clip


def create_caption_clips(captions, config):
    """Create text overlay clips from captions."""
    caption_config = config["captions"]
    video_config = config["video"]

    if not captions:
        return []

    grouped = group_captions(captions, caption_config["max_chars_per_line"])
    clips = []

    # Caption position
    pos_map = {
        "top": ("center", video_config["height"] * 0.15),
        "center": ("center", video_config["height"] * 0.45),
        "bottom": ("center", video_config["height"] * 0.75),
    }
    position = pos_map.get(caption_config["position"], pos_map["center"])

    for group in grouped:
        duration = group["end"] - group["start"]
        if duration <= 0:
            continue

        txt_clip = (
            TextClip(
                text=group["text"].upper(),
                font_size=caption_config["font_size"],
                color=caption_config["font_color"],
                stroke_color=caption_config["stroke_color"],
                stroke_width=caption_config["stroke_width"],
                font="Arial-Bold",
                method="caption",
                size=(video_config["width"] * 0.85, None),
                text_align="center",
            )
            .with_position(position)
            .with_start(group["start"])
            .with_duration(duration)
        )
        clips.append(txt_clip)

    return clips


def assemble_video(image_paths, audio_path, captions, config=None, output_dir=None):
    """Assemble final video from components.

    Args:
        image_paths: List of image file paths.
        audio_path: Path to voiceover audio.
        captions: List of caption dicts with {start, end, text}.
        config: Config dict.
        output_dir: Output directory.

    Returns:
        Path to the final video file.
    """
    if config is None:
        config = load_config()

    if output_dir is None:
        output_dir = config["paths"]["output_dir"]

    os.makedirs(output_dir, exist_ok=True)
    video_config = config["video"]

    # Load audio to get total duration
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    print(f"  Total audio duration: {total_duration:.1f}s")

    # Calculate duration per image
    num_images = len(image_paths)
    transition_dur = video_config.get("transition_duration", 0.5)
    duration_per_image = total_duration / num_images

    print(f"  Images: {num_images}, ~{duration_per_image:.1f}s each")

    # Create image clips with Ken Burns effect
    image_clips = []
    for i, img_path in enumerate(image_paths):
        start_time = i * duration_per_image
        clip = create_ken_burns_clip(img_path, duration_per_image, config)
        clip = clip.with_start(start_time)

        # Add crossfade transition (except first clip)
        if i > 0 and video_config.get("transition") == "crossfade":
            clip = clip.crossfadein(transition_dur)

        image_clips.append(clip)

    # Composite: images + captions
    all_clips = image_clips
    caption_clips = create_caption_clips(captions, config)
    all_clips.extend(caption_clips)

    # Build final video
    final = CompositeVideoClip(
        all_clips,
        size=(video_config["width"], video_config["height"]),
    ).with_duration(total_duration)

    # Add audio
    final = final.with_audio(audio)

    # Add background music if specified
    bg_music_path = video_config.get("background_music")
    if bg_music_path and os.path.exists(bg_music_path):
        bg_music = AudioFileClip(bg_music_path)
        bg_music = bg_music.subclipped(0, min(bg_music.duration, total_duration))
        music_vol = video_config.get("music_volume", 0.15)
        bg_music = bg_music.with_effects([("volumex", music_vol)])
        from moviepy import CompositeAudioClip

        final_audio = CompositeAudioClip([audio, bg_music])
        final = final.with_audio(final_audio)

    # Generate output filename
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"short_{timestamp}.mp4")

    print(f"  Rendering video...")
    final.write_videofile(
        output_path,
        fps=video_config["fps"],
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        logger="bar",
    )

    # Cleanup
    audio.close()
    final.close()

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Output: {output_path} ({file_size_mb:.1f} MB)")

    return output_path


if __name__ == "__main__":
    config = load_config()
    # Test with existing files
    import glob

    images = sorted(glob.glob("temp/scene_*.png"))
    if images and os.path.exists("temp/voiceover.mp3"):
        from scripts.generate_captions import generate_captions

        caps = generate_captions("temp/voiceover.mp3", "temp/voiceover.srt", config)
        path = assemble_video(images, "temp/voiceover.mp3", caps, config)
        print(f"Video: {path}")
    else:
        print("Run other scripts first to generate test data.")
