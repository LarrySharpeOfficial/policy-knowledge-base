# Larry Sharpe Policy Knowledge Base

A source-backed static policy library prototype. Markdown files with embedded JSON metadata are the human-authored source; the build emits deterministic JSON and static HTML without a database.

Status: public alpha. The initial records are approved for publication, source-backed, and still subject to correction as source review continues. No public reuse license has been approved yet.

## Build and test

    python scripts/build.py
    python -m unittest discover -s tests -v
    python -m http.server 8081 --directory dist

Open http://127.0.0.1:8081/.

Every record keeps source URLs, timestamped links, excerpts from YouTube auto-generated transcripts, and explicit editorial/publication status. Transcript errors are not silently corrected; readers should check the linked recording.
