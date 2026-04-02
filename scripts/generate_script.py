"""Generate video script and Stable Diffusion image prompts using AI."""

import json
import random
import yaml
import ollama as ollama_client

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


def generate_script(config=None):
    """Main entry point - generate a script with image prompts."""
    if config is None:
        config = load_config()

    topic, niche, subtopic = pick_topic(config)
    provider = config["script_generation"]["provider"]

    print(f"  Topic: {topic}")
    print(f"  Provider: {provider}")

    if provider == "ollama":
        result = generate_with_ollama(config, topic, niche, subtopic)
    elif provider == "claude":
        result = generate_with_claude(config, topic, niche, subtopic)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    # Validate required fields
    required = ["title", "script", "image_prompts"]
    for field in required:
        if field not in result:
            raise ValueError(f"Missing field in AI response: {field}")

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
