# Larry Sharpe Policy Knowledge Base

A source-backed static policy library prototype. Markdown files with embedded JSON metadata are the human-authored source; the build emits deterministic JSON and static HTML without a database.

Status: public alpha. The initial records are approved for publication, source-backed, and still subject to correction as source review continues. No public reuse license has been approved yet.

## Build and test

    python scripts/build.py
    python -m unittest discover -s tests -v
    python -m http.server 8081 --directory dist

Open http://127.0.0.1:8081/.

Every record keeps source URLs, timestamped links, excerpts from YouTube auto-generated transcripts, and explicit editorial/publication status. Transcript errors are not silently corrected; readers should check the linked recording.

## WebMCP progressive enhancement

Compatible Chrome sessions can discover two read-only tools after the policy snapshot loads:

- `search_policies` searches the published records and returns stable slugs plus policy-page URLs.
- `get_policy` returns the complete published record for an exact slug, including timestamped sources and transcript excerpts.

The tools use the same in-memory snapshot as the visible search. Browsers without WebMCP keep the existing search and no-script fallback. No tool writes data, calls an external service, or changes the page.

WebMCP remains experimental. For local testing, enable `chrome://flags/#enable-webmcp-testing`, relaunch Chrome, serve `dist/`, and inspect the page with Chrome DevTools or the official Model Context Tool Inspector. The dependency-free behavioral harness can be run directly with:

    node tests/webmcp_harness.mjs

Production activation requires a Chrome origin-trial token for `https://larrysharpeofficial.github.io`. Configure the public token as the GitHub Actions repository variable `WEBMCP_ORIGIN_TRIAL_TOKEN`; the build emits the supported `<meta http-equiv="origin-trial">` tag only when that variable is non-empty. Record the token's expiration date in this section when it is issued, rotate or remove it before expiry, and verify tool discovery on the exact deployed URL. Until that variable is configured and the live discovery check passes, the code is preview-ready but production WebMCP activation is not claimed.

## Video ingestion

The repeatable inventory/transcript/passage workflow is documented in `docs/video-ingestion.md`. Extracted passages and review-queue entries remain non-publishable until their source context is reviewed and Jerome approves a policy record.
