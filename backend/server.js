import express from "express";
import cors from "cors";
import multer from "multer";
import fs from "fs";
import path from "path";
import "dotenv/config";
import Groq from "groq-sdk";
import { pipeline } from "@huggingface/transformers";

import { processDocument } from "./process-pdf.js";
import { searchDb } from "./db.js";

const app = express();
app.use(cors());
app.use(express.json());

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

const uploadsDir = path.join(process.cwd(), "uploads");
fs.mkdirSync(uploadsDir, { recursive: true });
const upload = multer({ dest: uploadsDir });

app.post("/upload", upload.single("document"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "no file attached" });
    }
    await processDocument(req.file.path);
    fs.unlinkSync(req.file.path);
    return res.json({ message: "file uploaded successfully!" });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: "Failed to process document" });
  }
});

app.post("/chat", async (req, res) => {
  const { question } = req.body;
  const embedder = await pipeline(
    "feature-extraction",
    "Xenova/all-MiniLM-L6-v2"
  );
  const output = await embedder(question, { pooling: "mean", normalize: true });
  const queryvector = output.tolist()[0];
  output.dispose();

  const searchResults = await searchDb([queryvector]);

  const retrievedChunks = searchResults.documents[0];
  if (!retrievedChunks || retrievedChunks.length === 0) {
    return res.json({ answer: "No relevant sources found in the database" });
  }

  const contextString = retrievedChunks.join("\n\n---\n\n");

  const prompt = `You are a helpful study assistant. Answer the user's question using ONLY the provided context below. 
            If the context does not contain the answer, say "I don't have enough information in the provided document to answer that."
            
            Context:
            ${contextString}

            Question:
            ${question}`;

  const chatcompletion = await groq.chat.completions.create({
    messages: [{ content: prompt, role: "user" }],
    model: "llama-3.1-8b-instant",
    temperature: 0.1,
  });

  return res.json({
    answer: chatcompletion.choices[0].message.content,
    sources: searchResults.metadatas[0],
  });
});

const port = 3000;
app.listen(port, () => {
  console.log("server running successfully at port 3000");
});
