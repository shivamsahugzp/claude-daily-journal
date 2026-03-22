"""
Writer pipeline — uses Claude API to generate the full daily journal entry
from research data. Outputs structured content for all platforms.
"""

import os
import json
import re
from datetime import date
from typing import Any
import anthropic


CLAUDE_MODEL = "claude-sonnet-4-6"

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


def _get_day_number() -> int:
    """Calculate day number from project start date (2026-03-22)."""
    start = date(2026, 3, 22)
    delta = date.today() - start
    return max(1, delta.days + 1)


def generate_content(research: dict[str, Any]) -> dict[str, Any]:
    """Generate all content variants using Claude API."""

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
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
[3-4 sentences. Describe a real-world scenario where this helped — without any confidential info.
Example: "I had to summarise a long document at work. Before Claude, I'd spend 30 minutes reading it.
Today I just pasted it in and got a summary in 10 seconds."]

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
[3-4 sentences of personal reflection. Surprise, frustration, or genuine excitement.
End with one question for the reader to think about.]

---
*Day {day_num} of learning Claude in public. Follow along if you're also figuring this out.*"""

    article_resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": article_prompt}],
    )
    article = article_resp.content[0].text

    # Extract title from article
    title_match = re.search(r'title: "(.+?)"', article)
    title = title_match.group(1) if title_match else f"Day {day_num} — Learning Claude"

    # Extract key tip for visual cards
    tip_match = re.search(r'## Beginner Tip of the Day\n(.+?)(?=\n##|\Z)', article, re.DOTALL)
    tip = tip_match.group(1).strip() if tip_match else "Ask Claude to explain anything like you're 5 years old."

    # Extract "try this" prompt
    prompt_match = re.search(r'## Try This Right Now.*?\n```\n(.+?)```', article, re.DOTALL)
    sample_prompt = prompt_match.group(1).strip() if prompt_match else ""

    # ── Twitter thread ────────────────────────────────────────────────────────
    thread_prompt = f"""Convert this journal entry into a Twitter/X thread for Day {day_num}.

Article:
{article[:1500]}

Write exactly 6 tweets. Rules:
- Tweet 1: Hook. Make them stop scrolling. Max 240 chars.
- Tweet 2-4: 3 key learnings from today, one per tweet
- Tweet 5: The beginner tip — copy-paste ready
- Tweet 6: CTA — "Follow for daily Claude learnings. Day {day_num}/{'{'}∞{'}'} 🧵"

Format each tweet on its own line, numbered 1/ through 6/
No hashtag spam — max 2 hashtags total across all tweets."""

    thread_resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": thread_prompt}],
    )
    twitter_thread = thread_resp.content[0].text

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

    ig_resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": ig_prompt}],
    )
    instagram_caption = ig_resp.content[0].text

    # ── LinkedIn post ─────────────────────────────────────────────────────────
    li_prompt = f"""Write a LinkedIn post for Day {day_num} of my public Claude learning journey.

Based on: {title}
Key insight: {tip}

Rules:
- Professional but personal tone
- Start with a strong first line (people only see this before "see more")
- 200-250 words
- Tell a mini-story about how this Claude feature helped at work (generic, no confidential details)
- End with a CTA to follow the series
- 3-5 hashtags max"""

    li_resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": li_prompt}],
    )
    linkedin_post = li_resp.content[0].text

    # ── Threads post ──────────────────────────────────────────────────────────
    threads_post = f"Day {day_num}: {title.split('—')[-1].strip()}\n\n{tip}\n\nFull breakdown → link in bio\n#ClaudeAI #LearningInPublic"

    return {
        "day": day_num,
        "date": date.today().isoformat(),
        "title": title,
        "tip": tip,
        "sample_prompt": sample_prompt,
        "article": article,
        "twitter_thread": twitter_thread,
        "instagram_caption": instagram_caption,
        "linkedin_post": linkedin_post,
        "threads_post": threads_post,
    }


if __name__ == "__main__":
    # Test with mock research
    mock_research = {
        "all": [
            {"title": "Claude Code now supports MCP servers", "snippet": "You can connect Slack, Notion, and databases directly inside Claude Code.", "url": "https://docs.anthropic.com", "source": "web"},
        ]
    }
    result = generate_content(mock_research)
    print(result["article"][:500])
