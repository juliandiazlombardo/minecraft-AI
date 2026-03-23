"""
Minecraft Video Labeling with Gemini 2.5 Flash
================================================
Labels gameplay videos with visual descriptions using Google's Gemini API.
Gemini natively accepts video input — no frame extraction needed.

Usage:
    # Label a single video
    python label_videos_gemini.py --video path/to/video.mp4

    # Label all videos in a directory
    python label_videos_gemini.py --video-dir data/10xx/videos

    # Customize output and prompt
    python label_videos_gemini.py --video-dir data/10xx/videos --output-dir labels/ --interval 10
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[4]  # up to "My Minecraft AI Project"
load_dotenv(PROJECT_ROOT / ".env")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# The prompt you send alongside the video. Tweak this to get the labels you need.
DEFAULT_PROMPT = """You are analyzing a Minecraft gameplay video. For every ~10-second segment, provide:

1. **environment**: Biome/location the player is in (e.g., plains, cave, forest, nether)
2. **visible_blocks**: Key blocks visible (e.g., stone, dirt, oak_log, diamond_ore)
3. **visible_entities**: Any mobs or entities visible (e.g., zombie, cow, item_frame)
4. **player_action**: What the player is doing (e.g., mining_block, walking_forward, attacking_entity, looking_around, crafting, opening_inventory, swimming, jumping)
5. **held_item**: What item the player appears to be holding (e.g., diamond_pickaxe, empty_hand)
6. **summary**: A short natural-language sentence describing the segment.

Return your response as a JSON array where each element represents one segment:
```json
[
    {
        "segment_start_sec": 0,
        "segment_end_sec": 10,
        "environment": "forest",
        "visible_blocks": ["oak_log", "grass_block", "dirt"],
        "visible_entities": ["pig"],
        "player_action": "chopping_tree",
        "held_item": "iron_axe",
        "summary": "Player is chopping an oak tree in a forest biome."
    }
]
```

Be concise and use Minecraft-accurate terminology. Return ONLY valid JSON, no markdown fences."""


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def upload_video(video_path: str) -> genai.types.File:
    """Upload a video to Gemini's File API and wait until it's ready."""
    print(f"  Uploading {Path(video_path).name}...")
    video_file = genai.upload_file(path=video_path)

    # Poll until processing is complete
    while video_file.state.name == "PROCESSING":
        print("  Processing video...")
        time.sleep(5)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise RuntimeError(f"Video processing failed: {video_file.name}")

    print(f"  Upload complete: {video_file.uri}")
    return video_file


def label_video(video_path: str, prompt: str = DEFAULT_PROMPT, model_name: str = "gemini-2.5-flash-preview-05-20") -> list[dict]:
    """
    Send a video to Gemini and get structured labels back.

    Args:
        video_path: Path to the .mp4 file
        prompt: The labeling prompt
        model_name: Which Gemini model to use

    Returns:
        List of segment label dicts
    """
    video_file = upload_video(video_path)

    try:
        model = genai.GenerativeModel(model_name=model_name)

        print(f"  Requesting labels from {model_name}...")
        response = model.generate_content(
            [video_file, prompt],
            request_options={"timeout": 600},  # 10 min timeout for long videos
        )

        # Parse the JSON response
        text = response.text.strip()

        # Handle case where model wraps in markdown code fences
        if text.startswith("```"):
            text = text.split("\n", 1)[1]  # remove first line
            text = text.rsplit("```", 1)[0]  # remove last fence
            text = text.strip()

        labels = json.loads(text)
        print(f"  Got {len(labels)} segments labeled.")
        return labels

    finally:
        # Clean up the uploaded file
        try:
            genai.delete_file(video_file.name)
            print("  Cleaned up uploaded file.")
        except Exception:
            pass  # non-critical


def label_video_batch(
    video_dir: str,
    output_dir: str,
    prompt: str = DEFAULT_PROMPT,
    model_name: str = "gemini-2.5-flash-preview-05-20",
    limit: int | None = None,
):
    """
    Label all .mp4 files in a directory and save results as JSON.

    Args:
        video_dir: Directory containing .mp4 files
        output_dir: Where to save label JSON files
        prompt: The labeling prompt
        model_name: Gemini model name
        limit: Max number of videos to process (None = all)
    """
    video_dir = Path(video_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    videos = sorted(video_dir.glob("*.mp4"))
    if limit:
        videos = videos[:limit]

    print(f"Found {len(videos)} videos to label.\n")

    results_summary = []

    for i, video_path in enumerate(videos, 1):
        output_file = output_dir / f"{video_path.stem}_labels.json"

        # Skip already-labeled videos
        if output_file.exists():
            print(f"[{i}/{len(videos)}] SKIP {video_path.name} (already labeled)")
            continue

        print(f"[{i}/{len(videos)}] Labeling {video_path.name}...")

        try:
            labels = label_video(str(video_path), prompt, model_name)

            # Save labels
            with open(output_file, "w") as f:
                json.dump(
                    {"video": video_path.name, "model": model_name, "labels": labels},
                    f,
                    indent=2,
                )

            results_summary.append({"video": video_path.name, "segments": len(labels), "status": "ok"})
            print(f"  Saved to {output_file}\n")

        except Exception as e:
            print(f"  ERROR: {e}\n")
            results_summary.append({"video": video_path.name, "segments": 0, "status": f"error: {e}"})

        # Rate limit: Gemini free tier is 10 RPM, be conservative
        if i < len(videos):
            print("  Waiting 10s (rate limit)...")
            time.sleep(10)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    ok = sum(1 for r in results_summary if r["status"] == "ok")
    total_segs = sum(r["segments"] for r in results_summary)
    print(f"  Labeled: {ok}/{len(results_summary)} videos")
    print(f"  Total segments: {total_segs}")
    print(f"  Output dir: {output_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Label Minecraft videos with Gemini 2.5 Flash")
    parser.add_argument("--video", type=str, help="Path to a single video file")
    parser.add_argument("--video-dir", type=str, help="Directory with .mp4 files to batch label")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(PROJECT_ROOT / "src/tools/movement/VLA model_(work-in-progress)/data/10xx/labels"),
        help="Where to save label JSON files",
    )
    parser.add_argument("--model", type=str, default="gemini-2.5-flash-preview-05-20", help="Gemini model name")
    parser.add_argument("--limit", type=int, default=None, help="Max videos to process")
    parser.add_argument("--prompt", type=str, default=None, help="Custom prompt (overrides default)")

    args = parser.parse_args()
    prompt = args.prompt or DEFAULT_PROMPT

    if args.video:
        # Single video mode
        labels = label_video(args.video, prompt, args.model)
        print(json.dumps(labels, indent=2))

    elif args.video_dir:
        # Batch mode
        label_video_batch(args.video_dir, args.output_dir, prompt, args.model, args.limit)

    else:
        # Default: label videos in the project data dir
        default_video_dir = PROJECT_ROOT / "src/tools/movement/VLA model_(work-in-progress)/data/10xx/videos"
        if default_video_dir.exists():
            label_video_batch(str(default_video_dir), args.output_dir, prompt, args.model, args.limit)
        else:
            print("No videos found. Use --video or --video-dir to specify input.")
            sys.exit(1)


if __name__ == "__main__":
    main()
