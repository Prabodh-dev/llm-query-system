function toInt(env, key, fallback) {
  const raw = env[key];
  if (raw === undefined || raw === "") return fallback;
  const value = Number.parseInt(raw, 10);
  if (!Number.isInteger(value) || value <= 0) {
    throw new Error(`${key} must be a positive integer, got "${raw}"`);
  }
  return value;
}

export function loadConfig(env = process.env) {
  const missing = ["HACKRX_API_KEY", "LLM_API_URL"].filter((key) => !env[key]);
  if (missing.length) {
    throw new Error(`Missing required environment variables: ${missing.join(", ")}`);
  }
  try {
    new URL(env.LLM_API_URL);
  } catch {
    throw new Error("LLM_API_URL must be a valid URL");
  }
  return {
    port: toInt(env, "PORT", 3000),
    apiKey: env.HACKRX_API_KEY,
    llmApiUrl: env.LLM_API_URL,
    llmServiceToken: env.LLM_SERVICE_TOKEN || "",
    llmTimeoutMs: toInt(env, "LLM_TIMEOUT_MS", 120_000),
    maxQuestions: toInt(env, "MAX_QUESTIONS", 50),
    rateLimitPerMin: toInt(env, "RATE_LIMIT_PER_MIN", 60),
    logLevel: env.LOG_LEVEL || "info",
  };
}
