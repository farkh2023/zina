"""
config/settings.py — Centralised configuration for the YouTube AI pipeline.
All values are loaded from environment variables (see .env).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file)
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# ── Paths ─────────────────────────────────────────────────────────────────────
INPUT_SCRIPT        = ROOT_DIR / os.getenv("INPUT_SCRIPT", "input/script.md")
OUTPUT_DIR          = ROOT_DIR / os.getenv("OUTPUT_DIR", "output")
OUTPUT_AUDIO_DIR    = ROOT_DIR / os.getenv("OUTPUT_AUDIO_DIR", "output/audio")
OUTPUT_IMAGES_DIR   = ROOT_DIR / os.getenv("OUTPUT_IMAGES_DIR", "output/images")
OUTPUT_CLIPS_DIR    = ROOT_DIR / os.getenv("OUTPUT_CLIPS_DIR", "output/clips")
OUTPUT_THUMBNAIL_DIR= ROOT_DIR / os.getenv("OUTPUT_THUMBNAIL_DIR", "output/thumbnail")
OUTPUT_VIDEO_DIR    = ROOT_DIR / os.getenv("OUTPUT_VIDEO_DIR", "output/video")

# Ensure all output directories exist
for _dir in (
    OUTPUT_DIR, OUTPUT_AUDIO_DIR, OUTPUT_IMAGES_DIR,
    OUTPUT_CLIPS_DIR, OUTPUT_THUMBNAIL_DIR, OUTPUT_VIDEO_DIR,
):
    _dir.mkdir(parents=True, exist_ok=True)

# ── OpenAI ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY", "")
OPENAI_TTS_MODEL    = os.getenv("OPENAI_TTS_MODEL", "tts-1-hd")
OPENAI_TTS_VOICE    = os.getenv("OPENAI_TTS_VOICE", "alloy")
OPENAI_IMAGE_MODEL  = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
OPENAI_IMAGE_SIZE   = os.getenv("OPENAI_IMAGE_SIZE", "1792x1024")

# ── YouTube ───────────────────────────────────────────────────────────────────
YOUTUBE_CLIENT_SECRETS_FILE = ROOT_DIR / os.getenv(
    "YOUTUBE_CLIENT_SECRETS_FILE", "config/client_secrets.json"
)
YOUTUBE_CREDENTIALS_FILE = ROOT_DIR / os.getenv(
    "YOUTUBE_CREDENTIALS_FILE", "config/youtube_credentials.json"
)
YOUTUBE_API_SCOPES = os.getenv(
    "YOUTUBE_API_SCOPES",
    "https://www.googleapis.com/auth/youtube.upload",
).split(",")

# ── Video ─────────────────────────────────────────────────────────────────────
VIDEO_FPS                = int(os.getenv("VIDEO_FPS", "30"))
_res                     = os.getenv("VIDEO_RESOLUTION", "1920x1080").split("x")
VIDEO_WIDTH, VIDEO_HEIGHT= int(_res[0]), int(_res[1])
VIDEO_TRANSITION_DURATION= float(os.getenv("VIDEO_TRANSITION_DURATION", "0.5"))
AUDIO_FADE_DURATION      = float(os.getenv("AUDIO_FADE_DURATION", "1.0"))
