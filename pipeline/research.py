"""
Research pipeline — searches web for latest Claude/Anthropic content daily.
Uses multiple free sources: Reddit, GitHub, HackerNews, web search.
"""

import os
import json
import httpx
from datetime import date, datetime, timedelta
from typing import Any


SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")
REDDIT_USER_AGENT = "claude-daily-journal/1.0 (by /u/shivamsahu)"

SEARCH_QUERIES = [
    "Claude AI new feature",
    "Anthropic Claude update",
    "Claude Code tips tricks",
    "Claude MCP server",
    "Claude prompt engineering",
    "Claude vs GPT",
    "Anthropic announcement",
    "Claude AI beginner guide",
]

REDDIT_SUBREDDITS = ["ClaudeAI", "anthropic", "artificial", "MachineLearning"]


def _web_search(query: str) -> list[dict]:
    """Search via Serper.dev free API (100 searches/month free)."""
    if not SERPER_API_KEY:
        return []
    try:
        resp = httpx.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": query, "num": 5, "tbs": "qdr:w"},  # last week
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("organic", [])
        return [
            {
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "url": r.get("link", ""),
                "source": "web",
            }
            for r in results[:3]
        ]
    except Exception as e:
        print(f"[research] web search failed: {e}")
        return []


def _reddit_search() -> list[dict]:
    """Fetch top posts from Claude subreddits (no API key needed)."""
    results = []
    for sub in REDDIT_SUBREDDITS:
        try:
            resp = httpx.get(
                f"https://www.reddit.com/r/{sub}/hot.json?limit=5",
                headers={"User-Agent": REDDIT_USER_AGENT},
                timeout=15,
            )
            resp.raise_for_status()
            posts = resp.json().get("data", {}).get("children", [])
            for p in posts[:2]:
                d = p.get("data", {})
                if "claude" in d.get("title", "").lower() or "anthropic" in d.get("title", "").lower():
                    results.append({
                        "title": d.get("title", ""),
                        "snippet": d.get("selftext", "")[:300],
                        "url": f"https://reddit.com{d.get('permalink', '')}",
                        "source": "reddit",
                        "score": d.get("score", 0),
                    })
        except Exception as e:
            print(f"[research] reddit {sub} failed: {e}")
    return results


def _hackernews_search() -> list[dict]:
    """Search HackerNews for Claude/Anthropic mentions."""
    results = []
    try:
        resp = httpx.get(
            "https://hn.algolia.com/api/v1/search?query=claude+anthropic&tags=story&hitsPerPage=5",
            timeout=15,
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
        for h in hits[:3]:
            created = h.get("created_at", "")
            # Only last 7 days
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if (datetime.now().astimezone() - dt).days > 7:
                    continue
            except Exception:
                pass
            results.append({
                "title": h.get("title", ""),
                "snippet": h.get("story_text", "")[:300] if h.get("story_text") else "",
                "url": h.get("url", f"https://news.ycombinator.com/item?id={h.get('objectID')}"),
                "source": "hackernews",
                "points": h.get("points", 0),
            })
    except Exception as e:
        print(f"[research] hackernews failed: {e}")
    return results


def _github_releases() -> list[dict]:
    """Check anthropics/claude-code and anthropics repos for new releases."""
    repos = ["anthropics/claude-code", "anthropics/anthropic-sdk-python", "anthropics/anthropic-sdk-js"]
    results = []
    headers = {}
    gh_token = os.environ.get("GITHUB_TOKEN", "")
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"

    for repo in repos:
        try:
            resp = httpx.get(
                f"https://api.github.com/repos/{repo}/releases?per_page=3",
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 404:
                continue
            resp.raise_for_status()
            releases = resp.json()
            for r in releases[:2]:
                published = r.get("published_at", "")
                try:
                    dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    if (datetime.now().astimezone() - dt).days > 14:
                        continue
                except Exception:
                    pass
                results.append({
                    "title": f"{repo} — {r.get('tag_name', '')}",
                    "snippet": (r.get("body", "") or "")[:400],
                    "url": r.get("html_url", ""),
                    "source": "github",
                })
        except Exception as e:
            print(f"[research] github {repo} failed: {e}")
    return results


def _anthropic_docs_topics() -> list[dict]:
    """Return static list of Anthropic learning topics to rotate through."""
    topics = [
        {"title": "Claude's extended thinking mode", "snippet": "Extended thinking lets Claude reason deeply before responding, using up to 31,999 tokens of internal scratchpad.", "url": "https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking", "source": "anthropic_docs"},
        {"title": "Claude Code slash commands", "snippet": "Slash commands like /commit, /review, /test let you trigger specific workflows inside Claude Code.", "url": "https://docs.anthropic.com/en/docs/claude-code", "source": "anthropic_docs"},
        {"title": "MCP — Model Context Protocol", "snippet": "MCP lets Claude connect to external tools like Slack, Notion, Jira, and databases via a standard protocol.", "url": "https://modelcontextprotocol.io", "source": "anthropic_docs"},
        {"title": "Claude API tool use", "snippet": "Tool use (function calling) lets Claude call your code, APIs, and databases to get real-time data.", "url": "https://docs.anthropic.com/en/docs/tool-use", "source": "anthropic_docs"},
        {"title": "Claude prompt caching", "snippet": "Prompt caching reduces cost by 90% and latency by 85% when reusing long system prompts.", "url": "https://docs.anthropic.com/en/docs/prompt-caching", "source": "anthropic_docs"},
        {"title": "Building agents with Claude", "snippet": "Agents let Claude autonomously complete multi-step tasks — browsing web, writing code, managing files.", "url": "https://docs.anthropic.com/en/docs/agents", "source": "anthropic_docs"},
        {"title": "Claude vision and image analysis", "snippet": "Claude can read, describe, and reason about images — screenshots, charts, documents, photos.", "url": "https://docs.anthropic.com/en/docs/vision", "source": "anthropic_docs"},
        {"title": "Anthropic courses — free AI learning", "snippet": "Anthropic offers free prompt engineering and AI safety courses on their official learning platform.", "url": "https://www.anthropic.com/learn", "source": "anthropic_docs"},
    ]
    # Rotate based on day of year
    idx = date.today().timetuple().tm_yday % len(topics)
    return [topics[idx], topics[(idx + 1) % len(topics)]]


def gather_research() -> dict[str, Any]:
    """Main entry point — returns all research as structured dict."""
    print("[research] Starting daily research...")

    web_results = []
    for q in SEARCH_QUERIES[:3]:  # limit to 3 queries to save API quota
        web_results.extend(_web_search(q))

    reddit = _reddit_search()
    hn = _hackernews_search()
    github = _github_releases()
    docs = _anthropic_docs_topics()

    all_results = web_results + reddit + hn + github + docs

    # Deduplicate by title
    seen = set()
    unique = []
    for r in all_results:
        key = r["title"].lower()[:60]
        if key not in seen:
            seen.add(key)
            unique.append(r)

    research = {
        "date": date.today().isoformat(),
        "total_sources": len(unique),
        "web": web_results[:6],
        "reddit": reddit[:4],
        "hackernews": hn[:3],
        "github": github[:3],
        "docs": docs,
        "all": unique[:15],
    }

    print(f"[research] Found {len(unique)} unique sources")
    return research


if __name__ == "__main__":
    result = gather_research()
    print(json.dumps(result, indent=2))
