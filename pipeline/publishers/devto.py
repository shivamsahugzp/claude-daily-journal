"""Publisher — dev.to (forem API)."""
import os
import re
import httpx


DEVTO_API_KEY = os.environ.get("DEVTO_API_KEY", "")
BASE_URL = "https://dev.to/api"


def _extract_tags(article: str) -> list[str]:
    match = re.search(r'topics:\s*\[(.+?)\]', article)
    if not match:
        return ["claudeai", "ai", "beginners", "productivity"]
    raw = match.group(1).replace('"', '').replace("'", "")
    tags = [t.strip().replace("-", "") for t in raw.split(",")]
    return tags[:4]


def _strip_frontmatter(article: str) -> str:
    if article.startswith("---"):
        end = article.find("---", 3)
        if end != -1:
            return article[end + 3:].strip()
    return article


def publish(content: dict) -> dict:
    if not DEVTO_API_KEY:
        return {"success": False, "error": "DEVTO_API_KEY not set"}

    body = _strip_frontmatter(content["article"])
    tags = _extract_tags(content["article"])

    payload = {
        "article": {
            "title": content["title"],
            "body_markdown": body,
            "published": True,
            "tags": tags,
            "description": content["tip"][:160],
        }
    }

    try:
        resp = httpx.post(
            f"{BASE_URL}/articles",
            headers={"api-key": DEVTO_API_KEY, "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        url = data.get("url", "")
        print(f"[devto] Published → {url}")
        return {"success": True, "url": url, "id": data.get("id")}
    except Exception as e:
        print(f"[devto] Failed: {e}")
        return {"success": False, "error": str(e)}
