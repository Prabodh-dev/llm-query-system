// backend/routes/upload.js

const express = require('express');
const multer = require('multer');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const dotenv = require('dotenv');
const path = require('path');
const crypto = require('crypto');
const logger = require('../utils/logger');

dotenv.config();

const router = express.Router();

// Configure AWS S3 (v3 style)
const s3Client = new S3Client({
    region: process.env.AWS_REGION,
    credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    },
});

// Multer config to store files in memory
const storage = multer.memoryStorage();
const upload = multer({ storage });

// POST /hackerx/upload
router.post('/upload', upload.single('file'), async (req, res) => {
  try {
    const file = req.file;
    if (!file) {
      return res.status(400).json({ error: 'No file provided' });
    }

    // Unique file name
    const uniqueName = `${Date.now()}-${crypto.randomBytes(6).toString('hex')}${path.extname(file.originalname)}`;

    const params = {
      Bucket: process.env.AWS_BUCKET_NAME,
      Key: uniqueName,
      Body: file.buffer,
      ContentType: file.mimetype,
      ACL: 'public-read', // 👈 important line to allow public access
    };

    const command = new PutObjectCommand(params);
    const data = await s3Client.send(command);

    const fileUrl = `https://${process.env.AWS_BUCKET_NAME}.s3.${process.env.AWS_REGION}.amazonaws.com/${uniqueName}`;
    
    logger.info(`File uploaded to ${fileUrl}`);
    res.status(200).json({ message: 'Upload successful', url: fileUrl });
  } catch (err) {
    logger.error('Upload failed', err);
    res.status(500).json({ error: 'Failed to upload file' });
  }
});

module.exports = router;
