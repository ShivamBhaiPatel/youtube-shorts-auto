"""Upload video to YouTube using YouTube Data API v3."""

import os
import json
import yaml
import httplib2
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def get_authenticated_service(config):
    """Authenticate and return YouTube API service."""
    yt_config = config["youtube"]
    credentials = None

    token_file = yt_config["token_file"]
    creds_file = yt_config["credentials_file"]

    # Load existing token
    if os.path.exists(token_file):
        credentials = Credentials.from_authorized_user_file(token_file, SCOPES)

    # Refresh or get new credentials
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("  Refreshing access token...")
            credentials.refresh(Request())
        else:
            if not os.path.exists(creds_file):
                raise FileNotFoundError(
                    f"Missing {creds_file}. Download OAuth2 credentials from "
                    "Google Cloud Console > APIs & Services > Credentials."
                )
            print("  Starting OAuth2 flow (browser will open)...")
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            credentials = flow.run_local_server(port=0)

        # Save token for next time
        with open(token_file, "w") as f:
            f.write(credentials.to_json())
        print("  Token saved.")

    return build("youtube", "v3", credentials=credentials)


def upload_video(
    video_path, title, description, tags=None, config=None, thumbnail_path=None
):
    """Upload a video to YouTube.

    Args:
        video_path: Path to the video file.
        title: Video title.
        description: Video description.
        tags: List of tags.
        config: Config dict.
        thumbnail_path: Optional thumbnail image path.

    Returns:
        Dict with video_id and url.
    """
    if config is None:
        config = load_config()

    yt_config = config["youtube"]

    # Apply title prefix/suffix
    full_title = f"{yt_config.get('title_prefix', '')}{title}{yt_config.get('title_suffix', '')}"
    # YouTube title limit is 100 chars
    full_title = full_title[:100]

    if tags is None:
        tags = yt_config["default_tags"]
    else:
        # Merge with default tags
        all_tags = list(set(tags + yt_config["default_tags"]))
        tags = all_tags[:30]  # YouTube limit is ~500 chars total

    youtube = get_authenticated_service(config)

    body = {
        "snippet": {
            "title": full_title,
            "description": description,
            "tags": tags,
            "categoryId": yt_config["category_id"],
        },
        "status": {
            "privacyStatus": yt_config["privacy_status"],
            "selfDeclaredMadeForKids": yt_config["made_for_kids"],
        },
    }

    print(f"  Uploading: {full_title}")
    print(f"  Privacy: {yt_config['privacy_status']}")
    print(f"  File: {video_path}")

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024,  # 1MB chunks
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    # Upload with progress
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"  Upload progress: {progress}%")

    video_id = response["id"]
    video_url = f"https://youtube.com/shorts/{video_id}"

    print(f"  Upload complete!")
    print(f"  Video ID: {video_id}")
    print(f"  URL: {video_url}")

    # Set thumbnail if provided
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/png"),
            ).execute()
            print(f"  Thumbnail set: {thumbnail_path}")
        except Exception as e:
            print(f"  Warning: Could not set thumbnail: {e}")

    return {"video_id": video_id, "url": video_url}


if __name__ == "__main__":
    config = load_config()
    print("YouTube uploader ready.")
    print("To test, run: python -m scripts.upload_youtube")
    print("Make sure client_secrets.json exists in project root.")
