#!/usr/bin/env python3
"""Fetch timestamped YouTube transcripts for an explicit review batch."""
import argparse
import json
from datetime import date
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "data" / "video-inventory.json"
OUTPUT_DIR = ROOT / "data" / "transcripts"
FAILURES_PATH = ROOT / "data" / "transcript-failures.json"


def load_ids(args) -> list[str]:
    ids = list(args.video_id)
    if args.from_file:
        for line in args.from_file.read_text(encoding="utf-8").splitlines():
            value = line.strip()
            if value and not value.startswith("#"):
                ids.append(value)
    return list(dict.fromkeys(ids))


def fetch_batch(video_ids: list[str], inventory_path: Path, output_dir: Path, failures_path: Path, checked_on: str, languages: list[str]) -> dict:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    by_id = {video["video_id"]: video for video in inventory["videos"]}
    api = YouTubeTranscriptApi()
    output_dir.mkdir(parents=True, exist_ok=True)
    failures = []
    written = []

    for video_id in video_ids:
        metadata = by_id.get(video_id)
        if not metadata:
            failures.append({"video_id": video_id, "error_type": "NotInInventory", "message": "Video ID is not present in data/video-inventory.json"})
            continue
        try:
            transcript = api.fetch(video_id, languages=languages)
            snippets = [
                {"text": snippet.text, "start": round(snippet.start, 3), "duration": round(snippet.duration, 3)}
                for snippet in transcript
            ]
            record = {
                "transcript_version": "0.1.0",
                "fetched_on": checked_on,
                "video_id": video_id,
                "url": metadata["url"],
                "title": metadata["title"],
                "channel_id": metadata["channel_id"],
                "channel_name": metadata["channel_name"],
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "snippet_count": len(snippets),
                "snippets": snippets,
            }
            path = output_dir / f"{video_id}.json"
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
            written.append(video_id)
        except Exception as error:
            message = " ".join(str(error).split())
            failures.append({"video_id": video_id, "error_type": type(error).__name__, "message": message[:1000]})

    failure_record = {"checked_on": checked_on, "attempted": len(video_ids), "failure_count": len(failures), "failures": sorted(failures, key=lambda item: item["video_id"])}
    failures_path.parent.mkdir(parents=True, exist_ok=True)
    failures_path.write_text(json.dumps(failure_record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    result = {"attempted": len(video_ids), "written": len(written), "failed": len(failures), "video_ids": written}
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", action="append", default=[])
    parser.add_argument("--from-file", type=Path)
    parser.add_argument("--inventory", type=Path, default=INVENTORY_PATH)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--failures", type=Path, default=FAILURES_PATH)
    parser.add_argument("--checked-on", default=date.today().isoformat())
    parser.add_argument("--languages", default="en", help="Comma-separated preferred language codes")
    args = parser.parse_args()
    ids = load_ids(args)
    if not ids:
        raise SystemExit("Provide --video-id or --from-file")
    fetch_batch(ids, args.inventory, args.output_dir, args.failures, args.checked_on, [value.strip() for value in args.languages.split(",") if value.strip()])
