const express = require('express');
const multer = require('multer');
const path = require('path');
const logger = require('../utils/logger');

const router = express.Router();

// Multer config for file uploads
const storage = multer.memoryStorage();
const upload = multer({ 
  storage,
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB limit
  },
  fileFilter: (req, file, cb) => {
    // Allow only PDF and DOCX files
    const allowedTypes = ['.pdf', '.docx'];
    const fileExtension = path.extname(file.originalname).toLowerCase();
    
    if (allowedTypes.includes(fileExtension)) {
      cb(null, true);
    } else {
      cb(new Error('Only PDF and DOCX files are allowed'), false);
    }
  }
});

// POST /hackrx/run
router.post('/run', upload.single('file'), async (req, res) => {
  try {
    // Validate file upload
    if (!req.file) {
      return res.status(400).json({ 
        error: 'No file provided',
        message: 'Please upload a PDF or DOCX file'
      });
    }

    // Validate questions
    let questions;
    try {
      // Handle both string and array formats
      if (typeof req.body.questions === 'string') {
        questions = JSON.parse(req.body.questions);
      } else {
        questions = req.body.questions;
      }
      
      if (!questions || !Array.isArray(questions) || questions.length === 0) {
        return res.status(400).json({ 
          error: 'Invalid questions format',
          message: 'Questions must be an array with at least one question'
        });
      }
    } catch (parseError) {
      return res.status(400).json({ 
        error: 'Invalid questions format',
        message: 'Questions must be a valid JSON array string'
      });
    }

    // Validate each question
    for (let i = 0; i < questions.length; i++) {
      const question = questions[i];
      if (!question || typeof question !== 'string' || question.trim().length === 0) {
        return res.status(400).json({ 
          error: 'Invalid question format',
          message: `Question at index ${i} is empty or invalid`
        });
      }
    }

    // Log the request details
    logger.info(`Processing file: ${req.file.originalname} (${req.file.size} bytes)`);
    logger.info(`Questions received: ${questions.length} questions`);

    // Prepare data structure for future integration
    const requestData = {
      file: {
        originalName: req.file.originalname,
        buffer: req.file.buffer,
        mimetype: req.file.mimetype,
        size: req.file.size
      },
      questions: questions.map(q => q.trim()),
      timestamp: new Date().toISOString(),
      requestId: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };

    // TODO: Integration points for future development
    // 1. Send file to Dhanya's Python utils (parser.py, cleaner.py)
    // 2. Send processed text + questions to Prabodh's FastAPI
    
    logger.info(`Request ${requestData.requestId} prepared for processing`);

    // Return success response with request details
    res.status(200).json({
      message: 'Request received successfully',
      requestId: requestData.requestId,
      fileInfo: {
        name: requestData.file.originalName,
        size: requestData.file.size,
        type: requestData.file.mimetype
      },
      questionsCount: requestData.questions.length,
      status: 'pending_processing',
      note: 'Integration with Python utils and FastAPI will be added next'
    });

  } catch (error) {
    logger.error('Error in /run endpoint:', error);
    
    if (error.message === 'Only PDF and DOCX files are allowed') {
      return res.status(400).json({ 
        error: 'Invalid file type',
        message: error.message
      });
    }

    res.status(500).json({ 
      error: 'Internal server error',
      message: 'Failed to process request'
    });
  }
});

// GET /hackrx/run/health - Health check endpoint
router.get('/run/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    message: 'Run endpoint is operational',
    timestamp: new Date().toISOString()
  });
});

module.exports = router;
