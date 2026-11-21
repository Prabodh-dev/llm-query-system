import assert from "node:assert/strict";
import http from "node:http";
import { after, before, describe, it } from "node:test";
import { createApp } from "../src/app.js";
import { HttpError } from "../src/errors.js";
import { createLlmClient } from "../src/llmClient.js";
import { createLogger } from "../src/logger.js";
import { loadConfig } from "../src/config.js";

const KEY = "test-key";
const config = {
  apiKey: KEY,
  maxQuestions: 3,
  rateLimitPerMin: 1000,
};
const silent = createLogger({ level: "error", stream: { write() {} } });

function listen(app) {
  return new Promise((resolve) => {
    const server = app.listen(0, () => resolve({ server, base: `http://127.0.0.1:${server.address().port}` }));
  });
}

const call = (base, { body, headers = {}, raw } = {}) =>
  fetch(`${base}/hackrx/run`, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${KEY}`, ...headers },
    body: raw ?? JSON.stringify(body),
  });

describe("gateway", () => {
  let ctx;
  let behaviour = async ({ questions }) => questions.map((q) => `a:${q}`);

  before(async () => {
    const app = createApp({ config, logger: silent, llmClient: (p, o) => behaviour(p, o) });
    ctx = await listen(app);
  });
  after(() => ctx.server.close());

  const valid = { documents: "https://example.com/p.pdf", questions: ["one", "two"] };

  it("serves health without auth", async () => {
    const res = await fetch(`${ctx.base}/health`);
    assert.equal(res.status, 200);
    assert.deepEqual(await res.json(), { status: "ok" });
  });

  it("rejects missing and wrong tokens", async () => {
    assert.equal((await call(ctx.base, { body: valid, headers: { authorization: "" } })).status, 401);
    assert.equal((await call(ctx.base, { body: valid, headers: { authorization: "Bearer nope" } })).status, 401);
    assert.equal((await call(ctx.base, { body: valid, headers: { authorization: KEY } })).status, 401);
  });

  it("returns answers for a valid request", async () => {
    const res = await call(ctx.base, { body: valid });
    assert.equal(res.status, 200);
    assert.deepEqual(await res.json(), { answers: ["a:one", "a:two"] });
    assert.ok(res.headers.get("x-request-id"));
  });

  it("forwards a valid caller request id", async () => {
    let seen;
    behaviour = async ({ questions }, { requestId }) => ((seen = requestId), questions.map(() => "x"));
    await call(ctx.base, { body: valid, headers: { "x-request-id": "abc-123" } });
    assert.equal(seen, "abc-123");
    behaviour = async ({ questions }) => questions.map((q) => `a:${q}`);
  });

  for (const [name, body] of [
    ["missing documents", { questions: ["q"] }],
    ["non-http url", { documents: "file:///etc/passwd", questions: ["q"] }],
    ["not a url", { documents: "nope", questions: ["q"] }],
    ["empty questions", { documents: valid.documents, questions: [] }],
    ["blank question", { documents: valid.documents, questions: [" "] }],
    ["non-string question", { documents: valid.documents, questions: [1] }],
    ["too many questions", { documents: valid.documents, questions: ["a", "b", "c", "d"] }],
  ]) {
    it(`400 on ${name}`, async () => {
      const res = await call(ctx.base, { body });
      assert.equal(res.status, 400);
      assert.equal((await res.json()).code, "invalid_request");
    });
  }

  it("400 on malformed JSON", async () => {
    const res = await call(ctx.base, { raw: "{bad" });
    assert.equal(res.status, 400);
    assert.equal((await res.json()).code, "invalid_json");
  });

  it("maps upstream errors without leaking details", async () => {
    behaviour = async () => {
      throw new HttpError(504, "upstream_timeout", "The LLM service timed out");
    };
    const timeout = await call(ctx.base, { body: valid });
    assert.equal(timeout.status, 504);

    behaviour = async () => {
      throw new Error("secret internal detail");
    };
    const crash = await call(ctx.base, { body: valid });
    assert.equal(crash.status, 500);
    assert.ok(!JSON.stringify(await crash.json()).includes("secret"));
    behaviour = async ({ questions }) => questions.map((q) => `a:${q}`);
  });

  it("404 for unknown routes", async () => {
    assert.equal((await fetch(`${ctx.base}/nope`)).status, 404);
  });
});

describe("rate limiting", () => {
  it("returns 429 after the limit", async () => {
    const app = createApp({
      config: { ...config, rateLimitPerMin: 2 },
      logger: silent,
      llmClient: async ({ questions }) => questions,
    });
    const { server, base } = await listen(app);
    const body = { documents: "https://example.com/p.pdf", questions: ["q"] };
    const statuses = [];
    for (let i = 0; i < 3; i++) statuses.push((await call(base, { body })).status);
    server.close();
    assert.deepEqual(statuses, [200, 200, 429]);
  });
});

describe("llm client", () => {
  let upstream;
  let base;
  let handler;

  before(async () => {
    upstream = http.createServer((req, res) => {
      let data = "";
      req.on("data", (c) => (data += c));
      req.on("end", () => handler(req, res, data));
    });
    await new Promise((r) => upstream.listen(0, r));
    base = `http://127.0.0.1:${upstream.address().port}/generate`;
  });
  after(() => upstream.close());

  const reply = (res, status, payload) => {
    res.writeHead(status, { "content-type": "application/json" });
    res.end(JSON.stringify(payload));
  };
  const client = (extra = {}) => createLlmClient({ url: base, timeoutMs: 500, ...extra });
  const payload = { documents: "https://e.com/a.pdf", questions: ["q1", "q2"] };

  it("returns answers and sends auth + request id", async () => {
    let seen;
    handler = (req, res, body) => {
      seen = { auth: req.headers.authorization, id: req.headers["x-request-id"], body: JSON.parse(body) };
      reply(res, 200, { answers: ["a", "b"] });
    };
    const answers = await client({ token: "svc" })(payload, { requestId: "rid" });
    assert.deepEqual(answers, ["a", "b"]);
    assert.deepEqual(seen, { auth: "Bearer svc", id: "rid", body: payload });
  });

  it("forwards 422 from upstream", async () => {
    handler = (_q, res) => reply(res, 422, { error: "The PDF could not be parsed", code: "invalid_document" });
    await assert.rejects(client()(payload), (e) => e.status === 422 && e.code === "invalid_document");
  });

  it("maps upstream 500/502 to 502", async () => {
    handler = (_q, res) => reply(res, 500, { error: "boom" });
    await assert.rejects(client()(payload), (e) => e.status === 502);
  });

  it("maps a slow upstream to 504", async () => {
    handler = () => {};
    await assert.rejects(client()(payload), (e) => e.status === 504);
  });

  it("rejects malformed or misaligned answers", async () => {
    handler = (_q, res) => reply(res, 200, { answers: ["only one"] });
    await assert.rejects(client()(payload), (e) => e.status === 502 && e.code === "upstream_invalid_response");
  });
});

describe("config", () => {
  it("fails fast on missing variables", () => {
    assert.throws(() => loadConfig({}), /HACKRX_API_KEY, LLM_API_URL/);
  });
  it("validates URL and numbers", () => {
    assert.throws(() => loadConfig({ HACKRX_API_KEY: "k", LLM_API_URL: "nope" }), /valid URL/);
    assert.throws(
      () => loadConfig({ HACKRX_API_KEY: "k", LLM_API_URL: "http://x", PORT: "abc" }),
      /PORT/
    );
  });
  it("applies defaults", () => {
    const c = loadConfig({ HACKRX_API_KEY: "k", LLM_API_URL: "http://x" });
    assert.equal(c.port, 3000);
    assert.equal(c.maxQuestions, 50);
  });
});
