# Task Queue

Status: Phase 9 — Telegram Bot Integration
Last updated: 2026-04-05
Agent naming: Instance IDs — see .workflowstudio/CONTROL_CENTER.md

---

## YT-001
Title: Fix Gemini image generation quota / add HuggingFace Inference API fallback
Owner Agent: Codex-I1
Status: TODO
Priority: High
Why it matters: Gemini free tier returns limit:0, Pollinations is intermittent. Need a reliable free image provider.
Files involved:
- scripts/generate_images.py
- config.yaml
- requirements.txt
Acceptance criteria:
- HuggingFace Inference API added as a provider (free token, SDXL or Flux model)
- Fallback chain: Gemini → HuggingFace → Pollinations → local_sd
- Test: `python -m scripts.generate_images` produces 2 images successfully
Dependencies: None
Risks: HF free tier rate limits (unknown until tested)

---

## YT-002
Title: Add Telegram bot integration for pipeline control
Owner Agent: Codex-I1
Status: TODO
Priority: High
Why it matters: Control the pipeline from phone. Trigger runs, approve scripts, get notifications with video links.
Files involved:
- scripts/telegram_bot.py (new)
- main.py
- config.yaml
- requirements.txt
Acceptance criteria:
- `/generate` command triggers a full pipeline run
- `/status` shows current pipeline state
- Bot sends video link + thumbnail after successful upload
- Bot sends error message on failure
- Config: telegram section in config.yaml with bot_token_env and chat_id
Dependencies: None
Risks: Bot token must be regenerated (old one was exposed)

---

## YT-003
Title: Add multi-channel support with credential rotation
Owner Agent: Codex-I1
Status: TODO
Priority: Medium
Why it matters: Scale to 4-5 YouTube channels (AI Tools, Tech Tips, Deals, Coding) with separate branding and upload credentials.
Files involved:
- config.yaml
- scripts/upload_youtube.py
- main.py
Acceptance criteria:
- config.yaml supports `channels[]` array with per-channel: niche, topics, tags, credentials_file, token_file
- Pipeline selects channel based on rotation or explicit `--channel` arg
- Each channel uses its own OAuth2 credentials
- `python main.py --channel "ai-tools"` uploads to that specific channel
Dependencies: YT-002 (Telegram should know which channel)
Risks: YouTube API quota shared across channels (10,000 units/day default)

---

## YT-004
Title: Add thumbnail generation script
Owner Agent: Codex-I1
Status: TODO
Priority: Medium
Why it matters: Custom thumbnails increase CTR. Currently uploading without thumbnails.
Files involved:
- scripts/generate_thumbnail.py (new)
- scripts/upload_youtube.py
- main.py
- config.yaml
Acceptance criteria:
- Generates 1280x720 thumbnail from first scene image + title overlay
- Bold text, readable on mobile (large font, stroke/shadow)
- Integrates into pipeline between assemble_video and upload_youtube
- upload_youtube.py sends thumbnail with video
Dependencies: None
Risks: None significant

---

## YT-005
Title: End-to-end pipeline test run with upload
Owner Agent: Gemini-V1
Status: TODO
Priority: High
Why it matters: Verify full pipeline works: script → images → voice → captions → video → YouTube upload.
Files involved:
- main.py
- All scripts/
Acceptance criteria:
- `python main.py --no-upload` completes without errors, produces MP4 in output/
- `python main.py` uploads successfully to YouTube (unlisted for testing)
- Output video is <60s, 1080x1920, has captions, has audio
Dependencies: YT-001 (image gen must work)
Risks: Gemini quota may block; use Pollinations or local_sd as fallback

---
