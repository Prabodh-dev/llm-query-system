import express from "express";
import dotenv from "dotenv";
dotenv.config();

const PORT = process.env.PORT;

const app = express();

app.use(express.json());

import runRoute from "./routes/run.js";
app.use("/hackrx", runRoute);

const server = app.listen(PORT, () => {
  console.log(`🚀 Backend running on PORT: ${PORT}`);
});
