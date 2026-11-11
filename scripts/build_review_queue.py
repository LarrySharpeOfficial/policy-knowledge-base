#!/usr/bin/env python3
"""Build a non-publishing editorial review queue from fetched source material."""
import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BATCH = ROOT / "content" / "review-batches" / "initial-expansion-topics.json"
DEFAULT_OUTPUT = ROOT / "data" / "editorial-review-queue.json"


def build(batch_path: Path, inventory_path: Path, metadata_path: Path, transcripts_dir: Path, passages_path: Path, output: Path) -> dict:
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    passages = json.loads(passages_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    videos = {video["video_id"]: video for video in inventory["videos"]}
    metadata_by_id = {video["video_id"]: video for video in metadata["videos"]}
    transcript_ids = {path.stem for path in transcripts_dir.glob("*.json")}
    passage_counts = Counter(passage["video_id"] for passage in passages["passages"])
    items = []

    for configured in batch["items"]:
        video_id = configured["video_id"]
        video = videos.get(video_id)
        if not video:
            raise SystemExit(f"Review video {video_id} is absent from inventory")
        items.append({
            "video_id": video_id,
            "title": video["title"],
            "channel_id": video["channel_id"],
            "url": video["url"],
            "duration_seconds": video["duration_seconds"],
            "published_date": metadata_by_id.get(video_id, {}).get("upload_date"),
            "candidate_topics": configured["candidate_topics"],
            "transcript_status": "fetched" if video_id in transcript_ids else "unavailable",
            "passage_count": passage_counts[video_id],
            "editorial_status": "pending_source_review",
            "publication_status": "not_publishable",
            "required_review": [
                "check transcript excerpts against audio",
                "identify direct claims and complete proposal context",
                "record objections, trade-offs, and missing implementation details",
                "obtain Jerome approval before creating or publishing a policy record"
            ],
        })

    artifact = {
        "queue_version": "0.1.0",
        "batch_id": batch["batch_id"],
        "item_count": len(items),
        "items": items,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(output), "batch_id": artifact["batch_id"], "item_count": artifact["item_count"]}))
    return artifact


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--inventory", type=Path, default=ROOT / "data" / "video-inventory.json")
    parser.add_argument("--metadata", type=Path, default=ROOT / "data" / "review-video-metadata.json")
    parser.add_argument("--transcripts", type=Path, default=ROOT / "data" / "transcripts")
    parser.add_argument("--passages", type=Path, default=ROOT / "data" / "video-passages.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.batch, args.inventory, args.metadata, args.transcripts, args.passages, args.output)
