import fs from "fs";
import path from "path";
import { PDFExtract } from "pdf.js-extract";
import { pipeline } from "@huggingface/transformers";
import { saveToDb } from "./db.js";

const pdfExtract = new PDFExtract();

export function chunkText(
  text,
  sourceName,
  chunkSize = 300,
  chunkOverlap = 50
) {
  if (chunkSize <= chunkOverlap) {
    throw new Error(
      `Invalid chunk settings: chunkSize (${chunkSize}) must be greater than chunkOverlap (${chunkOverlap}).`
    );
  }

  const texts = text.split(/\s+/).filter((word) => word.length > 0);
  const chunks = [];
  const step = chunkSize - chunkOverlap;

  for (let i = 0; i < texts.length; i += step) {
    let chunk = texts.slice(i, i + chunkSize).join(" ");
    chunks.push({
      text: chunk,
      metadata: {
        source: sourceName,
      },
    });
  }

  return chunks;
}

export async function processDocument(filePath) {
  const dataBuffer = fs.readFileSync(filePath);
  const data = await pdfExtract.extractBuffer(dataBuffer, {});
  const fullText = data.pages
    .map((page) => page.content.map((item) => item.str).join(" "))
    .join("\n");

  const sourceName = path.basename(filePath);
  const chunks = chunkText(fullText, sourceName, 300, 50);

  const embedder = await pipeline(
    "feature-extraction",
    "Xenova/all-MiniLM-L6-v2"
  );

  const textArray = chunks.map((chunk) => chunk.text);

  const output = await embedder(textArray, {
    pooling: "mean",
    normalize: true,
  });

  const vectors = output.tolist();
  for (let i = 0; i < chunks.length; i++) {
    chunks[i].vector = vectors[i];
  }
  output.dispose();
  console.log(chunks);
  console.log(`Processed ${chunks.length} chunks from ${sourceName}.`);
  await saveToDb(chunks);
  return chunks;
}
