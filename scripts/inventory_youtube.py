#!/usr/bin/env python3
"""Inventory every public video on the configured Larry Sharpe channels."""
import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from ingestion_common import normalize_title

ROOT = Path(__file__).resolve().parents[1]
CHANNELS_PATH = ROOT / "content" / "channels.json"
DEFAULT_OUTPUT = ROOT / "data" / "video-inventory.json"


def load_jsonl(text: str) -> list[dict]:
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise SystemExit(f"Invalid yt-dlp JSON on line {number}: {error}") from error
    return rows


def fetch_channel(url: str) -> list[dict]:
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--flat-playlist",
        "--dump-json",
        "--ignore-errors",
        "--no-warnings",
        url.rstrip("/") + "/videos",
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8")
    return load_jsonl(result.stdout)


def parse_sources(values: list[str]) -> dict[str, Path]:
    sources = {}
    for value in values:
        if "=" not in value:
            raise SystemExit("--from-jsonl must be CHANNEL_ID=PATH")
        channel_id, path = value.split("=", 1)
        sources[channel_id] = Path(path)
    return sources


def build_inventory(channels_path: Path, output: Path, checked_on: str, jsonl_sources: dict[str, Path]) -> dict:
    channel_config = json.loads(channels_path.read_text(encoding="utf-8"))["channels"]
    videos = []
    channel_summaries = []

    for channel in channel_config:
        channel_id = channel["channel_id"]
        if channel_id in jsonl_sources:
            rows = load_jsonl(jsonl_sources[channel_id].read_text(encoding="utf-8"))
        else:
            rows = fetch_channel(channel["canonical_url"])
        clean_rows = []
        for position, row in enumerate(rows, 1):
            video_id = row.get("id")
            title = row.get("title")
            if not video_id or not title:
                continue
            clean_rows.append({
                "video_id": str(video_id),
                "channel_id": channel_id,
                "channel_name": channel["name"],
                "position": position,
                "title": str(title),
                "normalized_title": normalize_title(str(title)),
                "duration_seconds": int(row["duration"]) if row.get("duration") is not None else None,
                "availability": row.get("availability"),
                "live_status": row.get("live_status"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
            })
        videos.extend(clean_rows)
        channel_summaries.append({
            "channel_id": channel_id,
            "name": channel["name"],
            "source_url": channel["canonical_url"],
            "video_count": len(clean_rows),
        })

    duplicate_map = defaultdict(list)
    for video in videos:
        duplicate_map[video["normalized_title"]].append(video["video_id"])
    duplicate_groups = [
        {"normalized_title": title, "video_ids": sorted(video_ids)}
        for title, video_ids in sorted(duplicate_map.items())
        if title and len(video_ids) > 1
    ]

    inventory = {
        "inventory_version": "0.1.0",
        "checked_on": checked_on,
        "channels": channel_summaries,
        "summary": {
            "total_entries": len(videos),
            "unique_video_ids": len({video["video_id"] for video in videos}),
            "duplicate_title_groups": len(duplicate_groups),
        },
        "duplicate_titles": duplicate_groups,
        "videos": videos,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(output), **inventory["summary"], "channels": len(channel_summaries)}))
    return inventory


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--channels", type=Path, default=CHANNELS_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--checked-on", default=date.today().isoformat())
    parser.add_argument("--from-jsonl", action="append", default=[], metavar="CHANNEL_ID=PATH")
    args = parser.parse_args()
    build_inventory(args.channels, args.output, args.checked_on, parse_sources(args.from_jsonl))
