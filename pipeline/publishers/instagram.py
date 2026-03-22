"""
Publisher — Instagram via instagrapi (no Facebook Business approval needed).
Uses Instagram username + password directly, like logging in on your phone.
Posts a carousel of the 5 generated slide images with the caption.
Session is cached so 2FA is only needed on first login.
"""

import os
import json
import time
from pathlib import Path
from typing import Optional

IG_USERNAME = os.environ.get("IG_USERNAME", "")
IG_PASSWORD = os.environ.get("IG_PASSWORD", "")
IG_PHONE = os.environ.get("IG_PHONE", "9458707534")  # for 2FA if triggered

SESSION_FILE = Path("/tmp/ig_session.json")


def _get_client():
    """Return an authenticated instagrapi Client."""
    try:
        from instagrapi import Client
        from instagrapi.exceptions import LoginRequired, TwoFactorRequired
    except ImportError:
        raise RuntimeError("instagrapi not installed. Add it to requirements.txt.")

    cl = Client()
    cl.delay_range = [2, 5]  # human-like delays between requests

    # Try loading existing session first
    if SESSION_FILE.exists():
        try:
            session = json.loads(SESSION_FILE.read_text())
            cl.set_settings(session)
            cl.login(IG_USERNAME, IG_PASSWORD)
            print("[instagram] Reused existing session")
            return cl
        except Exception:
            print("[instagram] Session expired, re-logging in...")
            SESSION_FILE.unlink(missing_ok=True)

    # Fresh login
    try:
        cl.login(IG_USERNAME, IG_PASSWORD)
    except TwoFactorRequired:
        # In GitHub Actions this won't work interactively — use session file instead
        print("[instagram] 2FA required — use session file approach")
        raise

    # Save session for future runs
    SESSION_FILE.write_text(json.dumps(cl.get_settings()))
    print("[instagram] Logged in fresh, session saved")
    return cl


def publish(content: dict, asset_paths: dict) -> dict:
    if not IG_USERNAME or not IG_PASSWORD:
        return {"success": False, "error": "IG_USERNAME or IG_PASSWORD not set"}

    # Find carousel images
    carousel = asset_paths.get("carousel", [])
    if not carousel:
        return {"success": False, "error": "No carousel images found"}

    # Filter to existing files only
    valid_images = [Path(p) for p in carousel if Path(p).exists()]
    if not valid_images:
        return {"success": False, "error": "Carousel image files not found on disk"}

    caption = content.get("instagram_caption", f"Day {content['day']} of learning Claude AI in public. 🤖\n\n#ClaudeAI #LearningInPublic #AIForEveryone")

    try:
        cl = _get_client()

        if len(valid_images) == 1:
            # Single image post
            media = cl.photo_upload(valid_images[0], caption=caption)
        else:
            # Carousel post (up to 10 images)
            media = cl.album_upload(valid_images[:10], caption=caption)

        post_url = f"https://www.instagram.com/p/{media.code}/"
        print(f"[instagram] Posted carousel → {post_url}")
        return {"success": True, "url": post_url, "id": str(media.pk)}

    except Exception as e:
        print(f"[instagram] Failed: {e}")
        return {"success": False, "error": str(e)}
