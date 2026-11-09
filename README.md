# Larry Sharpe Policy Knowledge Base — local prototype

A source-backed static policy library prototype. Markdown files with embedded JSON metadata are the human-authored source; the build emits deterministic JSON and static HTML without a database.

Status: local prototype only. The initial records are draft, unapproved, and not licensed for public reuse.

## Build and test

    python scripts/build.py
    python -m unittest discover -s tests -v
    python -m http.server 8081 --directory dist

Open http://127.0.0.1:8081/.

Every record keeps source URLs, timestamped links, verbatim excerpts from YouTube auto-generated transcripts, and explicit editorial/publication status. Transcript errors are not silently corrected. Generated summaries require Jerome's approval before publication.
