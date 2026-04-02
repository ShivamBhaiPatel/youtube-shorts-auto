"""Generate images using Stable Diffusion locally on RTX 2050."""

import os
import torch
import yaml
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler


_pipeline = None


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def get_pipeline(config):
    """Load and cache the Stable Diffusion pipeline."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    img_config = config["images"]
    model_id = img_config["model_id"]

    print(f"  Loading model: {model_id}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(
            f"  VRAM: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB"
        )

    # Use float16 for RTX 2050 (4GB VRAM)
    pipe = StableDiffusionXLPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True,
    )

    # Optimize for low VRAM
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.enable_model_cpu_offload()  # Offloads to CPU when not needed
    pipe.enable_vae_slicing()  # Reduces VRAM for VAE
    pipe.enable_vae_tiling()  # Tile-based VAE decoding

    _pipeline = pipe
    return pipe


def generate_images(image_prompts, config=None, output_dir=None):
    """Generate images from prompts using Stable Diffusion.

    Args:
        image_prompts: List of text prompts for image generation.
        config: Config dict (loaded from config.yaml if None).
        output_dir: Directory to save images (uses temp_dir if None).

    Returns:
        List of file paths to generated images.
    """
    if config is None:
        config = load_config()

    if output_dir is None:
        output_dir = config["paths"]["temp_dir"]

    os.makedirs(output_dir, exist_ok=True)

    img_config = config["images"]
    negative_prompt = img_config["negative_prompt"]

    pipe = get_pipeline(config)
    image_paths = []

    for i, prompt in enumerate(image_prompts):
        print(f"  Generating image {i + 1}/{len(image_prompts)}...")

        # Add quality boosters to prompt
        enhanced_prompt = (
            f"{prompt}, high quality, detailed, sharp focus, "
            f"professional, 4k uhd, trending on artstation"
        )

        image = pipe(
            prompt=enhanced_prompt,
            negative_prompt=negative_prompt,
            width=img_config["width"],
            height=img_config["height"],
            guidance_scale=img_config["guidance_scale"],
            num_inference_steps=img_config["num_inference_steps"],
            num_images_per_prompt=1,
        ).images[0]

        path = os.path.join(output_dir, f"scene_{i:02d}.png")
        image.save(path)
        image_paths.append(path)
        print(f"  Saved: {path}")

    return image_paths


def cleanup_pipeline():
    """Free GPU memory."""
    global _pipeline
    if _pipeline is not None:
        del _pipeline
        _pipeline = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("  Pipeline cleaned up, GPU memory freed.")


if __name__ == "__main__":
    config = load_config()
    test_prompts = [
        "futuristic AI brain made of circuits, digital art, cinematic lighting, 4k",
        "quantum computer glowing with blue energy, sci-fi, detailed, 4k",
    ]
    paths = generate_images(test_prompts, config)
    print(f"Generated: {paths}")
    cleanup_pipeline()
