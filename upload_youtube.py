"""
upload_youtube.py — Upload the final video to YouTube via the Data API v3.

Authentication flow:
  1. On first run, opens a browser OAuth consent screen and saves credentials
     to YOUTUBE_CREDENTIALS_FILE.
  2. On subsequent runs, the saved token is refreshed automatically.

The function returns the uploaded video's YouTube ID.
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path

import google_auth_oauthlib.flow as oauth_flow
import googleapiclient.discovery as gd
import googleapiclient.errors as ge
import googleapiclient.http as gh
from google.auth.transport.requests import Request

import config.settings as cfg

logger = logging.getLogger(__name__)

API_SERVICE  = "youtube"
API_VERSION  = "v3"
CHUNK_SIZE   = 1024 * 1024 * 8   # 8 MB resumable upload chunks


# ── Auth ──────────────────────────────────────────────────────────────────────

def _get_authenticated_service():
    creds = None
    creds_file = cfg.YOUTUBE_CREDENTIALS_FILE

    if creds_file.exists():
        with open(creds_file, "rb") as f:
            creds = pickle.load(f)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        if not cfg.YOUTUBE_CLIENT_SECRETS_FILE.exists():
            raise FileNotFoundError(
                f"YouTube client secrets not found: {cfg.YOUTUBE_CLIENT_SECRETS_FILE}\n"
                "Download it from the Google Cloud Console and place it at that path."
            )
        flow = oauth_flow.InstalledAppFlow.from_client_secrets_file(
            str(cfg.YOUTUBE_CLIENT_SECRETS_FILE),
            scopes=cfg.YOUTUBE_API_SCOPES,
        )
        creds = flow.run_local_server(port=0)

    # Persist credentials
    creds_file.parent.mkdir(parents=True, exist_ok=True)
    with open(creds_file, "wb") as f:
        pickle.dump(creds, f)

    return gd.build(API_SERVICE, API_VERSION, credentials=creds)


# ── Upload ────────────────────────────────────────────────────────────────────

def upload_video(
    video_path: Path,
    metadata: dict,
    thumbnail_path: Path | None = None,
    privacy: str = "private",
) -> str:
    """
    Upload *video_path* to YouTube.

    Args:
        video_path     : path to the final MP4
        metadata       : dict with 'title', 'description', 'tags'
        thumbnail_path : optional thumbnail PNG
        privacy        : 'private' | 'unlisted' | 'public'

    Returns:
        YouTube video ID string.
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    youtube = _get_authenticated_service()

    body = {
        "snippet": {
            "title":       metadata.get("title", "Untitled"),
            "description": metadata.get("description", ""),
            "tags":        metadata.get("tags", []),
            "categoryId":  "27",   # Education
        },
        "status": {
            "privacyStatus": privacy,
        },
    }

    media = gh.MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        chunksize=CHUNK_SIZE,
        resumable=True,
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    response = None
    logger.info("Uploading '%s' to YouTube…", video_path.name)
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            logger.info("  Upload progress: %d%%", pct)

    video_id = response.get("id", "")
    logger.info("Upload complete! Video ID: %s", video_id)

    # ── Thumbnail ──────────────────────────────────────────────────────────────
    if thumbnail_path and thumbnail_path.exists() and video_id:
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=gh.MediaFileUpload(str(thumbnail_path)),
            ).execute()
            logger.info("Thumbnail uploaded.")
        except ge.HttpError as exc:
            logger.warning("Thumbnail upload failed: %s", exc)

    return video_id
