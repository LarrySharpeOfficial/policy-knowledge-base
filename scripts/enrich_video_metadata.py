#!/usr/bin/env python3
"""Enrich an explicit review batch with verified per-video YouTube metadata."""
import argparse
import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BATCH = ROOT / "content" / "review-batches" / "initial-expansion-topics.json"
DEFAULT_OUTPUT = ROOT / "data" / "review-video-metadata.json"


def iso_date(value) -> str | None:
    if not value:
        return None
    text = str(value)
    try:
        return datetime.strptime(text, "%Y%m%d").date().isoformat()
    except ValueError:
        return None


def enrich(batch_path: Path, output: Path, checked_on: str) -> dict:
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    ids = [item["video_id"] for item in batch["items"]]
    command = [sys.executable, "-m", "yt_dlp", "--dump-json", "--skip-download", "--ignore-errors", "--no-warnings", *[f"https://www.youtube.com/watch?v={video_id}" for video_id in ids]]
    result = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8")
    raw = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    records = []
    for row in raw:
        video_id = row.get("id")
        if video_id not in ids:
            continue
        records.append({
            "video_id": video_id,
            "title": row.get("title"),
            "channel": row.get("channel"),
            "channel_id": row.get("channel_id"),
            "upload_date": iso_date(row.get("upload_date")),
            "duration_seconds": int(row["duration"]) if row.get("duration") is not None else None,
            "availability": row.get("availability"),
            "live_status": row.get("live_status"),
            "url": f"https://www.youtube.com/watch?v={video_id}",
        })
    found = {record["video_id"] for record in records}
    artifact = {
        "metadata_version": "0.1.0",
        "checked_on": checked_on,
        "batch_id": batch["batch_id"],
        "requested": len(ids),
        "found": len(records),
        "missing_video_ids": [video_id for video_id in ids if video_id not in found],
        "videos": sorted(records, key=lambda item: ids.index(item["video_id"])),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(output), "requested": artifact["requested"], "found": artifact["found"], "missing": len(artifact["missing_video_ids"])}))
    return artifact


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--checked-on", default=date.today().isoformat())
    args = parser.parse_args()
    enrich(args.batch, args.output, args.checked_on)
