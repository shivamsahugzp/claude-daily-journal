"""
Video generator — creates 60-second Reels/Shorts/TikTok videos.
Uses edge-tts for voice-over + FFmpeg for video assembly.
No Remotion dependency needed (runs on GitHub Actions without Node.js overhead).
"""

import os
import json
import asyncio
import subprocess
import textwrap
from pathlib import Path
from typing import Optional

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


VOICE = "en-IN-NeerjaNeural"   # Indian English female voice
VOICE_FALLBACK = "en-US-AriaNeural"

BG_DARK = (13, 17, 23)
ACCENT_TEAL = (100, 255, 218)
ACCENT_PURPLE = (167, 139, 250)
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (139, 148, 158)


def _load_font(size: int, bold: bool = False) -> "ImageFont.FreeTypeFont":
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in font_paths:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines, current = [], ""
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


def _make_slide_image(slide: dict, output_path: Path, W: int = 1080, H: int = 1920) -> None:
    """Create a single 9:16 vertical slide image."""
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    color = slide.get("color", ACCENT_TEAL)

    # Background accent gradient simulation (top strip)
    for i in range(300):
        alpha = int(30 * (1 - i / 300))
        r = int(color[0] * alpha / 255 + BG_DARK[0] * (1 - alpha / 255))
        g = int(color[1] * alpha / 255 + BG_DARK[1] * (1 - alpha / 255))
        b = int(color[2] * alpha / 255 + BG_DARK[2] * (1 - alpha / 255))
        draw.line([(0, i), (W, i)], fill=(r, g, b))

    draw.rectangle([(0, 0), (W, 8)], fill=color)

    # Day badge
    if slide.get("show_day"):
        badge_font = _load_font(36, bold=True)
        badge_text = slide["show_day"]
        draw.rounded_rectangle([80, 120, 80 + 200, 180], radius=10, fill=color)
        draw.text((180, 150), badge_text, font=badge_font, fill=BG_DARK, anchor="mm")

    # Label
    if slide.get("label"):
        label_font = _load_font(30)
        draw.text((W // 2, 260), slide["label"], font=label_font, fill=TEXT_GRAY, anchor="mm")

    # Main heading
    heading_font = _load_font(72, bold=True)
    heading_lines = _wrap_text(slide.get("heading", ""), heading_font, W - 120)
    y = 340
    for line in heading_lines[:2]:
        draw.text((W // 2, y), line, font=heading_font, fill=color, anchor="mm")
        y += 95

    # Divider
    draw.rectangle([(W // 2 - 80, y + 20), (W // 2 + 80, y + 26)], fill=color)

    # Body
    body_font = _load_font(46)
    body_lines = _wrap_text(slide.get("body", ""), body_font, W - 160)
    y = y + 80
    for line in body_lines[:6]:
        draw.text((W // 2, y), line, font=body_font, fill=TEXT_WHITE, anchor="mm")
        y += 65

    # Bottom
    bottom_font = _load_font(30)
    draw.text((W // 2, H - 100), "@shivamsahu", font=bottom_font, fill=color, anchor="mm")
    draw.text((W // 2, H - 55), "#LearningClaude #AIForEveryone", font=_load_font(24), fill=TEXT_GRAY, anchor="mm")
    draw.rectangle([(0, H - 6), (W, H)], fill=color)

    img.save(output_path, "PNG")


async def _generate_voiceover(script: str, output_path: Path) -> bool:
    """Generate voice-over MP3 using edge-tts."""
    if not EDGE_TTS_AVAILABLE:
        return False
    try:
        communicate = edge_tts.Communicate(script, VOICE)
        await communicate.save(str(output_path))
        return True
    except Exception:
        try:
            communicate = edge_tts.Communicate(script, VOICE_FALLBACK)
            await communicate.save(str(output_path))
            return True
        except Exception as e:
            print(f"[video] voice-over failed: {e}")
            return False


def _check_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


def _images_to_video(slide_paths: list[Path], audio_path: Optional[Path], output_path: Path) -> bool:
    """Assemble slide images + audio into MP4 using FFmpeg."""
    if not _check_ffmpeg():
        print("[video] FFmpeg not found, skipping video generation")
        return False

    # Each slide shown for ~10 seconds (6 slides = 60s)
    duration_per_slide = 10
    concat_file = output_path.parent / "concat.txt"

    with open(concat_file, "w") as f:
        for p in slide_paths:
            f.write(f"file '{p.absolute()}'\n")
            f.write(f"duration {duration_per_slide}\n")
        # Repeat last slide to avoid FFmpeg concat issue
        f.write(f"file '{slide_paths[-1].absolute()}'\n")

    try:
        if audio_path and audio_path.exists():
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-i", str(audio_path),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-shortest",
                "-vf", "scale=1080:1920,fps=30",
                "-pix_fmt", "yuv420p",
                str(output_path),
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-vf", "scale=1080:1920,fps=30",
                "-pix_fmt", "yuv420p",
                str(output_path),
            ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        concat_file.unlink(missing_ok=True)

        if result.returncode == 0:
            print(f"[video] Video saved → {output_path}")
            return True
        else:
            print(f"[video] FFmpeg error: {result.stderr[-500:]}")
            return False
    except Exception as e:
        print(f"[video] Assembly failed: {e}")
        return False


def generate_video(content: dict, output_dir: Path) -> Optional[Path]:
    """Main entry — generates 60s vertical video from content dict."""
    if not PILLOW_AVAILABLE:
        print("[video] Pillow not available, skipping")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    day = content["day"]
    title_clean = content["title"].replace(f"Day {day} — ", "")

    slides_data = [
        {
            "show_day": f"DAY {day}",
            "label": "Learning Claude in Public",
            "heading": "Today I learned",
            "body": title_clean[:80],
            "color": ACCENT_TEAL,
        },
        {
            "label": "What is Claude?",
            "heading": "Claude is an AI assistant",
            "body": "It helps you write, research, code, and think — no technical skills needed.",
            "color": ACCENT_PURPLE,
        },
        {
            "label": "Today's Learning",
            "heading": "Key insight",
            "body": content.get("tip", "You can ask Claude anything in plain language.")[:120],
            "color": ACCENT_TEAL,
        },
        {
            "label": "Try this right now",
            "heading": "Copy this prompt",
            "body": (content.get("sample_prompt", "Ask Claude: Explain this to me like I'm 5."))[:150],
            "color": (255, 180, 50),
        },
        {
            "label": "Real talk",
            "heading": "Honest take",
            "body": "I'm not a developer. If I can use this, you can too.",
            "color": ACCENT_PURPLE,
        },
        {
            "label": "Follow for more",
            "heading": "Day " + str(day) + " done ✓",
            "body": "Daily Claude learnings. No jargon. No tech degree needed.\n\nFollow @shivamsahu",
            "color": ACCENT_TEAL,
        },
    ]

    # Generate slide images
    slide_paths = []
    for i, slide in enumerate(slides_data):
        p = output_dir / f"video_slide_{i+1}.png"
        _make_slide_image(slide, p)
        slide_paths.append(p)

    # Voice-over script
    voiceover_script = f"""
    Day {day} of learning Claude AI in public.
    Today I explored {title_clean}.
    Here's what I found out — {content.get('tip', 'Claude can save hours of daily work.')}.
    Try this prompt right now: {content.get('sample_prompt', 'Ask Claude to explain something confusing in simple words.')[:100]}.
    I post every single day. Follow along if you're also learning.
    """.strip()

    audio_path = output_dir / "voiceover.mp3"
    has_audio = asyncio.run(_generate_voiceover(voiceover_script, audio_path))

    # Assemble video
    video_path = output_dir / "reel.mp4"
    success = _images_to_video(slide_paths, audio_path if has_audio else None, video_path)

    # Cleanup slide images and audio
    for p in slide_paths:
        p.unlink(missing_ok=True)
    if has_audio:
        audio_path.unlink(missing_ok=True)

    return video_path if success else None
