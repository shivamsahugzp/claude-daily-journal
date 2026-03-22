"""
Publisher — Instagram Graph API.
Posts a carousel (multi-image) with the 5 generated slide images.
Requires: Instagram Business/Creator account connected to a Facebook Page.
"""
import os
import time
import httpx
from pathlib import Path


IG_USER_ID = os.environ.get("IG_USER_ID", "")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")  # long-lived token
BASE_URL = "https://graph.facebook.com/v19.0"

# Images must be hosted at a public URL for the IG API.
# We use GitHub raw URLs since the repo is public.
GITHUB_RAW_BASE = os.environ.get("GITHUB_RAW_BASE", "")  # e.g. https://raw.githubusercontent.com/shivamsahugzp/claude-daily-journal/main


def _image_url(date_str: str, filename: str) -> str:
    return f"{GITHUB_RAW_BASE}/journal/{date_str}/{filename}?t={int(time.time())}"


def _create_image_container(image_url: str, is_carousel_item: bool = True) -> str:
    params = {
        "image_url": image_url,
        "is_carousel_item": "true" if is_carousel_item else "false",
        "access_token": IG_ACCESS_TOKEN,
    }
    resp = httpx.post(f"{BASE_URL}/{IG_USER_ID}/media", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("id")


def _create_carousel_container(children: list[str], caption: str) -> str:
    params = {
        "media_type": "CAROUSEL",
        "children": ",".join(children),
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN,
    }
    resp = httpx.post(f"{BASE_URL}/{IG_USER_ID}/media", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("id")


def _publish_container(container_id: str) -> dict:
    params = {
        "creation_id": container_id,
        "access_token": IG_ACCESS_TOKEN,
    }
    resp = httpx.post(f"{BASE_URL}/{IG_USER_ID}/media_publish", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def publish(content: dict, asset_paths: dict) -> dict:
    if not IG_USER_ID or not IG_ACCESS_TOKEN or not GITHUB_RAW_BASE:
        return {"success": False, "error": "Instagram credentials not fully set"}

    date_str = content["date"]
    carousel_files = [f"carousel_{i}.png" for i in range(1, 6)]

    try:
        # Create individual image containers
        child_ids = []
        for filename in carousel_files:
            url = _image_url(date_str, filename)
            container_id = _create_image_container(url)
            child_ids.append(container_id)
            time.sleep(1)

        # Create carousel container
        carousel_id = _create_carousel_container(child_ids, content["instagram_caption"])
        time.sleep(5)  # IG requires wait before publishing

        # Publish
        result = _publish_container(carousel_id)
        post_id = result.get("id", "")
        url = f"https://www.instagram.com/p/{post_id}/" if post_id else ""
        print(f"[instagram] Posted carousel → {url}")
        return {"success": True, "url": url, "id": post_id}
    except Exception as e:
        print(f"[instagram] Failed: {e}")
        return {"success": False, "error": str(e)}
