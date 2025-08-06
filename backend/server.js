import express from "express";
import dotenv from "dotenv";
dotenv.config();

const PORT = process.env.PORT;

const app = express();

app.use(express.json());

// Mount the /hackrx/run route
import runRoute from "./routes/run.js";
app.use("/hackrx", runRoute);

// Optional: Logging middleware
// import logger from './utils/logger'; app.use(logger);

const server = app.listen(PORT, () => {
  console.log(`🚀 Backend running on PORT: ${PORT}`);
});
