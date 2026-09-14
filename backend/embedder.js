import { pipeline } from "@huggingface/transformers";

let embedderPromise = null;

export function getEmbedder() {
  if (!embedderPromise) {
    embedderPromise = pipeline(
      "feature-extraction",
      "Xenova/all-MiniLM-L6-v2"
    );
  }

  return embedderPromise;
}
