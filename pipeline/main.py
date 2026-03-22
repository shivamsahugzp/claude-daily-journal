"""
Main orchestrator — runs the full daily pipeline.
Called by GitHub Actions at 10:30 AM IST (05:00 UTC) every day.

Flow:
  1. Research  → gather Claude news from web, Reddit, HN, GitHub, Anthropic docs
  2. Write     → Claude API generates article + all platform variants
  3. Assets    → Pillow generates cards, carousel, snippet image
  4. Video     → FFmpeg + edge-tts assembles 60s vertical video
  5. Commit    → save all files to journal/{date}/
  6. Publish   → push to dev.to, Hashnode, Instagram, Twitter, Threads, LinkedIn
  7. Report    → write publish_report.json with all URLs
"""

import os
import json
import sys
import subprocess
from datetime import date
from pathlib import Path

# ── Import pipeline modules ───────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.research import gather_research
from pipeline.writer import generate_content
from pipeline.assets.card_generator import generate_all_assets
from pipeline.assets.video_generator import generate_video
from pipeline import publishers


def _save_article(content: dict, output_dir: Path) -> Path:
    """Write markdown article to disk."""
    article_path = output_dir / "article.md"
    article_path.write_text(content["article"], encoding="utf-8")
    print(f"[main] Article saved → {article_path}")
    return article_path


def _save_social_content(content: dict, output_dir: Path) -> None:
    """Write all social platform content to disk for reference."""
    social = {
        "twitter_thread": content["twitter_thread"],
        "instagram_caption": content["instagram_caption"],
        "linkedin_post": content["linkedin_post"],
        "threads_post": content["threads_post"],
    }
    (output_dir / "social_content.json").write_text(json.dumps(social, indent=2), encoding="utf-8")


def _git_commit_and_push(date_str: str) -> bool:
    """Commit today's journal entry and push to GitHub."""
    try:
        subprocess.run(["git", "config", "user.name", "Shivam Sahu"], check=True)
        subprocess.run(["git", "config", "user.email", "shivamsahugzp@gmail.com"], check=True)
        subprocess.run(["git", "add", f"journal/{date_str}/", "docs/"], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"feat: Day journal entry — {date_str}"],
            check=True,
        )
        subprocess.run(["git", "push"], check=True)
        print("[main] Committed and pushed to GitHub")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[main] Git push failed: {e}")
        return False


def _update_github_pages(content: dict, all_entries: list[dict]) -> None:
    """Regenerate docs/index.html for GitHub Pages."""
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    entries_html = ""
    for entry in sorted(all_entries, key=lambda x: x.get("date", ""), reverse=True)[:30]:
        entries_html += f"""
        <article class="entry">
          <span class="day-badge">Day {entry.get('day', '?')}</span>
          <h2><a href="{entry.get('devto_url', '#')}" target="_blank">{entry.get('title', '')}</a></h2>
          <p class="date">{entry.get('date', '')}</p>
          <p class="tip">{entry.get('tip', '')}</p>
          <div class="links">
            {'<a href="' + entry.get('devto_url','') + '" target="_blank">dev.to</a>' if entry.get('devto_url') else ''}
            {'<a href="' + entry.get('hashnode_url','') + '" target="_blank">Hashnode</a>' if entry.get('hashnode_url') else ''}
          </div>
        </article>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Shivam Learns Claude — Daily Learning Journal</title>
  <meta name="description" content="A non-technical person learning Claude AI in public, every single day.">
  <style>
    :root {{
      --bg: #0d1117; --card: #161b22; --border: #30363d;
      --teal: #64ffda; --purple: #a78bfa; --white: #fff; --gray: #8b949e;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--white); font-family: -apple-system, sans-serif; }}
    .hero {{ padding: 80px 24px 60px; text-align: center; border-bottom: 1px solid var(--border); }}
    .hero h1 {{ font-size: clamp(2rem, 5vw, 4rem); font-weight: 900; }}
    .hero h1 span {{ color: var(--teal); }}
    .hero p {{ color: var(--gray); margin-top: 16px; font-size: 1.1rem; max-width: 600px; margin-inline: auto; }}
    .stats {{ display: flex; gap: 40px; justify-content: center; margin-top: 40px; flex-wrap: wrap; }}
    .stat {{ text-align: center; }}
    .stat .num {{ font-size: 2rem; font-weight: 900; color: var(--teal); }}
    .stat .label {{ color: var(--gray); font-size: 0.85rem; margin-top: 4px; }}
    .feed {{ max-width: 800px; margin: 60px auto; padding: 0 24px; }}
    .feed h2 {{ font-size: 1.5rem; color: var(--gray); margin-bottom: 32px; }}
    .entry {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 28px; margin-bottom: 20px; }}
    .day-badge {{ background: var(--teal); color: #000; font-weight: 700; font-size: 0.75rem; padding: 4px 10px; border-radius: 6px; }}
    .entry h2 {{ margin-top: 14px; font-size: 1.25rem; }}
    .entry h2 a {{ color: var(--white); text-decoration: none; }}
    .entry h2 a:hover {{ color: var(--teal); }}
    .entry .date {{ color: var(--gray); font-size: 0.85rem; margin-top: 8px; }}
    .entry .tip {{ color: #ccc; margin-top: 12px; font-size: 0.95rem; line-height: 1.6; }}
    .links {{ margin-top: 16px; display: flex; gap: 12px; flex-wrap: wrap; }}
    .links a {{ color: var(--teal); font-size: 0.85rem; text-decoration: none; border: 1px solid var(--teal); padding: 4px 12px; border-radius: 6px; }}
    .links a:hover {{ background: var(--teal); color: #000; }}
    footer {{ text-align: center; padding: 40px; color: var(--gray); font-size: 0.85rem; border-top: 1px solid var(--border); }}
  </style>
</head>
<body>
  <header class="hero">
    <h1>Shivam Learns <span>Claude</span></h1>
    <p>A non-technical person learning Claude AI in public — every single day.<br>
       No jargon. No coding degree needed. Real results from real tasks.</p>
    <div class="stats">
      <div class="stat"><div class="num">{len(all_entries)}</div><div class="label">Days Published</div></div>
      <div class="stat"><div class="num">6</div><div class="label">Platforms</div></div>
      <div class="stat"><div class="num">∞</div><div class="label">Days to Go</div></div>
    </div>
  </header>
  <main class="feed">
    <h2>Latest Entries</h2>
    {entries_html if entries_html else '<p style="color:var(--gray)">First entry coming soon...</p>'}
  </main>
  <footer>
    <p>By <strong>Shivam Sahu</strong> · Updated daily · <a href="https://github.com/shivamsahugzp/claude-daily-journal" style="color:var(--teal)">GitHub</a></p>
  </footer>
</body>
</html>"""

    (docs_dir / "index.html").write_text(html, encoding="utf-8")
    print("[main] GitHub Pages updated → docs/index.html")


