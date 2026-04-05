"""Generate video script and Stable Diffusion image prompts using AI."""

import json
import random
import yaml
import ollama as ollama_client
from dotenv import load_dotenv
load_dotenv()

SYSTEM_PROMPT = """You are a viral YouTube Shorts scriptwriter for tech content.
You write short, punchy, engaging scripts about technology facts and trends.

Rules:
- Script must be under {max_words} words (for a ~{duration}s video)
- Start with a HOOK in the first sentence (surprising fact, question, bold claim)
- Use simple language, short sentences
- End with a mind-blowing conclusion or call to action
- No emojis, no hashtags, just clean narration text

You must also generate image prompts for Stable Diffusion to create visuals.

Respond in this exact JSON format:
{{
    "title": "Short catchy title for YouTube (under 70 chars)",
    "description": "YouTube description (2-3 sentences with keywords)",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
    "script": "The full narration script text...",
    "image_prompts": [
        "detailed SD prompt for scene 1, digital art, 4k, cinematic lighting",
        "detailed SD prompt for scene 2, digital art, 4k, cinematic lighting",
        "detailed SD prompt for scene 3, digital art, 4k, cinematic lighting",
        "detailed SD prompt for scene 4, digital art, 4k, cinematic lighting",
        "detailed SD prompt for scene 5, digital art, 4k, cinematic lighting"
    ]
}}"""

USER_PROMPT = """Write a YouTube Shorts script about: {topic}

Topic area: {niche} / {subtopic}
Target duration: {duration} seconds
Max words: {max_words}
Number of image scenes: {num_images}

Make it fascinating and shareable. The image prompts should be vivid,
detailed descriptions for AI image generation - each representing a key
visual moment in the script. Include style keywords like 'digital art',
'cinematic lighting', '4k', 'futuristic' etc."""


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def pick_topic(config):
    """Pick a random topic from config or generate a specific one."""
    topics = config["content"]["topics"]
    niche = config["content"]["niche"]
    subtopic = random.choice(topics)

    topic_ideas = [
        f"A surprising fact about {subtopic} that most people don't know",
        f"How {subtopic} is changing the world right now",
        f"The most mind-blowing thing about {subtopic}",
        f"Why {subtopic} matters more than you think",
        f"The future of {subtopic} will shock you",
        f"Something incredible about {subtopic} that happened recently",
        f"The hidden truth about {subtopic}",
        f"How {subtopic} works in a way you never expected",
    ]

    return random.choice(topic_ideas), niche, subtopic


def generate_with_ollama(config, topic, niche, subtopic):
    """Generate script using local Ollama (free)."""
    ollama_config = config["script_generation"]["ollama"]
    content_config = config["content"]

    system = SYSTEM_PROMPT.format(
        max_words=content_config["max_words"],
        duration=content_config["duration_seconds"],
    )
    user = USER_PROMPT.format(
        topic=topic,
        niche=niche,
        subtopic=subtopic,
        duration=content_config["duration_seconds"],
        max_words=content_config["max_words"],
        num_images=config["images"]["num_images"],
    )

    response = ollama_client.chat(
        model=ollama_config["model"],
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        format="json",
        options={"temperature": 0.8},
    )

    return json.loads(response["message"]["content"])


def generate_with_claude(config, topic, niche, subtopic):
    """Generate script using Claude API (paid, better quality)."""
    import anthropic
    import os

    content_config = config["content"]
    claude_config = config["script_generation"]["claude"]

    api_key = os.environ.get(claude_config["api_key_env"])
    if not api_key:
        raise ValueError(
            f"Set {claude_config['api_key_env']} environment variable for Claude API"
        )

    client = anthropic.Anthropic(api_key=api_key)

    system = SYSTEM_PROMPT.format(
        max_words=content_config["max_words"],
        duration=content_config["duration_seconds"],
    )
    user = USER_PROMPT.format(
        topic=topic,
        niche=niche,
        subtopic=subtopic,
        duration=content_config["duration_seconds"],
        max_words=content_config["max_words"],
        num_images=config["images"]["num_images"],
    )

    message = client.messages.create(
        model=claude_config["model"],
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"{system}\n\n{user}\n\nRespond with valid JSON only.",
            }
        ],
    )

    response_text = message.content[0].text
    # Extract JSON from response
    start = response_text.find("{")
    end = response_text.rfind("}") + 1
    return json.loads(response_text[start:end])


