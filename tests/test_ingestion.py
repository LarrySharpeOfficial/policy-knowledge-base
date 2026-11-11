import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ingestion_common import build_passages, normalize_title
from inventory_youtube import build_inventory


class IngestionHelperTests(unittest.TestCase):
    def test_title_normalization_groups_equivalent_titles(self):
        self.assertEqual(normalize_title("Taxes, Jobs & Growth!"), "taxes jobs growth")
        self.assertEqual(normalize_title("  TAXES — Jobs + Growth  "), "taxes jobs growth")

    def test_passages_preserve_timestamp_boundaries(self):
        snippets = [
            {"text": "one", "start": 0, "duration": 10},
            {"text": "two", "start": 10, "duration": 10},
            {"text": "three", "start": 50, "duration": 5},
        ]
        passages = build_passages(snippets, max_seconds=30, max_chars=100)
        self.assertEqual(len(passages), 2)
        self.assertEqual(passages[0], {"start_seconds": 0.0, "end_seconds": 20.0, "text": "one two"})
        self.assertEqual(passages[1]["start_seconds"], 50.0)

    def test_offline_inventory_is_deterministic_and_finds_duplicate_titles(self):
        test_temp = ROOT / ".test-tmp"
        test_temp.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=test_temp) as temporary:
            base = Path(temporary)
            channels = base / "channels.json"
            channels.write_text(json.dumps({"channels": [
                {"name": "One", "channel_id": "one", "canonical_url": "https://example.invalid/one"},
                {"name": "Two", "channel_id": "two", "canonical_url": "https://example.invalid/two"},
            ]}), encoding="utf-8")
            one = base / "one.jsonl"
            two = base / "two.jsonl"
            one.write_text(json.dumps({"id": "aaaaaaaaaaa", "title": "Fix Property Taxes!", "duration": 60}) + "\n", encoding="utf-8")
            two.write_text(json.dumps({"id": "bbbbbbbbbbb", "title": "Fix property taxes", "duration": 61}) + "\n", encoding="utf-8")
            output = base / "inventory.json"
            inventory = build_inventory(channels, output, "2026-01-01", {"one": one, "two": two})
            self.assertEqual(inventory["summary"], {"total_entries": 2, "unique_video_ids": 2, "duplicate_title_groups": 1})
            first = output.read_bytes()
            build_inventory(channels, output, "2026-01-01", {"one": one, "two": two})
            self.assertEqual(first, output.read_bytes())


class GeneratedIngestionArtifactTests(unittest.TestCase):
    def test_public_inventory_and_review_queue_are_bounded(self):
        inventory = json.loads((ROOT / "data" / "video-inventory.json").read_text(encoding="utf-8"))
        queue = json.loads((ROOT / "data" / "editorial-review-queue.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(inventory["summary"]["total_entries"], 480)
        self.assertEqual(queue["item_count"], 8)
        inventory_ids = {video["video_id"] for video in inventory["videos"]}
        self.assertTrue(all(item["video_id"] in inventory_ids for item in queue["items"]))
        self.assertTrue(all(item["published_date"] for item in queue["items"]))
        self.assertTrue(all(item["publication_status"] == "not_publishable" for item in queue["items"]))
        self.assertTrue(all(item["editorial_status"] == "pending_source_review" for item in queue["items"]))


if __name__ == "__main__":
    unittest.main()
