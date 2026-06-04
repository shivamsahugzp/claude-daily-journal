"""
Card generator — creates visual assets using Pillow.
Generates: main title card, beginner tip card, before/after card, carousel slides.
"""

import os
import textwrap
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

# ── Paths ─────────────────────────────────────────────────────────────────────
ASSETS_DIR = Path(__file__).parent.parent.parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "journal"

# ── Brand Colors ──────────────────────────────────────────────────────────────
BG_DARK = (13, 17, 23)          # near-black
BG_CARD = (22, 27, 34)          # card background
ACCENT_TEAL = (100, 255, 218)   # #64FFDA — Claude teal
ACCENT_PURPLE = (167, 139, 250) # #A78BFA
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (139, 148, 158)
BORDER = (48, 54, 61)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load system font with fallback to default."""
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    bold_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    paths = bold_paths if bold else font_paths
    for path in paths:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_rounded_rect(draw: ImageDraw.Draw, xy: tuple, radius: int, fill: tuple) -> None:
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def create_main_card(day: int, title: str, date_str: str, output_dir: Path) -> Path:
    """1080x1080 main title card for Instagram/LinkedIn."""
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Subtle grid background
    for x in range(0, W, 60):
        draw.line([(x, 0), (x, H)], fill=(255, 255, 255, 8), width=1)
    for y in range(0, H, 60):
        draw.line([(0, y), (W, y)], fill=(255, 255, 255, 8), width=1)

    # Top accent bar
    draw.rectangle([(0, 0), (W, 6)], fill=ACCENT_TEAL)

    # Day badge
    badge_font = _load_font(28, bold=True)
    badge_text = f"DAY {day}"
    draw.rounded_rectangle([60, 80, 60 + 140, 130], radius=8, fill=ACCENT_TEAL)
    draw.text((130, 105), badge_text, font=badge_font, fill=BG_DARK, anchor="mm")

    # "Learning Claude in Public" tag
    tag_font = _load_font(22)
    draw.text((220, 105), "Learning Claude in Public", font=tag_font, fill=TEXT_GRAY, anchor="lm")

    # Main title
    title_font = _load_font(58, bold=True)
    clean_title = title.replace(f"Day {day} — ", "").replace(f"Day {day}: ", "")
    lines = _wrap_text(clean_title, title_font, W - 120)
    y = 200
    for line in lines[:3]:
        draw.text((60, y), line, font=title_font, fill=TEXT_WHITE)
        y += 75

    # Teal accent line under title
    draw.rectangle([(60, y + 20), (200, y + 26)], fill=ACCENT_TEAL)

    # Decorative card in middle
    card_y = y + 80
    _draw_rounded_rect(draw, (60, card_y, W - 60, card_y + 280), 16, BG_CARD)
    draw.rounded_rectangle([60, card_y, W - 60, card_y + 280], radius=16, outline=BORDER, width=1)

    card_label_font = _load_font(20)
    draw.text((90, card_y + 25), "TODAY'S FOCUS", font=card_label_font, fill=ACCENT_TEAL)

    focus_font = _load_font(32, bold=False)
    focus_lines = _wrap_text("Claude AI — free tool that saves hours of daily work", focus_font, W - 180)
    fy = card_y + 65
    for line in focus_lines[:3]:
        draw.text((90, fy), line, font=focus_font, fill=TEXT_WHITE)
        fy += 45

    # Bottom section
    bottom_y = H - 160
    draw.rectangle([(0, bottom_y), (W, bottom_y + 1)], fill=BORDER)

    name_font = _load_font(30, bold=True)
    draw.text((60, bottom_y + 30), "@shivamsahu", font=name_font, fill=ACCENT_TEAL)

    date_font = _load_font(24)
    draw.text((60, bottom_y + 72), date_str, font=date_font, fill=TEXT_GRAY)

    follow_font = _load_font(22)
    draw.text((W - 60, bottom_y + 50), "Follow for daily learnings →", font=follow_font, fill=TEXT_GRAY, anchor="rm")

    # Bottom accent bar
    draw.rectangle([(0, H - 6), (W, H)], fill=ACCENT_PURPLE)

    out_path = output_dir / "card_main.png"
    img.save(out_path, "PNG", optimize=True)
    print(f"[assets] Saved main card → {out_path}")
    return out_path


def create_tip_card(day: int, tip: str, output_dir: Path) -> Path:
    """1080x1080 beginner tip card."""
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (W, 6)], fill=ACCENT_PURPLE)

    # Bulb emoji substitute — coloured circle
    draw.ellipse([(420, 120), (660, 360)], fill=(255, 220, 50))
    icon_font = _load_font(100, bold=True)
    draw.text((540, 240), "💡", font=icon_font, fill=(0, 0, 0), anchor="mm")

    label_font = _load_font(26, bold=True)
    draw.text((W // 2, 400), f"BEGINNER TIP — DAY {day}", font=label_font, fill=ACCENT_TEAL, anchor="mm")

    # Tip text
    tip_font = _load_font(42, bold=True)
    lines = _wrap_text(tip, tip_font, W - 120)
    total_h = len(lines) * 60
    y = (H // 2) - (total_h // 2)
    for line in lines:
        draw.text((W // 2, y), line, font=tip_font, fill=TEXT_WHITE, anchor="mm")
        y += 60

    name_font = _load_font(26)
    draw.text((W // 2, H - 80), "@shivamsahu · #LearningInPublic", font=name_font, fill=TEXT_GRAY, anchor="mm")
    draw.rectangle([(0, H - 6), (W, H)], fill=ACCENT_TEAL)

    out_path = output_dir / "card_tip.png"
    img.save(out_path, "PNG", optimize=True)
    print(f"[assets] Saved tip card → {out_path}")
    return out_path


def create_carousel(day: int, title: str, tip: str, sample_prompt: str, output_dir: Path) -> list[Path]:
    """Generate 5 Instagram carousel slides."""
    paths = []
    slides = [
        {"label": "1/5", "heading": f"Day {day}", "body": title.replace(f"Day {day} — ", ""), "color": ACCENT_TEAL},
        {"label": "2/5", "heading": "What I Learned", "body": "Claude can do this task in seconds instead of hours. No coding needed.", "color": ACCENT_PURPLE},
        {"label": "3/5", "heading": "Try This Prompt", "body": sample_prompt[:200] if sample_prompt else "Ask Claude: 'Explain [topic] like I'm completely new to it, with a real example.'", "color": (255, 180, 50)},
        {"label": "4/5", "heading": "Beginner Tip", "body": tip, "color": ACCENT_TEAL},
        {"label": "5/5", "heading": "Follow Along", "body": "I post every day. Real learnings, no jargon, beginner-friendly.\n\n@shivamsahu", "color": ACCENT_PURPLE},
    ]

    for i, slide in enumerate(slides):
        W, H = 1080, 1080
        img = Image.new("RGB", (W, H), BG_DARK)
        draw = ImageDraw.Draw(img)

        # Colored top bar
        draw.rectangle([(0, 0), (W, 8)], fill=slide["color"])

        # Slide counter
        counter_font = _load_font(24)
        draw.text((W - 60, 40), slide["label"], font=counter_font, fill=TEXT_GRAY, anchor="rm")

        # Heading
        heading_font = _load_font(64, bold=True)
        draw.text((60, 120), slide["heading"], font=heading_font, fill=slide["color"])

        # Divider
        draw.rectangle([(60, 210), (200, 216)], fill=slide["color"])

        # Body
        body_font = _load_font(38)
        lines = _wrap_text(slide["body"], body_font, W - 120)
        y = 260
        for line in lines[:8]:
            draw.text((60, y), line, font=body_font, fill=TEXT_WHITE)
            y += 55

        # Bottom
        name_font = _load_font(24)
        draw.text((60, H - 60), "@shivamsahu · Learning Claude in Public", font=name_font, fill=TEXT_GRAY)
        draw.rectangle([(0, H - 6), (W, H)], fill=slide["color"])

        out_path = output_dir / f"carousel_{i+1}.png"
        img.save(out_path, "PNG", optimize=True)
        paths.append(out_path)

    print(f"[assets] Saved {len(paths)} carousel slides")
    return paths


def create_snippet_card(prompt_text: str, day: int, output_dir: Path) -> Path:
    """Dark-theme code/prompt snippet card."""
    W, H = 1080, 600
    img = Image.new("RGB", (W, H), (30, 30, 30))
    draw = ImageDraw.Draw(img)

    # Title bar
    draw.rectangle([(0, 0), (W, 50)], fill=(50, 50, 50))
    dot_colors = [(255, 95, 86), (255, 189, 46), (39, 201, 63)]
    for i, color in enumerate(dot_colors):
        cx = 20 + i * 25
        draw.ellipse([(cx - 7, 17), (cx + 7, 33)], fill=color)
    draw.text((W // 2, 25), f"Claude Prompt — Day {day}", font=_load_font(18), fill=(180, 180, 180), anchor="mm")

    # Prompt text
    code_font = _load_font(28)
    lines = _wrap_text(prompt_text, code_font, W - 80)
    y = 80
    for j, line in enumerate(lines[:8]):
        line_num_font = _load_font(20)
        draw.text((20, y + 5), str(j + 1), font=line_num_font, fill=(100, 100, 100))
        draw.text((60, y), line, font=code_font, fill=(204, 204, 204))
        y += 50

    out_path = output_dir / "card_snippet.png"
    img.save(out_path, "PNG", optimize=True)
    print(f"[assets] Saved snippet card → {out_path}")
    return out_path


def generate_all_assets(content: dict, output_dir: Path) -> dict:
    """Generate all visual assets for a given day's content."""
    output_dir.mkdir(parents=True, exist_ok=True)

    from datetime import date
    date_str = date.fromisoformat(content["date"]).strftime("%B %d, %Y")

    paths = {
        "main_card": str(create_main_card(content["day"], content["title"], date_str, output_dir)),
        "tip_card": str(create_tip_card(content["day"], content["tip"], output_dir)),
        "carousel": [str(p) for p in create_carousel(
            content["day"], content["title"], content["tip"], content.get("sample_prompt", ""), output_dir
        )],
        "snippet_card": str(create_snippet_card(
            content.get("sample_prompt", "Ask Claude anything and see what happens."), content["day"], output_dir
        )),
    }
    return paths
