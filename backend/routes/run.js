import express from "express";
import axios from "axios";
import logger from "../utils/logger.js";
import dotenv from "dotenv";
dotenv.config();

const router = express.Router();

// ✅ Bearer Token Auth Middleware
router.use((req, res, next) => {
  const token = req.headers["authorization"];
  const expected = `Bearer ${process.env.HACKRX_API_KEY}`;

  if (!token || token !== expected) {
    logger.warn("⛔ Unauthorized access attempt.");
    return res.status(401).json({ error: "Unauthorized" });
  }

  next();
});

// ✅ POST /hackrx/run
router.post("/run", async (req, res) => {
  try {
    const { documents, questions } = req.body;

    if (!documents || !Array.isArray(questions) || questions.length === 0) {
      logger.warn("⚠️ Missing documents or questions in request body");
      return res.status(400).json({ error: "Missing documents or questions" });
    }

    logger.info("📤 Sending request to FastAPI LLM...");

    const llmResponse = await axios.post(
      `${process.env.LLM_API_URL}/generate`,
      {
        documents,
        questions,
      }
    );

    const { answers, relevant_clauses } = llmResponse.data;

    logger.info("✅ Response received from LLM");

    return res.status(200).json({
      answers: answers || [],
      relevant_clauses: relevant_clauses || [],
    });
  } catch (error) {
    logger.error("❌ Error in /hackrx/run:", error.message);
    return res.status(500).json({ error: "LLM processing failed" });
  }
});

export default router;
