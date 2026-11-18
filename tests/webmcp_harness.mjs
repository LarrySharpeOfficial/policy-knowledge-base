import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { setImmediate as waitForImmediate } from "node:timers/promises";

const appSource = fs.readFileSync(new URL("../static/app.js", import.meta.url), "utf8");
const samplePolicies = [
  {
    schema_version: "1.0.0",
    id: "policy-education",
    slug: "education-funding-portability",
    title: "Make education funding follow the student",
    problem: "School assignment and funding depend too much on district lines.",
    proposal: "Let education funding follow each student.",
    implementation: "Create portable education accounts.",
    benefits: ["More family choice"],
    tradeoffs: ["Requires transition rules"],
    jurisdictions: ["New York"],
    topics: ["education", "school choice"],
    attribution: "Larry Sharpe",
    editorial_status: "approved",
    publication_status: "published",
    sources: [{ type: "video", title: "Education interview", url: "https://example.test/video", video_id: "education-video", channel: "Larry Sharpe", published_date: "2026-01-01", excerpt_start_seconds: 10, timestamp_url: "https://example.test/video?t=10", quote: "Funding should follow the student.", transcript_type: "auto" }],
  },
  {
    schema_version: "1.0.0",
    id: "policy-healthcare",
    slug: "healthcare-direct-access",
    title: "Expand direct access to healthcare",
    problem: "Insurance-centered payment adds barriers.",
    proposal: "Expand direct care options.",
    implementation: "Remove barriers to direct primary care.",
    benefits: ["Lower administrative cost"],
    tradeoffs: ["Needs consumer safeguards"],
    jurisdictions: ["New York"],
    topics: ["healthcare", "direct care"],
    attribution: "Larry Sharpe",
    editorial_status: "approved",
    publication_status: "published",
    sources: [{ type: "video", title: "Healthcare interview", url: "https://example.test/video", video_id: "healthcare-video", channel: "Larry Sharpe", published_date: "2026-01-02", excerpt_start_seconds: 20, timestamp_url: "https://example.test/video?t=20", quote: "Direct care lowers costs.", transcript_type: "auto" }],
  },
  {
    schema_version: "1.0.0",
    id: "policy-cannabis",
    slug: "cannabis-like-a-plant",
    title: "Regulate cannabis like an ordinary plant",
    problem: "Cannabis rules remain unusually burdensome.",
    proposal: "Regulate cannabis like an ordinary legal product.",
    implementation: "Simplify licensing and taxation.",
    benefits: ["Lower barriers"],
    tradeoffs: ["Requires regulatory changes"],
    jurisdictions: ["New York"],
    topics: ["cannabis", "regulation"],
    attribution: "Larry Sharpe",
    editorial_status: "approved",
    publication_status: "published",
    sources: [{ type: "video", title: "Cannabis interview", url: "https://example.test/video", video_id: "cannabis-video", channel: "Larry Sharpe", published_date: "2026-01-03", excerpt_start_seconds: 30, timestamp_url: "https://example.test/video?t=30", quote: "Treat it like a plant.", transcript_type: "auto" }],
  },
];

function makeElement() {
  return {
    textContent: "",
    innerHTML: "",
    value: "",
    listeners: new Map(),
    addEventListener(type, callback) { this.listeners.set(type, callback); },
  };
}

async function runApp({ modelContext } = {}) {
  const elements = new Map([
    ["#policy-results", makeElement()],
    ["#policy-search", makeElement()],
    ["#search-status", makeElement()],
  ]);
  const document = {
    baseURI: "https://larrysharpeofficial.github.io/policy-knowledge-base/",
    querySelector(selector) { return elements.get(selector); },
  };
  if (modelContext !== undefined) document.modelContext = modelContext;
  const errors = [];
  const context = vm.createContext({
    AbortController,
    URL,
    document,
    fetch: async (url) => {
      assert.equal(url, "policy-snapshot-v0.1.0.json");
      return { ok: true, async json() { return { policies: structuredClone(samplePolicies) }; } };
    },
    console: { error(...args) { errors.push(args.map(String).join(" ")); } },
    structuredClone,
  });
  vm.runInContext(appSource, context, { filename: "static/app.js" });
  await waitForImmediate();
  await waitForImmediate();
  return { elements, errors };
}

async function testUnsupportedBrowser() {
  const { elements, errors } = await runApp();
  assert.equal(elements.get("#search-status").textContent, "3 policies found");
  assert.match(elements.get("#policy-results").innerHTML, /Make education funding follow the student/);
  assert.equal(elements.get("#policy-search").listeners.has("input"), true);
  elements.get("#policy-search").value = "healthcare";
  elements.get("#policy-search").listeners.get("input")();
  assert.equal(elements.get("#search-status").textContent, "1 policy found");
  assert.match(elements.get("#policy-results").innerHTML, /Expand direct access to healthcare/);
  assert.deepEqual(errors, []);
}

async function testToolContractsAndExecution() {
  const registrations = [];
  const modelContext = {
    async registerTool(tool, options) { registrations.push({ tool, options }); },
  };
  const { errors } = await runApp({ modelContext });
  assert.deepEqual(errors, []);
  assert.deepEqual(registrations.map(({ tool }) => tool.name), ["search_policies", "get_policy"]);
  for (const { tool } of registrations) {
    assert.deepEqual(JSON.parse(JSON.stringify(tool.annotations)), {
      readOnlyHint: true,
      consequentialHint: false,
      untrustedContentHint: true,
      debugging: false,
    });
    assert.equal(tool.inputSchema.type, "object");
    assert.equal(tool.outputSchema.type, "object");
  }

  const search = registrations[0].tool;
  const searchResult = await search.execute({ query: "EDUCATION", limit: 1 });
  assert.equal(searchResult.count, 1);
  assert.equal(searchResult.results[0].slug, "education-funding-portability");
  assert.equal(searchResult.results[0].url, "https://larrysharpeofficial.github.io/policy-knowledge-base/policies/education-funding-portability.html");
  await assert.rejects(() => search.execute({ query: "  " }), /query/i);
  await assert.rejects(() => search.execute({ query: "education", limit: 11 }), /limit/i);

  const detail = registrations[1].tool;
  const policy = await detail.execute({ slug: "education-funding-portability" });
  assert.equal(policy.slug, "education-funding-portability");
  assert.equal(policy.attribution, "Larry Sharpe");
  assert.equal(policy.sources[0].timestamp_url, "https://example.test/video?t=10");
  assert.equal(policy.url, "https://larrysharpeofficial.github.io/policy-knowledge-base/policies/education-funding-portability.html");
  await assert.rejects(() => detail.execute({ slug: "missing-policy" }), /unknown policy slug/i);
}

async function testRegistrationRollback() {
  const calls = [];
  const modelContext = {
    async registerTool(tool, options) {
      calls.push({ tool, options });
      if (tool.name === "get_policy") throw new Error("registration failed");
    },
  };
  const { elements } = await runApp({ modelContext });
  assert.equal(calls.length, 2);
  assert.equal(calls[0].options.signal, calls[1].options.signal);
  assert.equal(calls[0].options.signal.aborted, true);
  assert.equal(elements.get("#search-status").textContent, "3 policies found");
}

await testUnsupportedBrowser();
await testToolContractsAndExecution();
await testRegistrationRollback();
console.log(JSON.stringify({ scenarios: 3, tools: ["search_policies", "get_policy"], status: "ok" }));
