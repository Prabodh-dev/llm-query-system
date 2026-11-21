import crypto from "node:crypto";
import express from "express";
import helmet from "helmet";
import { rateLimit } from "express-rate-limit";
import { bearerAuth } from "./auth.js";
import { HttpError } from "./errors.js";

const REQUEST_ID = /^[\w-]{1,64}$/;

function validateRunBody(body, maxQuestions) {
  const { documents, questions } = body ?? {};
  if (typeof documents !== "string" || !documents.trim()) {
    throw new HttpError(400, "invalid_request", "`documents` must be a URL string");
  }
  let url;
  try {
    url = new URL(documents);
  } catch {
    throw new HttpError(400, "invalid_request", "`documents` must be a valid URL");
  }
  if (!["http:", "https:"].includes(url.protocol)) {
    throw new HttpError(400, "invalid_request", "`documents` must be an http(s) URL");
  }
  if (!Array.isArray(questions) || questions.length === 0) {
    throw new HttpError(400, "invalid_request", "`questions` must be a non-empty array");
  }
  if (questions.length > maxQuestions) {
    throw new HttpError(400, "invalid_request", `At most ${maxQuestions} questions are allowed`);
  }
  if (!questions.every((q) => typeof q === "string" && q.trim())) {
    throw new HttpError(400, "invalid_request", "`questions` must contain non-empty strings");
  }
  return { documents: documents.trim(), questions: questions.map((q) => q.trim()) };
}

export function createApp({ config, llmClient, logger }) {
  const app = express();
  app.disable("x-powered-by");
  app.set("trust proxy", 1);

  app.use(helmet());
  app.use((req, res, next) => {
    const incoming = req.get("x-request-id");
    req.id = incoming && REQUEST_ID.test(incoming) ? incoming : crypto.randomUUID();
    res.set("X-Request-ID", req.id);
    const started = process.hrtime.bigint();
    res.on("finish", () => {
      logger.info("request", {
        requestId: req.id,
        method: req.method,
        path: req.path,
        status: res.statusCode,
        ms: Number((process.hrtime.bigint() - started) / 1_000_000n),
      });
    });
    next();
  });
  app.use(express.json({ limit: "100kb" }));

  app.get("/health", (_req, res) => res.json({ status: "ok" }));

  const limiter = rateLimit({
    windowMs: 60_000,
    limit: config.rateLimitPerMin,
    standardHeaders: true,
    legacyHeaders: false,
    handler: (_req, _res, next) =>
      next(new HttpError(429, "rate_limited", "Too many requests, slow down")),
  });

  const router = express.Router();
  router.use(bearerAuth(config.apiKey));
  router.use(limiter);

  router.post("/run", async (req, res) => {
    const payload = validateRunBody(req.body, config.maxQuestions);
    const answers = await llmClient(payload, { requestId: req.id });
    res.json({ answers });
  });
  app.use("/hackrx", router);

  app.use((_req, _res, next) => next(new HttpError(404, "not_found", "Not found")));

  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, _next) => {
    let { status, code, message } = err;
    if (err.type === "entity.parse.failed") {
      [status, code, message] = [400, "invalid_json", "Request body is not valid JSON"];
    } else if (err.type === "entity.too.large") {
      [status, code, message] = [413, "payload_too_large", "Request body is too large"];
    } else if (!(err instanceof HttpError)) {
      logger.error("unhandled error", { requestId: req.id, error: err.message });
      [status, code, message] = [500, "internal_error", "Internal server error"];
    } else if (status >= 500) {
      logger.error("upstream failure", { requestId: req.id, code, error: message });
    }
    res.status(status).json({ error: message, code });
  });

  return app;
}
