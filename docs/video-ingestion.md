# Video ingestion and editorial review

The video archive is source material, not automatically publishable policy content. This pipeline preserves provenance and timestamps while keeping source extraction separate from editorial approval.

## Current inventory

`data/video-inventory.json` inventories Larry's two initial own-channel sources:

- Larry Sharpe
- The Sharpe Way with Larry Sharpe

The first complete run found 480 public video entries: 368 on the Larry Sharpe channel and 112 on The Sharpe Way channel. Twenty-six normalized-title groups indicate likely reposts or closely duplicated programs; duplicate titles are retained because their video IDs and source URLs differ.

Flat channel inventory does not reliably expose publication dates. Do not invent dates. Enrich dates only from verified per-video metadata when a video enters editorial review.

## Environment

Install the optional ingestion tools separately from the dependency-free static-site build:

    python -m pip install -r requirements-ingestion.txt

The same commands can be run without changing the project environment through `uv`:

    uv run --with yt-dlp==2026.10.26 python scripts/inventory_youtube.py
    uv run --with youtube-transcript-api==1.2.5 python scripts/fetch_transcripts.py --from-file content/review-batches/initial-expansion.txt

## Workflow

1. Inventory configured channels:

       python scripts/inventory_youtube.py

   For reproducible offline rebuilding from prior yt-dlp JSONL output, provide one source per channel:

       python scripts/inventory_youtube.py \
         --from-jsonl CHANNEL_ID=channel.jsonl \
         --from-jsonl OTHER_CHANNEL_ID=other-channel.jsonl

2. Select an explicit editorial batch under `content/review-batches/`. Selection is not approval.

3. Enrich the selected videos with verified per-video metadata, including upload dates:

       python scripts/enrich_video_metadata.py

4. Fetch transcripts for that batch:

       python scripts/fetch_transcripts.py --from-file content/review-batches/initial-expansion.txt

   Transcript failures are written honestly to `data/transcript-failures.json`. Never create transcript text for an unavailable source.

5. Build timestamped passages:

       python scripts/build_video_passages.py

   Raw transcript files and the full passage index are local processing artifacts and are intentionally ignored by Git. The repository is public; do not publish full unreviewed transcripts or reconstruct a complete copyrighted program through passage output. Only approved, context-checked excerpts belong in published policy records.

6. Build the non-publishing review queue:

       python scripts/build_review_queue.py

7. Run all tests:

       python -m unittest discover -s tests -v

## Provenance and approval boundaries

- Every local passage retains video ID, channel ID, source title, start/end time, timestamp URL, language, and whether YouTube labels the transcript as auto-generated.
- Raw transcript passages are marked `unreviewed_source_passage`.
- Review-queue entries are marked `not_publishable`.
- Candidate topics are navigation aids, not policy interpretations.
- Before a policy record is created or published, review the recording, identify Larry's complete proposal in context, record material trade-offs and missing implementation details, and obtain Jerome's approval.
- Do not present auto-generated transcript text as a corrected quotation.

## Initial expansion batch

The first batch contains eight policy-rich videos covering transportation, housing, property tax, nuclear energy, non-tax infrastructure funding, state income tax, education reform, and homeschooling. All eight transcripts were available; the pipeline generated 75 timestamped passages. They remain pending source review and do not change the three-policy public snapshot.
