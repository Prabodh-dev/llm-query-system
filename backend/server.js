import express from "express";
import dotenv from "dotenv";
dotenv.config();

const PORT = process.env.PORT;

const app = express();

app.use(express.json());

const server = app.listen(PORT, () => {
  try {
    console.log(`Server running on PORT:${PORT}`);
  } catch (err) {
    console.log("Server connection error");
  }
});
