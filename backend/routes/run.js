import express from "express";
import axios from "axios";
import logger from "../utils/logger.js";
import dotenv from "dotenv";
dotenv.config();

const router = express.Router();

// Bajaj API Bearer Token Middleware
router.use((req, res, next) => {
  const token = req.headers["authorization"];
  if (!token || token !== `Bearer ${process.env.HACKRX_API_KEY}`) {
    logger.warn("Unauthorized access attempt.");
    return res.status(401).json({ error: "Unauthorized" });
  }
  next();
});

// POST /hackrx/run
router.post("/run", async (req, res) => {
  try {
    const { documents, questions } = req.body;

    if (!documents || !Array.isArray(questions) || !questions.length) {
      logger.warn("Missing documents or questions in request");
      return res.status(400).json({ error: "Missing documents or questions" });
    }

    logger.info("📥 Sending to FastAPI...");

    // ✅ Send JSON directly to FastAPI
    const llmRes = await axios.post(`${process.env.LLM_API_URL}/generate`, {
      documents,
      questions,
    });

    logger.info("✅ LLM response received");

    return res.status(200).json({
      answers: llmRes.data.answers || [],
      relevant_clauses: llmRes.data.relevant_clauses || [],
    });
  } catch (err) {
    logger.error("❌ Run endpoint error:", err.message);
    return res.status(500).json({ error: "LLM processing failed" });
  }
});

export default router;
