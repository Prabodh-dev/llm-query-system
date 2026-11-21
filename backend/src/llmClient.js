import axios from "axios";
import { HttpError } from "./errors.js";

const PASS_THROUGH = new Set([400, 413, 422]);

function toUpstreamError(err) {
  if (err instanceof HttpError) return err;
  if (err.code === "ECONNABORTED" || err.code === "ETIMEDOUT") {
    return new HttpError(504, "upstream_timeout", "The LLM service timed out");
  }
  const status = err.response?.status;
  if (status && PASS_THROUGH.has(status)) {
    const data = err.response.data ?? {};
    return new HttpError(
      status,
      data.code || "upstream_rejected",
      typeof data.error === "string" ? data.error : "Request rejected by the LLM service"
    );
  }
  if (status === 504) {
    return new HttpError(504, "upstream_timeout", "The LLM service timed out");
  }
  return new HttpError(502, "upstream_unavailable", "The LLM service failed to process the request");
}

export function createLlmClient({ url, timeoutMs, token }) {
  const http = axios.create({
    timeout: timeoutMs,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  return async function generate({ documents, questions }, { requestId } = {}) {
    let data;
    try {
      ({ data } = await http.post(
        url,
        { documents, questions },
        { headers: requestId ? { "X-Request-ID": requestId } : {} }
      ));
    } catch (err) {
      throw toUpstreamError(err);
    }
    const answers = data?.answers;
    if (
      !Array.isArray(answers) ||
      answers.length !== questions.length ||
      !answers.every((a) => typeof a === "string")
    ) {
      throw new HttpError(502, "upstream_invalid_response", "The LLM service returned a malformed response");
    }
    return answers;
  };
}
