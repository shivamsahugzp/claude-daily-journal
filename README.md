# Daily AI Learning Journal

A zero-touch pipeline that publishes a daily entry of me learning Claude AI in public, posted to **six platforms** every morning at 10:30 AM IST — without me touching the laptop.

The goal: prove that a non-technical operator can use Claude to build, ship, and run real software end-to-end. The journal itself *is* the proof.

## What runs every day

```
06:00 IST  cron in GitHub Actions
             ↓
  ┌──────────────────────────────────────────────────────────────────┐
  │  pipeline/research.py    gather day's Claude news from Reddit /  │
  │                          HackerNews / web / GitHub trending      │
  │                                  ↓                                │
  │  pipeline/writer.py      Gemini Flash (primary) / Claude (fallback)│
  │                          → article, twitter thread, IG caption,  │
  │                          LinkedIn post, Threads post              │
  │                                  ↓                                │
  │  pipeline/assets/*       Pillow renders 5-card carousel + cover   │
  │  pipeline/assets/video   FFmpeg + edge-tts → 60s vertical video   │
  │                                  ↓                                │
  │  git commit + push       to main; site rebuilds on GitHub Pages  │
  │                                  ↓                                │
  │  pipeline/publishers/    parallel posts: dev.to, Hashnode,        │
  │                          Twitter, Threads, Instagram, LinkedIn   │
  └──────────────────────────────────────────────────────────────────┘
             ↓
  publish_report.json with all 6 URLs committed back to repo
```

Runs entirely on the GitHub Actions free tier (2000 min / month). One daily run uses ~3 min.

## Stack

| Layer | Tool | Why |
|---|---|---|
| Orchestrator | GitHub Actions cron | Free, reliable, no server to babysit |
| Content gen | Gemini 1.5 Flash (primary), Claude Sonnet 4.6 (fallback) | Gemini is free-tier; Claude better at voice consistency |
| Research | Serper (web), Reddit JSON, HN API, GitHub trending | All free / generous free tiers |
| Image assets | Pillow + DejaVu fonts | No paid design tool; deterministic output |
| Video | FFmpeg + edge-tts | Free Microsoft voice; vertical 1080×1920 for IG/Reels |
| Publishing | dev.to API, Hashnode GraphQL, Twitter v2, Threads API, instagrapi, LinkedIn REST | Each platform's free tier is enough for one post/day |
| Static site | GitHub Pages | Auto-deploys from `docs/` |

## Repo layout

```
pipeline/
  research.py              gather sources
  writer.py                LLM call + voice/style guardrails
  assets/card_generator.py 5-card carousel + cover image
  assets/video_generator.py 60s vertical narrated video
  publishers/              one module per platform
  main.py                  orchestrator
.github/workflows/daily.yml cron + xvfb headless display
docs/index.html            auto-regenerated catalog page
templates/ig_profile.png   profile circle for cards
requirements.txt
.env.example
```

## Voice + safety guardrails

The writer's system prompt enforces:
- No buzzwords ("leverage", "synergy", "paradigm" are blocked)
- No AI-sounding phrases ("Certainly!", "As an AI", "I apologize")
- Short sentences; Indian English is fine
- **Never mention employer names, internal projects, or confidential work** — explicit in the prompt
- Always include one copy-paste example a beginner can try the same day

## Running locally

```bash
# Clone the repo, then:
cd claude-daily-journal
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # fill the API keys for whichever platforms you want
python -m pipeline.main
```

Only `ANTHROPIC_API_KEY` (or `GEMINI_API_KEY`) is required. Every publisher is independent — skip the ones whose env vars are missing.

## Why this exists

I'm a Customer Success operator, not a developer. Most people who built things like this had backgrounds in engineering. I wanted the journal to be a daily public proof that you don't.

Co-built with [Claude](https://claude.com) as pair-programmer over many iterations.

MIT licensed.
