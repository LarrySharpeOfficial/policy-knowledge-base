# Architecture decision: local vertical slice

Use two independent static products joined by an explicit, versioned policy snapshot. The library builds Markdown sources into static HTML and deterministic JSON. LarrySharpe.com vendors one snapshot and checksum at build time; neither site depends on the other at runtime.

This keeps hosting inexpensive, makes rollback a Git revert, avoids a database and paid per-query AI calls, and preserves independent failure domains. WordPress remains an option only if frequent nontechnical browser editing becomes an immediate requirement. It is not needed for the canonical policy library.

The first slice uses small dependency-free browser search because three records do not justify a larger index. Pagefind is the preferred next step when corpus size makes measured search quality or payload size inadequate.

The 2026-11-09 decision to defer WebMCP is superseded for a bounded experiment. WebMCP is included only as a read-only progressive enhancement over the existing versioned snapshot: `search_policies` returns stable slugs and `get_policy` returns an exact published record. Static HTML and JSON remain canonical, unsupported browsers keep identical human-facing behavior, and no runtime service or external query dependency is added.

Chrome still describes WebMCP as a proposed, origin-trial feature. Local verification uses Chrome's testing flag; production activation requires an origin-trial token configured at build time and a live discovery check. Registration is all-or-none and abort-backed. If the API changes, the trial expires, registration harms the human UI, or the tool contract returns incorrect records, roll back by reverting the WebMCP integration commit or removing the origin-trial variable; the baseline site remains independently usable.

Primary references:

- https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
- https://pagefind.app/docs/
- https://json-schema.org/specification
- https://wordpress.org/documentation/article/faq-installation/
- https://developer.chrome.com/docs/ai/webmcp
- https://www.w3.org/WAI/WCAG22/quickref/
