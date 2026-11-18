"use strict";

const results = document.querySelector("#policy-results");
const search = document.querySelector("#policy-search");
const status = document.querySelector("#search-status");
const MAX_TOOL_RESULTS = 10;
let policies = [];

const esc = value => String(value).replace(/[&<>"']/g, char => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
})[char]);

const normalized = value => String(value ?? "").trim().toLowerCase();

function policyUrl(slug) {
  return new URL(`policies/${encodeURIComponent(slug)}.html`, document.baseURI).href;
}

function matchesQuery(policy, query) {
  return JSON.stringify(policy).toLowerCase().includes(normalized(query));
}

function validateLimit(limit) {
  const resolved = limit === undefined ? 5 : limit;
  if (!Number.isInteger(resolved) || resolved < 1 || resolved > MAX_TOOL_RESULTS) {
    throw new TypeError(`limit must be an integer from 1 to ${MAX_TOOL_RESULTS}`);
  }
  return resolved;
}

function findPolicies(query, limit) {
  const resolvedQuery = normalized(query);
  if (!resolvedQuery) throw new TypeError("query must be a non-empty string");
  return policies.filter(policy => matchesQuery(policy, resolvedQuery)).slice(0, validateLimit(limit));
}

function policySummary(policy) {
  return {
    slug: policy.slug,
    title: policy.title,
    problem: policy.problem,
    proposal: policy.proposal,
    topics: policy.topics,
    editorial_status: policy.editorial_status,
    publication_status: policy.publication_status,
    url: policyUrl(policy.slug),
  };
}

function policyDetail(slug) {
  const resolvedSlug = normalized(slug);
  if (!resolvedSlug) throw new TypeError("slug must be a non-empty string");
  const policy = policies.find(candidate => candidate.slug === resolvedSlug);
  if (!policy) throw new RangeError(`Unknown policy slug: ${slug}`);
  return { ...policy, url: policyUrl(policy.slug) };
}

function render(items) {
  status.textContent = `${items.length} ${items.length === 1 ? "policy" : "policies"} found`;
  results.innerHTML = items.map(policy => `<article class="card"><p class="meta">${esc(policy.editorial_status.replaceAll("_", " "))}</p><h3><a href="policies/${encodeURIComponent(policy.slug)}.html">${esc(policy.title)}</a></h3><p>${esc(policy.problem)}</p><ul class="tags">${policy.topics.map(topic => `<li>${esc(topic)}</li>`).join("")}</ul></article>`).join("");
}

function filterVisiblePolicies() {
  const query = normalized(search.value);
  render(query ? policies.filter(policy => matchesQuery(policy, query)) : policies);
}

const toolAnnotations = {
  readOnlyHint: true,
  consequentialHint: false,
  untrustedContentHint: true,
  debugging: false,
};

const searchTool = {
  name: "search_policies",
  description: "Search Larry Sharpe's published policy library by a natural-language topic or problem and return stable policy slugs for detailed lookup.",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string", description: "Topic, proposal, or problem to search for." },
      limit: { type: "integer", minimum: 1, maximum: MAX_TOOL_RESULTS, default: 5 },
    },
    required: ["query"],
    additionalProperties: false,
  },
  outputSchema: {
    type: "object",
    properties: {
      query: { type: "string" },
      count: { type: "integer" },
      results: {
        type: "array",
        items: {
          type: "object",
          properties: {
            slug: { type: "string" },
            title: { type: "string" },
            problem: { type: "string" },
            proposal: { type: "string" },
            topics: { type: "array", items: { type: "string" } },
            editorial_status: { type: "string" },
            publication_status: { type: "string" },
            url: { type: "string", format: "uri" },
          },
          required: ["slug", "title", "problem", "proposal", "topics", "editorial_status", "publication_status", "url"],
          additionalProperties: false,
        },
      },
    },
    required: ["query", "count", "results"],
    additionalProperties: false,
  },
  annotations: toolAnnotations,
  async execute({ query, limit } = {}) {
    const matches = findPolicies(query, limit).map(policySummary);
    return { query: String(query).trim(), count: matches.length, results: matches };
  },
};

const detailTool = {
  name: "get_policy",
  description: "Return the complete published Larry Sharpe policy record for an exact slug returned by search_policies, including source excerpts and timestamp links.",
  inputSchema: {
    type: "object",
    properties: {
      slug: { type: "string", description: "Exact policy slug returned by search_policies." },
    },
    required: ["slug"],
    additionalProperties: false,
  },
  outputSchema: {
    type: "object",
    properties: {
      schema_version: { type: "string" },
      id: { type: "string" },
      slug: { type: "string" },
      title: { type: "string" },
      problem: { type: "string" },
      proposal: { type: "string" },
      implementation: { type: "array", items: { type: "string" } },
      benefits: { type: "array", items: { type: "string" } },
      tradeoffs: { type: "array", items: { type: "string" } },
      jurisdictions: { type: "array", items: { type: "string" } },
      topics: { type: "array", items: { type: "string" } },
      attribution: { type: "string" },
      editorial_status: { type: "string" },
      publication_status: { type: "string" },
      body_markdown: { type: "string" },
      sources: {
        type: "array",
        items: {
          type: "object",
          properties: {
            type: { type: "string" },
            title: { type: "string" },
            url: { type: "string", format: "uri" },
            video_id: { type: "string" },
            channel: { type: "string" },
            published_date: { type: "string" },
            excerpt_start_seconds: { type: "number" },
            timestamp_url: { type: "string", format: "uri" },
            quote: { type: "string" },
            transcript_type: { type: "string" },
          },
          required: ["type", "title", "url", "video_id", "channel", "published_date", "excerpt_start_seconds", "timestamp_url", "quote", "transcript_type"],
          additionalProperties: false,
        },
      },
      url: { type: "string", format: "uri" },
    },
    required: ["schema_version", "id", "slug", "title", "problem", "proposal", "implementation", "benefits", "tradeoffs", "jurisdictions", "topics", "attribution", "editorial_status", "publication_status", "body_markdown", "sources", "url"],
    additionalProperties: true,
  },
  annotations: toolAnnotations,
  async execute({ slug } = {}) {
    return policyDetail(slug);
  },
};

async function registerWebMCPTools() {
  if (!document.modelContext?.registerTool) return;
  const controller = new AbortController();
  try {
    await Promise.all([searchTool, detailTool].map(tool => Promise.resolve().then(
      () => document.modelContext.registerTool(tool, { signal: controller.signal }),
    )));
  } catch (error) {
    controller.abort();
    console.error("WebMCP tool registration failed; all policy tools were removed.", error);
  }
}

fetch("policy-snapshot-v0.1.0.json")
  .then(response => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then(data => {
    policies = data.policies;
    render(policies);
    search.addEventListener("input", filterVisiblePolicies);
    return registerWebMCPTools();
  })
  .catch(() => {
    status.textContent = "Search is unavailable. Use the policy links below.";
  });
