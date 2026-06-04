"""Publisher — Meta Threads API."""
import os
import httpx
import time


THREADS_USER_ID = os.environ.get("THREADS_USER_ID", "")
THREADS_ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")
BASE_URL = "https://graph.threads.net/v1.0"


def _create_container(text: str) -> str:
    """Step 1: Create a media container."""
    resp = httpx.post(
        f"{BASE_URL}/{THREADS_USER_ID}/threads",
        params={
            "media_type": "TEXT",
            "text": text,
            "access_token": THREADS_ACCESS_TOKEN,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json().get("id")


def _publish_container(container_id: str) -> dict:
    """Step 2: Publish the container."""
    resp = httpx.post(
        f"{BASE_URL}/{THREADS_USER_ID}/threads_publish",
        params={
            "creation_id": container_id,
            "access_token": THREADS_ACCESS_TOKEN,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def publish(content: dict) -> dict:
    if not THREADS_USER_ID or not THREADS_ACCESS_TOKEN:
        return {"success": False, "error": "THREADS credentials not set"}

    try:
        container_id = _create_container(content["threads_post"])
        time.sleep(3)  # Threads API requires a brief wait
        result = _publish_container(container_id)
        post_id = result.get("id", "")
        url = f"https://www.threads.net/@shivamsahu/post/{post_id}" if post_id else ""
        print(f"[threads] Posted → {url}")
        return {"success": True, "url": url, "id": post_id}
    except Exception as e:
        print(f"[threads] Failed: {e}")
        return {"success": False, "error": str(e)}
