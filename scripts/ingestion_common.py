#!/usr/bin/env python3
"""Shared deterministic helpers for the video-ingestion pipeline."""
import html
import re
import unicodedata


def normalize_title(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "").casefold()
    text = html.unescape(text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def seconds(value) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return 0.0


def build_passages(snippets: list[dict], max_seconds: float = 45.0, max_chars: int = 700) -> list[dict]:
    passages = []
    current = []
    start = None
    end = None

    def flush() -> None:
        nonlocal current, start, end
        if not current or start is None or end is None:
            return
        passages.append({
            "start_seconds": round(start, 3),
            "end_seconds": round(end, 3),
            "text": " ".join(current).strip(),
        })
        current = []
        start = None
        end = None

    for snippet in snippets:
        text = " ".join(str(snippet.get("text", "")).split())
        if not text:
            continue
        snippet_start = seconds(snippet.get("start"))
        snippet_end = snippet_start + seconds(snippet.get("duration"))
        proposed_text = " ".join([*current, text])
        proposed_start = snippet_start if start is None else start
        proposed_end = max(snippet_end, end or snippet_end)
        if current and (proposed_end - proposed_start > max_seconds or len(proposed_text) > max_chars):
            flush()
            proposed_start = snippet_start
            proposed_end = snippet_end
        if start is None:
            start = proposed_start
        end = proposed_end
        current.append(text)
    flush()
    return passages