def generate_with_gemini(config, topic, niche, subtopic):
    """Generate script using Gemini API — reuses existing GEMINI_API_KEY."""
    import os
    from google import genai
    from google.genai import types

    gemini_config = config["script_generation"]["gemini"]
    content_config = config["content"]

    api_key = os.environ.get(gemini_config["api_key_env"])
    if not api_key:
        raise ValueError(
            f"Set {gemini_config['api_key_env']} environment variable for Gemini API"
        )

    client = genai.Client(api_key=api_key)

    system = SYSTEM_PROMPT.format(
        max_words=content_config["max_words"],
        duration=content_config["duration_seconds"],
    )
    user = USER_PROMPT.format(
        topic=topic,
        niche=niche,
        subtopic=subtopic,
        duration=content_config["duration_seconds"],
        max_words=content_config["max_words"],
        num_images=config["images"]["num_images"],
    )

    response = client.models.generate_content(
        model=gemini_config["model"],
        contents=user + "\n\nRespond with valid JSON only.",
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.8,
            response_mime_type="application/json",
        ),
    )

    return json.loads(response.text)


def generate_with_huggingface(config, topic, niche, subtopic):
    """Generate script using HuggingFace model with TurboQuant KV cache compression.
    Runs entirely on CPU (RAM), keeping VRAM free for SDXL and Whisper.
    """
    import gc
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM

    hf_config = config["script_generation"]["huggingface"]
    content_config = config["content"]
    model_id = hf_config["model"]
    bits = hf_config.get("turbo_quant_bits", 4)

    print(f"  Loading model: {model_id}")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="cpu",
    )
    model.eval()

    # Apply TurboQuant KV cache compression
    try:
        from turboquant import TurboQuantCache
        cache = TurboQuantCache(bits=bits)
        print(f"  TurboQuant: {bits}-bit KV cache (~6x less RAM during inference)")
        use_turbo = True
    except ImportError:
        cache = None
        use_turbo = False
        print("  TurboQuant not installed — run: pip install turboquant")

    system = SYSTEM_PROMPT.format(
        max_words=content_config["max_words"],
        duration=content_config["duration_seconds"],
    )
    user = USER_PROMPT.format(
        topic=topic,
        niche=niche,
        subtopic=subtopic,
        duration=content_config["duration_seconds"],
        max_words=content_config["max_words"],
        num_images=config["images"]["num_images"],
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user + "\n\nRespond with valid JSON only."},
    ]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(prompt, return_tensors="pt")

    generate_kwargs = dict(
        max_new_tokens=1024,
        temperature=0.8,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )
    if use_turbo:
        generate_kwargs["past_key_values"] = cache
        generate_kwargs["use_cache"] = True

    with torch.no_grad():
        outputs = model.generate(**inputs, **generate_kwargs)

    new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    response_text = tokenizer.decode(new_tokens, skip_special_tokens=True)

    # Free RAM
    del model
    gc.collect()

    start = response_text.find("{")
    end = response_text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON found in HuggingFace response")

    return json.loads(response_text[start:end])


def _normalize_result(result):
    """Normalize AI response keys — local models often use variant names."""
    # Normalize image_prompts from common variants
    if "image_prompts" not in result:
        for key in ("images", "image_prompt", "prompts", "scenes", "visual_prompts"):
            if key in result and isinstance(result[key], list):
                result["image_prompts"] = result.pop(key)
                break

    # Normalize script from common variants
    if "script" not in result:
        for key in ("narration", "text", "voiceover", "content", "body"):
            if key in result and isinstance(result[key], str):
                result["script"] = result.pop(key)
                break

    return result


def generate_script(config=None, max_retries=3):
    """Main entry point - generate a script with image prompts."""
    if config is None:
        config = load_config()

    topic, niche, subtopic = pick_topic(config)
    provider = config["script_generation"]["provider"]

    print(f"  Topic: {topic}")
    print(f"  Provider: {provider}")

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            if provider == "ollama":
                result = generate_with_ollama(config, topic, niche, subtopic)
            elif provider == "claude":
                result = generate_with_claude(config, topic, niche, subtopic)
            elif provider == "gemini":
                result = generate_with_gemini(config, topic, niche, subtopic)
            elif provider == "huggingface":
                result = generate_with_huggingface(config, topic, niche, subtopic)
            else:
                raise ValueError(f"Unknown provider: {provider}")

            result = _normalize_result(result)

            # Validate required fields
            required = ["title", "script", "image_prompts"]
            for field in required:
                if field not in result:
                    raise ValueError(f"Missing field in AI response: {field}")

            break  # success
        except (ValueError, json.JSONDecodeError, KeyError) as e:
            last_error = e
            if attempt < max_retries:
                print(f"  Attempt {attempt} failed ({e}), retrying...")
            else:
                raise ValueError(
                    f"Failed after {max_retries} attempts. Last error: {last_error}"
                )

    # Ensure we have enough image prompts
    num_needed = config["images"]["num_images"]
    while len(result["image_prompts"]) < num_needed:
        result["image_prompts"].append(result["image_prompts"][-1])

    result["image_prompts"] = result["image_prompts"][:num_needed]

    # Add defaults for optional fields
    result.setdefault("description", "")
    result.setdefault("tags", config["youtube"]["default_tags"])

    return result


if __name__ == "__main__":
    from rich import print as rprint

    result = generate_script()
    rprint(result)
