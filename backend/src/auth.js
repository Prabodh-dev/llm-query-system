import crypto from "node:crypto";
import { HttpError } from "./errors.js";

const digest = (value) => crypto.createHash("sha256").update(value).digest();

/** Bearer-token middleware using a constant-time comparison. */
export function bearerAuth(apiKey) {
  const expected = digest(apiKey);
  return (req, _res, next) => {
    const [scheme, token] = (req.get("authorization") || "").trim().split(/\s+/);
    const valid =
      scheme?.toLowerCase() === "bearer" &&
      token &&
      crypto.timingSafeEqual(digest(token), expected);
    if (!valid) return next(new HttpError(401, "unauthorized", "Unauthorized"));
    next();
  };
}
