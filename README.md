# YouTube AI Pipeline

Automated pipeline that converts a **Markdown script** into a fully produced
YouTube video using OpenAI (TTS + DALL-E 3) and the YouTube Data API v3.

```
Markdown script
      │
      ▼
 extraction_markdown  →  sections (title / narration / image prompt)
      │
      ▼
  nlp_processing      →  cleaned text + YouTube metadata
      │
      ├──► generate_audio     →  output/audio/section_XX.mp3   (OpenAI TTS)
      │
      ├──► generate_images    →  output/images/section_XX.png  (DALL-E 3)
      │
      ├──► generate_thumbnail →  output/thumbnail/thumbnail.png
      │
      ├──► assemble_video     →  output/video/final_video.mp4  (MoviePy)
      │
      └──► upload_youtube     →  YouTube (Data API v3)
```

---

## Requirements

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| FFmpeg | any recent | ← must be on your PATH |

---

## Installation

```bash
# 1. Clone / navigate to the project
cd MODEL_youtube_ai_pipeline

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install FFmpeg  (required by MoviePy and pydub)
#    Windows  : https://ffmpeg.org/download.html  (add bin/ to PATH)
#    macOS    : brew install ffmpeg
#    Ubuntu   : sudo apt install ffmpeg
```

---

## Configuration

### 1. OpenAI API key

Copy `.env` and fill in your key:

```
OPENAI_API_KEY=sk-...
```

### 2. YouTube OAuth credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable **YouTube Data API v3**.
3. Create an **OAuth 2.0 Desktop App** credential.
4. Download the JSON file and save it as:

```
config/client_secrets.json
```

> On first run the pipeline will open a browser window for OAuth consent.
> The resulting token is saved to `config/youtube_credentials.json`.

---

## Writing your script

Create (or edit) `input/script.md`.
Use **H1 / H2 / H3 headings** — each heading becomes one video slide.

```markdown
# My Amazing Video Title

## Introduction
Welcome to this video about...

## Chapter 1 — The Basics
<!-- img: Wide-angle photograph of a futuristic classroom, warm lighting -->
Here we explain the fundamentals...

## Conclusion
Thank you for watching!
```

> The optional `<!-- img: ... -->` HTML comment lets you override the
> auto-generated DALL-E prompt for that section.

---

## Running the pipeline

```bash
# Full run (generates everything + uploads as private)
python pipeline.py

# Custom script path
python pipeline.py --script path/to/my_script.md

# Skip upload (useful for testing)
python pipeline.py --no-upload

# Upload as public
python pipeline.py --privacy public

# Verbose / debug logging
python pipeline.py -v
```

---

## Output files

| Path | Content |
|------|---------|
| `output/audio/section_XX.mp3` | Narration audio per section |
| `output/images/section_XX.png` | DALL-E illustration per section |
| `output/thumbnail/thumbnail.png` | YouTube thumbnail (1280×720) |
| `output/video/final_video.mp4` | Final assembled video |

---

## Project structure

```
MODEL_youtube_ai_pipeline/
├── pipeline.py             # Main orchestrator (entry point)
├── extraction_markdown.py  # Markdown → Section objects
├── nlp_processing.py       # Text cleaning + metadata generation
├── generate_audio.py       # OpenAI TTS → MP3
├── generate_images.py      # DALL-E 3 → PNG
├── generate_thumbnail.py   # Pillow thumbnail composer
├── assemble_video.py       # MoviePy video assembler
├── upload_youtube.py       # YouTube Data API v3 uploader
├── config/
│   └── settings.py         # Centralised settings (reads .env)
├── input/
│   └── script.md           # Your Markdown script
├── output/                 # Generated artefacts (git-ignored)
│   ├── audio/
│   ├── images/
│   ├── clips/
│   ├── thumbnail/
│   └── video/
├── .env                    # Secret keys (git-ignored)
├── requirements.txt
└── README.md
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `FileNotFoundError: ffmpeg` | Install FFmpeg and add to PATH |
| `OPENAI_API_KEY is not set` | Check your `.env` file |
| `client_secrets.json not found` | See YouTube setup above |
| Upload quota exceeded | YouTube free tier: 6 uploads/day |
| Image generation error | Verify DALL-E 3 is enabled on your OpenAI account |
