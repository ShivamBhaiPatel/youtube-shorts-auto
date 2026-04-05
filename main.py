"""YouTube Shorts Automation - One-click pipeline.

Generates a tech YouTube Short from scratch:
  Script (AI) -> Images (Stable Diffusion) -> Voice (Edge-TTS)
  -> Captions (Whisper) -> Video (MoviePy) -> Upload (YouTube API)

Usage:
  python main.py              # Generate and upload one video
  python main.py --no-upload  # Generate without uploading
  python main.py --schedule   # Run on daily schedule
  python main.py --topic "quantum computing"  # Specific topic
"""

import os
import sys
import json
import shutil
import argparse
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()  # loads .env file automatically

import yaml
from rich.console import Console
from rich.panel import Panel

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from scripts.generate_script import generate_script
from scripts.generate_images import generate_images, cleanup_pipeline
from scripts.generate_voice import generate_voice
from scripts.generate_captions import generate_captions
from scripts.assemble_video import assemble_video
from scripts.upload_youtube import upload_video

console = Console()


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def clean_temp(config):
    """Clean temp directory for fresh run."""
    temp_dir = config["paths"]["temp_dir"]
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)


def save_metadata(output_dir, script_data, video_path, upload_result=None):
    """Save video metadata for records."""
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "title": script_data.get("title", ""),
        "description": script_data.get("description", ""),
        "tags": script_data.get("tags", []),
        "script": script_data.get("script", ""),
        "video_path": video_path,
    }
    if upload_result:
        metadata["youtube"] = upload_result

    meta_path = video_path.replace(".mp4", "_meta.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    return meta_path


def run_pipeline(config, upload=True):
    """Run the full video generation pipeline."""
    start_time = datetime.now()

    console.print(Panel("[bold green]YouTube Shorts Auto Pipeline[/bold green]", expand=False))
    console.print()

    # Step 1: Generate Script
    console.print("[bold cyan]Step 1/6:[/bold cyan] Generating script...")
    script_data = generate_script(config)
    console.print(f"  Title: [bold]{script_data['title']}[/bold]")
    console.print(f"  Words: {len(script_data['script'].split())}")
    console.print(f"  Image prompts: {len(script_data['image_prompts'])}")
    console.print()

    # Step 2: Generate Images
    console.print("[bold cyan]Step 2/6:[/bold cyan] Generating images (Stable Diffusion)...")
    temp_dir = config["paths"]["temp_dir"]
    image_paths = generate_images(script_data["image_prompts"], config, temp_dir)
    console.print(f"  Generated {len(image_paths)} images.")
    console.print()

    # Free GPU memory before Whisper
    cleanup_pipeline()

    # Step 3: Generate Voiceover
    console.print("[bold cyan]Step 3/6:[/bold cyan] Generating voiceover (Edge-TTS)...")
    audio_path, srt_path = generate_voice(script_data["script"], config, temp_dir)
    console.print()

    # Step 4: Generate Captions
    console.print("[bold cyan]Step 4/6:[/bold cyan] Generating captions...")
    captions = generate_captions(audio_path, srt_path, config)
    console.print(f"  Caption entries: {len(captions)}")
    console.print()

    # Step 5: Assemble Video
    console.print("[bold cyan]Step 5/6:[/bold cyan] Assembling video...")
    output_dir = config["paths"]["output_dir"]
    video_path = assemble_video(image_paths, audio_path, captions, config, output_dir)
    console.print()

    # Step 6: Upload
    upload_result = None
    if upload:
        console.print("[bold cyan]Step 6/6:[/bold cyan] Uploading to YouTube...")
        title = script_data.get("title", "Tech Facts")
        description = script_data.get("description", "")
        tags = script_data.get("tags", [])
        upload_result = upload_video(video_path, title, description, tags, config)
        console.print()
    else:
        console.print("[bold yellow]Step 6/6:[/bold yellow] Upload skipped (--no-upload)")
        console.print()

    # Save metadata
    meta_path = save_metadata(output_dir, script_data, video_path, upload_result)

    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    console.print(Panel(
        f"[bold green]Pipeline Complete![/bold green]\n"
        f"  Video: {video_path}\n"
        f"  Metadata: {meta_path}\n"
        f"  Duration: {elapsed:.0f}s\n"
        + (f"  YouTube: {upload_result['url']}" if upload_result else "  YouTube: Not uploaded"),
        expand=False,
    ))

    return video_path, upload_result


def run_scheduler(config):
    """Run pipeline on a daily schedule."""
    import schedule as sched
    import time

    upload_time = config["schedule"]["upload_time"]
    videos_per_day = config["schedule"]["videos_per_day"]

    console.print(f"[bold]Scheduler active:[/bold] {videos_per_day} video(s)/day at {upload_time}")
    console.print("Press Ctrl+C to stop.\n")

    def job():
        for i in range(videos_per_day):
            console.print(f"\n[bold]Scheduled run {i + 1}/{videos_per_day}[/bold]")
            try:
                clean_temp(config)
                run_pipeline(config, upload=True)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")
                import traceback
                traceback.print_exc()

    sched.every().day.at(upload_time).do(job)

    # Also run immediately on first start
    console.print("[bold]Running first video now...[/bold]")
    job()

    while True:
        sched.run_pending()
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="YouTube Shorts Auto Pipeline")
    parser.add_argument("--no-upload", action="store_true", help="Skip YouTube upload")
    parser.add_argument("--schedule", action="store_true", help="Run on daily schedule")
    parser.add_argument("--topic", type=str, help="Specific topic override")
    args = parser.parse_args()

    config = load_config()
    os.makedirs(config["paths"]["output_dir"], exist_ok=True)
    os.makedirs(config["paths"]["temp_dir"], exist_ok=True)

    if args.topic:
        config["_topic_override"] = args.topic

    if args.schedule:
        run_scheduler(config)
    else:
        clean_temp(config)
        run_pipeline(config, upload=not args.no_upload)


if __name__ == "__main__":
    main()
