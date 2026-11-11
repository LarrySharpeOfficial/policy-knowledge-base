#!/usr/bin/env python3
"""Build deterministic timestamped search passages from fetched transcripts."""
import argparse
import json
from pathlib import Path

from ingestion_common import build_passages

ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPTS_DIR = ROOT / "data" / "transcripts"
DEFAULT_OUTPUT = ROOT / "data" / "video-passages.json"


def build(transcripts_dir: Path, output: Path, max_seconds: float, max_chars: int) -> dict:
    records = []
    for path in sorted(transcripts_dir.glob("*.json")):
        transcript = json.loads(path.read_text(encoding="utf-8"))
        video_id = transcript["video_id"]
        passages = build_passages(transcript["snippets"], max_seconds=max_seconds, max_chars=max_chars)
        for index, passage in enumerate(passages, 1):
            start = int(passage["start_seconds"])
            records.append({
                "passage_id": f"{video_id}:{index:04d}",
                "video_id": video_id,
                "channel_id": transcript["channel_id"],
                "title": transcript["title"],
                "start_seconds": passage["start_seconds"],
                "end_seconds": passage["end_seconds"],
                "timestamp_url": f"https://www.youtube.com/watch?v={video_id}&t={start}s",
                "text": passage["text"],
                "provenance": {
                    "transcript_type": "youtube_auto_generated" if transcript["is_generated"] else "youtube_creator_provided",
                    "language_code": transcript["language_code"],
                    "editorial_status": "unreviewed_source_passage",
                },
            })
    artifact = {
        "passage_index_version": "0.1.0",
        "video_count": len({record["video_id"] for record in records}),
        "passage_count": len(records),
        "passages": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(output), "video_count": artifact["video_count"], "passage_count": artifact["passage_count"]}))
    return artifact


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcripts", type=Path, default=TRANSCRIPTS_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-seconds", type=float, default=45.0)
    parser.add_argument("--max-chars", type=int, default=700)
    args = parser.parse_args()
    build(args.transcripts, args.output, args.max_seconds, args.max_chars)
