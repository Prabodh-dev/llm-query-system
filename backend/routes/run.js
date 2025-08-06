import express from "express";
import axios from "axios";
import logger from "../utils/logger.js";
import dotenv from "dotenv";
dotenv.config();

const router = express.Router();

// Authorization middleware
router.use((req, res, next) => {
  const token = req.headers["authorization"];
  const expected = `Bearer ${process.env.HACKRX_API_KEY}`;
  if (!token || token !== expected) {
    logger.warn("Unauthorized access attempt.");
    return res.status(401).json({ error: "Unauthorized" });
  }
  next();
});

// POST /hackrx/run
router.post("/run", async (req, res) => {
  const { documents, questions } = req.body;

  if (!documents || !Array.isArray(questions) || !questions.length) {
    logger.warn("❌ Missing documents or questions");
    return res.status(400).json({ error: "Missing documents or questions" });
  }

  try {
    const llmUrl = `${process.env.LLM_API_URL}/generate`;
    logger.info(`📡 Calling LLM at: ${llmUrl}`);

    const llmRes = await axios.post(llmUrl, { documents, questions });

    logger.info("✅ LLM responded");

    return res.status(200).json({
      answers: llmRes.data.answers || [],
      relevant_clauses: llmRes.data.relevant_clauses || [],
    });
  } catch (err) {
    logger.error("❌ LLM proxy error:", err.message);
    console.error("📛 LLM ERROR:", err?.response?.data || err);

    return res.status(502).json({
      error: "Failed to fetch from LLM",
      details: err?.response?.data || err.message,
    });
  }
});

export default router;
