const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const logger = require('./utils/logger');

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

// Routes
const uploadRoutes = require('./routes/upload');
const runRoutes = require('./routes/run');

app.use('/hackerx', uploadRoutes); // Mounts upload routes under /hackerx
app.use('/hackerx', runRoutes);    // Mounts run routes under /hackerx


const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  logger.info(`Server running at http://localhost:${PORT}`);
});
