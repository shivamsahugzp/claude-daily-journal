"""Publisher — Twitter/X API v2."""
import os
import re
import httpx
from requests_oauthlib import OAuth1


TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.environ.get("TWITTER_ACCESS_SECRET", "")

BASE_URL = "https://api.twitter.com/2/tweets"


def _parse_thread(thread_text: str) -> list[str]:
    """Parse numbered tweets from thread text."""
    tweets = []
    pattern = re.compile(r'^\d+/', re.MULTILINE)
    parts = pattern.split(thread_text)
    for part in parts:
        cleaned = part.strip()
        if cleaned and len(cleaned) > 10:
            tweets.append(cleaned[:280])
    return tweets[:7] if tweets else [thread_text[:280]]


def _post_tweet(text: str, reply_to_id: str = None) -> dict:
    auth = OAuth1(TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    payload = {"text": text}
    if reply_to_id:
        payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}

    resp = httpx.post(BASE_URL, auth=auth, json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def publish(content: dict) -> dict:
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        return {"success": False, "error": "Twitter credentials not set"}

    tweets = _parse_thread(content["twitter_thread"])

    try:
        tweet_ids = []
        prev_id = None

        for tweet in tweets:
            result = _post_tweet(tweet, reply_to_id=prev_id)
            tweet_id = result.get("data", {}).get("id")
            tweet_ids.append(tweet_id)
            prev_id = tweet_id

        first_id = tweet_ids[0] if tweet_ids else None
        url = f"https://twitter.com/shivamsahugzp/status/{first_id}" if first_id else ""
        print(f"[twitter] Posted thread ({len(tweet_ids)} tweets) → {url}")
        return {"success": True, "url": url, "tweet_ids": tweet_ids}
    except Exception as e:
        print(f"[twitter] Failed: {e}")
        return {"success": False, "error": str(e)}
