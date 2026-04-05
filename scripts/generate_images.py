"""Generate images using Gemini (primary), Pollinations (fallback), or local SD."""

import os
import time
import yaml
import requests
from io import BytesIO
from urllib.parse import quote
from PIL import Image
from dotenv import load_dotenv
load_dotenv()


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Gemini Imagen (google-genai SDK)
# ---------------------------------------------------------------------------

def generate_images_gemini(image_prompts, config, output_dir):
    """Generate images using Gemini native image generation (free tier)."""
    from google import genai
    from google.genai import types

    img_config = config["images"]
    gemini_config = img_config.get("gemini", {})
    api_key = os.environ.get(gemini_config.get("api_key_env", "GEMINI_API_KEY"))

    if not api_key:
        raise ValueError(
            "Set GEMINI_API_KEY environment variable. "
            "Get one free at https://aistudio.google.com/apikey"
        )

    client = genai.Client(api_key=api_key)
    model = gemini_config.get("model", "gemini-2.5-flash-preview-image-generation")
    aspect_ratio = gemini_config.get("aspect_ratio", "9:16")

    print(f"  Provider: Gemini ({model})")
    print(f"  Aspect ratio: {aspect_ratio}")

    image_paths = []
    for i, prompt in enumerate(image_prompts):
        print(f"  Generating image {i + 1}/{len(image_prompts)}...")

        enhanced_prompt = (
            f"Generate a high quality, vivid, cinematic image of: {prompt}. "
            f"Style: digital art, 4k, detailed, sharp focus, professional."
        )

        response = client.models.generate_content(
            model=model,
            contents=enhanced_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                ),
            ),
        )

        # Extract image from response
        saved = False
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                image_data = part.inline_data.data
                image = Image.open(BytesIO(image_data))
                path = os.path.join(output_dir, f"scene_{i:02d}.png")
                image.save(path)
                image_paths.append(path)
                print(f"  Saved: {path}")
                saved = True
                break

        if not saved:
            raise RuntimeError(
                f"Gemini returned no image for prompt {i + 1} "
                "(possibly filtered by safety). Try a different prompt."
            )

    return image_paths


# ---------------------------------------------------------------------------
# Pollinations.ai (completely free, no API key)
# ---------------------------------------------------------------------------

def generate_images_pollinations(image_prompts, config, output_dir):
    """Generate images using Pollinations.ai (free, no API key needed)."""
    img_config = config["images"]
    poll_config = img_config.get("pollinations", {})
    width = poll_config.get("width", 768)
    height = poll_config.get("height", 1344)
    model = poll_config.get("model", "flux")

    print(f"  Provider: Pollinations.ai ({model})")
    print(f"  Size: {width}x{height}")

    image_paths = []
    for i, prompt in enumerate(image_prompts):
        print(f"  Generating image {i + 1}/{len(image_prompts)}...")

        enhanced_prompt = (
            f"{prompt}, high quality, detailed, sharp focus, "
            f"digital art, 4k uhd, cinematic lighting"
        )

        url = (
            f"https://image.pollinations.ai/prompt/{quote(enhanced_prompt)}"
            f"?width={width}&height={height}&model={model}&nologo=true&seed={int(time.time()) + i}"
        )

        # Retry with longer timeout — Pollinations can be slow on first request
        resp = None
        for attempt in range(3):
            try:
                resp = requests.get(url, timeout=180)
                resp.raise_for_status()
                break
            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt < 2:
                    print(f"  Retry {attempt + 1}/3 for image {i + 1}...")
                    time.sleep(5)
                else:
                    raise

        path = os.path.join(output_dir, f"scene_{i:02d}.png")
        image = Image.open(BytesIO(resp.content))
        image.save(path)
        image_paths.append(path)
        print(f"  Saved: {path}")

    return image_paths


# ---------------------------------------------------------------------------
# Local Stable Diffusion (GPU required, slow on low VRAM)
# ---------------------------------------------------------------------------

_pipeline = None


def _get_sd_pipeline(config):
    """Load and cache the Stable Diffusion pipeline."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    import torch
    from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler

    img_config = config["images"]
    model_id = img_config.get("sd_model_id", "stabilityai/stable-diffusion-xl-base-1.0")

    print(f"  Loading model: {model_id}")
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    pipe = StableDiffusionXLPipeline.from_pretrained(
        model_id, torch_dtype=torch.float16, variant="fp16", use_safetensors=True,
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.enable_model_cpu_offload()
    pipe.enable_vae_slicing()
    pipe.enable_vae_tiling()

    _pipeline = pipe
    return pipe


def generate_images_local_sd(image_prompts, config, output_dir):
    """Generate images using local Stable Diffusion (GPU)."""
    img_config = config["images"]
    negative_prompt = img_config.get("negative_prompt", "")

    pipe = _get_sd_pipeline(config)
    image_paths = []

    for i, prompt in enumerate(image_prompts):
        print(f"  Generating image {i + 1}/{len(image_prompts)}...")
        enhanced_prompt = (
            f"{prompt}, high quality, detailed, sharp focus, "
            f"professional, 4k uhd, trending on artstation"
        )
        image = pipe(
            prompt=enhanced_prompt,
            negative_prompt=negative_prompt,
            width=img_config.get("width", 768),
            height=img_config.get("height", 1344),
            guidance_scale=img_config.get("guidance_scale", 7.5),
            num_inference_steps=img_config.get("num_inference_steps", 30),
            num_images_per_prompt=1,
        ).images[0]

        path = os.path.join(output_dir, f"scene_{i:02d}.png")
        image.save(path)
        image_paths.append(path)
        print(f"  Saved: {path}")

    return image_paths


# ---------------------------------------------------------------------------
# Public API (used by main.py)
# ---------------------------------------------------------------------------

PROVIDERS = {
    "gemini": generate_images_gemini,
    "pollinations": generate_images_pollinations,
    "local_sd": generate_images_local_sd,
}


def generate_images(image_prompts, config=None, output_dir=None):
    """Generate images using configured provider with fallback.

    Provider priority: config provider → pollinations fallback.
    """
    if config is None:
        config = load_config()

    if output_dir is None:
        output_dir = config["paths"]["temp_dir"]

    os.makedirs(output_dir, exist_ok=True)

    img_config = config["images"]
    provider = img_config.get("provider", "gemini")
    fallback = img_config.get("fallback_provider", "pollinations")

    gen_func = PROVIDERS.get(provider)
    if not gen_func:
        raise ValueError(f"Unknown image provider: {provider}. Use: {list(PROVIDERS.keys())}")

    try:
        return gen_func(image_prompts, config, output_dir)
    except Exception as e:
        if fallback and fallback != provider:
            print(f"  [!] {provider} failed: {e}")
            print(f"  [!] Falling back to {fallback}...")
            fallback_func = PROVIDERS.get(fallback)
            if fallback_func:
                return fallback_func(image_prompts, config, output_dir)
        raise


def cleanup_pipeline():
    """Free GPU memory (only needed for local_sd)."""
    global _pipeline
    if _pipeline is not None:
        import torch
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
