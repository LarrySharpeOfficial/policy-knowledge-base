# Architecture decision: local vertical slice

Use two independent static products joined by an explicit, versioned policy snapshot. The library builds Markdown sources into static HTML and deterministic JSON. LarrySharpe.com vendors one snapshot and checksum at build time; neither site depends on the other at runtime.

This keeps hosting inexpensive, makes rollback a Git revert, avoids a database and paid per-query AI calls, and preserves independent failure domains. WordPress remains an option only if frequent nontechnical browser editing becomes an immediate requirement. It is not needed for the canonical policy library.

The first slice uses small dependency-free browser search because three records do not justify a larger index. Pagefind is the preferred next step when corpus size makes measured search quality or payload size inadequate.

Do not include WebMCP in version one. As reviewed on 2026-11-09, Chrome describes it as a proposed standard with experimental/origin-trial access rather than a dependable cross-browser baseline. Keep semantic HTML and versioned JSON suitable for humans and machines; revisit only after interoperable unflagged support and a demonstrated use case.

Primary references:

- https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
- https://pagefind.app/docs/
- https://json-schema.org/specification
- https://wordpress.org/documentation/article/faq-installation/
- https://developer.chrome.com/docs/ai/webmcp
- https://www.w3.org/WAI/WCAG22/quickref/
