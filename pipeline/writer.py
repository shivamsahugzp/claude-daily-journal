"""
Writer pipeline — generates the full daily journal entry using AI.
Primary: Google Gemini API (free tier — gemini-1.5-flash)
Fallback: Anthropic Claude API (if ANTHROPIC_API_KEY is set)
"""

import os
import json
import re
from datetime import date
from typing import Any
import httpx


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"
CLAUDE_MODEL = "claude-sonnet-4-6"

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

SYSTEM_PROMPT = """You are writing a daily learning journal for Shivam Sahu — a non-technical person
from India who is publicly documenting his journey learning Claude AI from scratch.

Your voice: warm, honest, conversational, relatable. Write like you're texting a friend who
knows nothing about AI. Use simple English. Avoid jargon — if you must use a technical term,
explain it in plain words immediately after.

The journal's mission: Show non-technical people that Claude is for everyone, not just developers.
Every entry should leave a beginner thinking "I can try this today."

Tone rules:
- No buzzwords (no "leverage", "synergy", "paradigm")
- No AI-sounding phrases ("I apologize", "Certainly!", "As an AI")
- Real, honest reactions — including confusion, frustration, and genuine excitement
- Keep sentences short. Indian English is fine and authentic.
- Never mention company names, internal projects, or confidential work details
- Always include a practical example a beginner can copy-paste and try right now"""


def _call_gemini(prompt: str, system: str = "") -> str:
    """Call Gemini 1.5 Flash API (free tier)."""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    url = f"{GEMINI_BASE}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"maxOutputTokens": 2000, "temperature": 0.8},
    }
    resp = httpx.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    candidates = resp.json().get("candidates", [])
    if not candidates:
        raise ValueError("Gemini returned no candidates")
    return candidates[0]["content"]["parts"][0]["text"]


def _call_claude(prompt: str, system: str = "") -> str:
    """Call Anthropic Claude API as fallback."""
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def _generate(prompt: str, system: str = "", max_tokens: int = 2000) -> str:
    """Call Gemini first, fall back to Claude if unavailable."""
    if GEMINI_API_KEY:
        try:
            return _call_gemini(prompt, system)
        except Exception as e:
            print(f"[writer] Gemini failed ({e}), trying Claude...")
    if ANTHROPIC_API_KEY:
        return _call_claude(prompt, system)
    raise RuntimeError("No AI API key available. Set GEMINI_API_KEY or ANTHROPIC_API_KEY.")


def _get_day_number() -> int:
    start = date(2026, 3, 22)
    delta = date.today() - start
    return max(1, delta.days + 1)


def generate_content(research: dict[str, Any]) -> dict[str, Any]:
    """Generate all content variants using AI."""
    day_num = _get_day_number()
    today = date.today().strftime("%B %d, %Y")
    research_summary = json.dumps(research.get("all", [])[:10], indent=2)

    # ── Full article ──────────────────────────────────────────────────────────
    article_prompt = f"""Based on this research about Claude AI from today ({today}), write Day {day_num} of my learning journal.

RESEARCH DATA:
{research_summary}

Write a complete article in this EXACT markdown structure:

---
title: "Day {day_num} — [catchy title based on today's most interesting topic]"
date: {date.today().isoformat()}
day: {day_num}
topics: [pick 2-3 from: claude-code, mcp, agents, prompting, api, tools, productivity, beginners]
---

# Day {day_num} — [same catchy title]

## What I Explored Today
[2-3 sentences. What was the main Claude topic/feature today? Keep it casual and relatable.]

## What I Learned
[5-7 bullet points. Real things a beginner would find useful. Be specific, not vague.]

## How It Helped Me (Real Task, No Details)
[3-4 sentences. Describe a real-world scenario where this helped — without any confidential info.]

## Try This Right Now (Beginner Prompt)
[Give ONE ready-to-use prompt they can copy-paste into Claude.ai and try in the next 5 minutes.
Format as a code block.]

## What Confused Me
[1-2 sentences of honest confusion or something still unclear. This builds trust.]

## Beginner Tip of the Day
[One bold, actionable tip. Keep it under 2 sentences.]

## Resources
[2-3 links from the research data, formatted as markdown links]

## My Honest Take
[3-4 sentences of personal reflection. End with one question for the reader.]

---
*Day {day_num} of learning Claude in public. Follow along if you're also figuring this out.*"""

    article = _generate(article_prompt, SYSTEM_PROMPT)

    # Extract title
    title_match = re.search(r'title: "(.+?)"', article)
    title = title_match.group(1) if title_match else f"Day {day_num} — Learning Claude"

    # Extract tip
    tip_match = re.search(r'## Beginner Tip of the Day\n(.+?)(?=\n##|\Z)', article, re.DOTALL)
    tip = tip_match.group(1).strip() if tip_match else "Ask Claude to explain anything like you're 5 years old."

    # Extract sample prompt
    prompt_match = re.search(r'## Try This Right Now.*?\n```\n(.+?)```', article, re.DOTALL)
    sample_prompt = prompt_match.group(1).strip() if prompt_match else ""

    # ── Instagram caption ─────────────────────────────────────────────────────
    ig_prompt = f"""Write an Instagram caption for Day {day_num} of learning Claude.
Based on: {title}
Key tip: {tip}

Rules:
- Start with a hook (no "I" as first word)
- 150-200 words max
- 3-4 short paragraphs
- End with a question to drive comments
- 8-10 relevant hashtags at the bottom
- Include: #ClaudeAI #LearningInPublic #AIForEveryone #ShivamLearnsAI"""

    instagram_caption = _generate(ig_prompt, SYSTEM_PROMPT)

    # ── LinkedIn post ─────────────────────────────────────────────────────────
    li_prompt = f"""Write a LinkedIn post for Day {day_num} of my public Claude learning journey.
Based on: {title}
Key insight: {tip}

Rules:
- Professional but personal tone
- Start with a strong first line people see before "see more"
- 200-250 words
- Tell a mini-story about how this Claude feature helped at work (generic, no confidential details)
- End with a CTA to follow the series
- 3-5 hashtags max"""

    linkedin_post = _generate(li_prompt, SYSTEM_PROMPT)

    # ── Threads post ──────────────────────────────────────────────────────────
    threads_post = f"Day {day_num}: {title.split('—')[-1].strip()}\n\n{tip}\n\nFull breakdown → link in bio\n#ClaudeAI #LearningInPublic"

    return {
        "day": day_num,
        "date": date.today().isoformat(),
        "title": title,
        "tip": tip,
        "sample_prompt": sample_prompt,
        "article": article,
        "twitter_thread": "",   # Twitter disabled
        "instagram_caption": instagram_caption,
        "linkedin_post": linkedin_post,
        "threads_post": threads_post,
    }
