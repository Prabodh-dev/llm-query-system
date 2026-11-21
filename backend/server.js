import "dotenv/config";
import { createApp } from "./src/app.js";
import { loadConfig } from "./src/config.js";
import { createLlmClient } from "./src/llmClient.js";
import { createLogger } from "./src/logger.js";

let config;
try {
  config = loadConfig();
} catch (err) {
  console.error(`Configuration error: ${err.message}`);
  process.exit(1);
}

const logger = createLogger({ level: config.logLevel });
const llmClient = createLlmClient({
  url: config.llmApiUrl,
  timeoutMs: config.llmTimeoutMs,
  token: config.llmServiceToken,
});
const app = createApp({ config, llmClient, logger });

const server = app.listen(config.port, () => {
  logger.info("gateway listening", { port: config.port });
});

function shutdown(signal) {
  logger.info("shutting down", { signal });
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(1), 10_000).unref();
}
process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