def _load_all_entries() -> list[dict]:
    """Load all previous publish reports to build the full entry list."""
    journal_root = Path(__file__).parent.parent / "journal"
    entries = []
    for report_path in journal_root.glob("*/publish_report.json"):
        try:
            entries.append(json.loads(report_path.read_text()))
        except Exception:
            pass
    return entries


def run() -> None:
    today = date.today().isoformat()
    output_dir = Path(__file__).parent.parent / "journal" / today
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Claude Daily Journal — {today}")
    print(f"{'='*60}\n")

    # ── 1. Research ───────────────────────────────────────────────
    print("📡 Phase 1: Research")
    research = gather_research()
    (output_dir / "research.json").write_text(json.dumps(research, indent=2))

    # ── 2. Write ──────────────────────────────────────────────────
    print("\n✍️  Phase 2: Writing content")
    content = generate_content(research)
    _save_article(content, output_dir)
    _save_social_content(content, output_dir)

    # ── 3. Assets ─────────────────────────────────────────────────
    print("\n🎨 Phase 3: Generating visual assets")
    asset_paths = generate_all_assets(content, output_dir)

    # ── 4. Video ──────────────────────────────────────────────────
    print("\n🎬 Phase 4: Generating video")
    video_path = generate_video(content, output_dir)
    if video_path:
        asset_paths["video"] = str(video_path)

    # ── 5. Commit all files first (images need to be on GitHub for IG API) ───
    print("\n💾 Phase 5: Committing to GitHub")
    _update_github_pages(content, _load_all_entries())
    _git_commit_and_push(today)

    # ── 6. Publish ────────────────────────────────────────────────
    print("\n📢 Phase 6: Publishing to all platforms")
    report = {
        "day": content["day"],
        "date": today,
        "title": content["title"],
        "tip": content["tip"],
    }

    # dev.to
    from pipeline.publishers import devto
    r = devto.publish(content)
    report["devto_url"] = r.get("url", "")
    report["devto_success"] = r["success"]

    # Hashnode
    from pipeline.publishers import hashnode
    r = hashnode.publish(content)
    report["hashnode_url"] = r.get("url", "")
    report["hashnode_success"] = r["success"]

    # Twitter/X — disabled
    report["twitter_success"] = False

    # Threads
    from pipeline.publishers import threads
    r = threads.publish(content)
    report["threads_url"] = r.get("url", "")
    report["threads_success"] = r["success"]

    # Instagram (depends on images being pushed to GitHub first)
    from pipeline.publishers import instagram
    r = instagram.publish(content, asset_paths)
    report["instagram_url"] = r.get("url", "")
    report["instagram_success"] = r["success"]

    # LinkedIn
    from pipeline.publishers import linkedin
    r = linkedin.publish(content, report.get("devto_url", ""), report.get("hashnode_url", ""))
    report["linkedin_success"] = r["success"]

    # ── 7. Save report ────────────────────────────────────────────
    report_path = output_dir / "publish_report.json"
    report_path.write_text(json.dumps(report, indent=2))

    # Final commit with report + updated index
    _update_github_pages(content, _load_all_entries())
    _git_commit_and_push(today)

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  ✅ Day {content['day']} Complete — {today}")
    print(f"{'='*60}")
    platforms = ["devto", "hashnode", "threads", "instagram", "linkedin"]
    for p in platforms:
        status = "✅" if report.get(f"{p}_success") else "❌"
        url = report.get(f"{p}_url", "")
        print(f"  {status} {p.title():12} {url}")
    print()


if __name__ == "__main__":
    run()
