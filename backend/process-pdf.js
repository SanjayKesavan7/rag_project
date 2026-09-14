import fs from "fs";
import path from "path";
import { PDFExtract } from "pdf.js-extract";
import { saveToDb } from "./db.js";
import { getEmbedder } from "./embedder.js";
import { EMBEDDING_BATCH_SIZE } from "./constants.js";

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

function batchArray(items, batchSize) {
  const batches = [];

  for (let i = 0; i < items.length; i += batchSize) {
    batches.push(items.slice(i, i + batchSize));
  }

  return batches;
}

export async function processDocument(filePath, sourceNameOverride) {
  const dataBuffer = fs.readFileSync(filePath);
  const data = await pdfExtract.extractBuffer(dataBuffer, {});
  const fullText = data.pages
    .map((page) => page.content.map((item) => item.str).join(" "))
    .join("\n");

  const sourceName = path.basename(sourceNameOverride || filePath);
  const chunks = chunkText(fullText, sourceName, 300, 50);
  const embedder = await getEmbedder();
  const chunkBatches = batchArray(chunks, EMBEDDING_BATCH_SIZE);

  for (let i = 0; i < chunkBatches.length; i++) {
    const chunkBatch = chunkBatches[i];
    const output = await embedder(
      chunkBatch.map((chunk) => chunk.text),
      {
        pooling: "mean",
        normalize: true,
      }
    );

    const vectors = output.tolist();
    output.dispose();

    for (let j = 0; j < chunkBatch.length; j++) {
      chunkBatch[j].vector = vectors[j];
    }

    await saveToDb(chunkBatch);
  }

  return {
    sourceName,
    chunkCount: chunks.length,
  };
}
