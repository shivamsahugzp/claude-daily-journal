"""
Publisher — LinkedIn API.
Posts a text article post with image attachment.
Note: LinkedIn API for articles requires special partner access.
This implementation posts a rich text update (available to all) with the
full article content as a document/post, which is publicly visible.
"""
import os
import httpx
import json


LI_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
LI_PERSON_URN = os.environ.get("LINKEDIN_PERSON_URN", "")  # urn:li:person:XXXXX
BASE_URL = "https://api.linkedin.com/v2"


def _get_person_urn() -> str:
    """Fetch the authenticated user's URN if not set."""
    if LI_PERSON_URN:
        return LI_PERSON_URN
    resp = httpx.get(
        f"{BASE_URL}/me",
        headers={"Authorization": f"Bearer {LI_ACCESS_TOKEN}"},
        timeout=15,
    )
    resp.raise_for_status()
    person_id = resp.json().get("id", "")
    return f"urn:li:person:{person_id}"


def publish(content: dict, devto_url: str = "", hashnode_url: str = "") -> dict:
    if not LI_ACCESS_TOKEN:
        return {"success": False, "error": "LINKEDIN_ACCESS_TOKEN not set"}

    try:
        urn = _get_person_urn()

        # Add article link at end of post
        post_text = content["linkedin_post"]
        if devto_url:
            post_text += f"\n\n📖 Full article: {devto_url}"
        elif hashnode_url:
            post_text += f"\n\n📖 Full article: {hashnode_url}"

        payload = {
            "author": urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": post_text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        resp = httpx.post(
            f"{BASE_URL}/ugcPosts",
            headers={
                "Authorization": f"Bearer {LI_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        post_id = resp.headers.get("x-restli-id", "")
        print(f"[linkedin] Posted → post ID: {post_id}")
        return {"success": True, "id": post_id}
    except Exception as e:
        print(f"[linkedin] Failed: {e}")
        return {"success": False, "error": str(e)}
