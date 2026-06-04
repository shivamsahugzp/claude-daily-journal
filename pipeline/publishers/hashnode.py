"""Publisher — Hashnode (GraphQL API)."""
import os
import re
import httpx


HASHNODE_TOKEN = os.environ.get("HASHNODE_TOKEN", "")
HASHNODE_PUBLICATION_ID = os.environ.get("HASHNODE_PUBLICATION_ID", "")
BASE_URL = "https://gql.hashnode.com"


def _strip_frontmatter(article: str) -> str:
    if article.startswith("---"):
        end = article.find("---", 3)
        if end != -1:
            return article[end + 3:].strip()
    return article


def _extract_tags(article: str) -> list[dict]:
    match = re.search(r'topics:\s*\[(.+?)\]', article)
    if not match:
        return [{"name": "Claude AI"}, {"name": "AI"}, {"name": "Beginners"}]
    raw = match.group(1).replace('"', '').replace("'", "")
    tags = [t.strip() for t in raw.split(",")]
    return [{"name": t.replace("-", " ").title()} for t in tags[:5]]


def publish(content: dict) -> dict:
    if not HASHNODE_TOKEN or not HASHNODE_PUBLICATION_ID:
        return {"success": False, "error": "HASHNODE_TOKEN or HASHNODE_PUBLICATION_ID not set"}

    body = _strip_frontmatter(content["article"])

    mutation = """
    mutation PublishPost($input: PublishPostInput!) {
      publishPost(input: $input) {
        post {
          id
          url
          title
        }
      }
    }
    """

    variables = {
        "input": {
            "title": content["title"],
            "contentMarkdown": body,
            "publicationId": HASHNODE_PUBLICATION_ID,
            "tags": _extract_tags(content["article"]),
            "subtitle": content["tip"][:160],
        }
    }

    try:
        resp = httpx.post(
            BASE_URL,
            headers={
                "Authorization": HASHNODE_TOKEN,
                "Content-Type": "application/json",
            },
            json={"query": mutation, "variables": variables},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        errors = data.get("errors")
        if errors:
            print(f"[hashnode] GraphQL errors: {errors}")
            return {"success": False, "error": str(errors)}

        post = data.get("data", {}).get("publishPost", {}).get("post", {})
        url = post.get("url", "")
        print(f"[hashnode] Published → {url}")
        return {"success": True, "url": url, "id": post.get("id")}
    except Exception as e:
        print(f"[hashnode] Failed: {e}")
        return {"success": False, "error": str(e)}
