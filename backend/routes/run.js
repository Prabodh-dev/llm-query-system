import express from "express";
import axios from "axios";
import fs from "fs";
import path from "path";
import FormData from "form-data";
import logger from "../utils/logger.js";
import dotenv from "dotenv";
dotenv.config();

const router = express.Router();

//  Bajaj API Bearer Token Middleware
router.use((req, res, next) => {
  const token = req.headers["authorization"];
  if (!token || token !== `Bearer ${process.env.HACKRX_API_KEY}`) {
    logger.warn("Unauthorized access attempt.");
    return res.status(401).json({ error: "Unauthorized" });
  }
  next();
});

//  POST /hackrx/run
router.post("/run", async (req, res) => {
  try {
    const { documents, questions } = req.body;

    if (!documents || !Array.isArray(questions) || !questions.length) {
      logger.warn("Missing documents or questions in request");
      return res.status(400).json({ error: "Missing documents or questions" });
    }

    //  Save PDF to /temp folder
    const filePath = path.join(path.resolve("temp"), `doc_${Date.now()}.pdf`);
    const response = await axios.get(documents, { responseType: "stream" });

    await new Promise((resolve, reject) => {
      const stream = fs.createWriteStream(filePath);
      response.data.pipe(stream);
      stream.on("finish", resolve);
      stream.on("error", reject);
    });

    logger.info(" PDF downloaded successfully");

    //  Prepare form data for FastAPI
    const formData = new FormData();
    formData.append("file", fs.createReadStream(filePath));
    formData.append("query", JSON.stringify(questions));

    //  Call LLM FastAPI (no auth header)
    const llmRes = await axios.post(process.env.LLM_API_URL, formData, {
      headers: formData.getHeaders(),
    });

    //  Clean up temp file
    fs.unlinkSync(filePath);
    logger.info(" LLM processing complete");

    //  Send final response
    return res.status(200).json({
      answers: llmRes.data.answers || [],
    });
  } catch (err) {
    logger.error(" Run endpoint error:", err.message);
    res.status(500).json({ error: "Processing failed" });
  }
});

export default router;
