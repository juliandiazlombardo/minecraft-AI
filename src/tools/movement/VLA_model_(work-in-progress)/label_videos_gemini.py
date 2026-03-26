"""
Minecraft Video Labeling — Gemini 2.5 Flash
============================================
Generates agent-style instructions from gameplay videos.
Each 1-minute chunk gets 3 varied instruction descriptions.

Usage:
    # Single video
    python label_videos_gemini.py --video path/to/video.mp4

    # Batch (all .mp4 in a dir)
    python label_videos_gemini.py --video-dir data/10xx/videos --limit 5
"""

import json
import os
import sys
import time
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

import config

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
load_dotenv(config.PROJECT_ROOT / ".env")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.5-flash-preview-05-20"
CHUNK_SECONDS = 60  # label in 1-minute segments

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------
PROMPT = f"""You are watching a Minecraft gameplay video. Your job is to generate
agent instructions — written as commands you would give to a Minecraft bot to
reproduce what the player does in the video.

Divide the video into {CHUNK_SECONDS}-second chunks. For EACH chunk, write 3
instruction variants with different wording but the same meaning.

Rules:
- Write in second-person imperative ("walk to the tree", "mine the stone").
- Be specific about directions, targets, and context visible in the video.
- Each instruction should be 1-2 sentences max.
- If nothing meaningful happens in a chunk (e.g. player is idle), say "wait" or "stay still".

Return ONLY valid JSON (no markdown fences) in this exact format:
[
  {{
    "chunk_start_sec": 0,
    "chunk_end_sec": {CHUNK_SECONDS},
    "instructions": [
      "Walk forward to the oak tree ahead of you and chop it down.",
      "Move toward the nearby oak tree and start breaking it.",
      "Head to the tree in front of you and cut it."
    ]
  }}
]
"""


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def upload_video(path: str) -> genai.types.File:
    """Upload video and wait until processed."""
    print(f"  Uploading {Path(path).name}...")
    f = genai.upload_file(path=path)
    while f.state.name == "PROCESSING":
        time.sleep(3)
        f = genai.get_file(f.name)
    if f.state.name == "FAILED":
        raise RuntimeError(f"Processing failed: {f.name}")
    print(f"  Ready: {f.uri}")
    return f


def label_video(path: str) -> list[dict]:
    """Upload a video, send it to Gemini with the prompt, return parsed labels."""
    video = upload_video(path)
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        print(f"  Labeling with {MODEL_NAME}...")
        resp = model.generate_content(
            [video, PROMPT],
            request_options={"timeout": 600},
        )
        text = resp.text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    finally:
        try:
            genai.delete_file(video.name)
        except Exception:
            pass


def label_batch(video_dir: str, output_dir: str, limit: int | None = None):
    """Label all .mp4s in a folder, save JSON results."""
    video_dir = Path(video_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    videos = sorted(video_dir.glob("*.mp4"))
    if limit:
        videos = videos[:limit]

    print(f"Found {len(videos)} videos.\n")

    for i, vp in enumerate(videos, 1):
        out = output_dir / f"{vp.stem}_labels.json"
        if out.exists():
            print(f"[{i}/{len(videos)}] SKIP {vp.name} (exists)")
            continue

        print(f"[{i}/{len(videos)}] {vp.name}")
        try:
            labels = label_video(str(vp))
            with open(out, "w") as f:
                json.dump({"video": vp.name, "labels": labels}, f, indent=2)
            print(f"  -> {out}  ({len(labels)} chunks)\n")
        except Exception as e:
            print(f"  ERROR: {e}\n")

        # Rate limit buffer (free tier = 10 RPM)
        if i < len(videos):
            time.sleep(10)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Label Minecraft videos with Gemini")
    p.add_argument("--video", type=str, help="Single video path")
    p.add_argument("--video-dir", type=str, help="Directory of .mp4 files")
    p.add_argument("--output-dir", type=str,
                   default=str(config.VLA_DATA_DIR / "10xx" / "labels"))
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()

    if args.video:
        result = label_video(args.video)
        print(json.dumps(result, indent=2))
    elif args.video_dir:
        label_batch(args.video_dir, args.output_dir, args.limit)
    else:
        # Default: use project video dir
        default = config.VLA_DATA_DIR / "10xx" / "videos"
        if default.exists():
            label_batch(str(default), args.output_dir, args.limit)
        else:
            print("No videos found. Use --video or --video-dir.")
            sys.exit(1)
