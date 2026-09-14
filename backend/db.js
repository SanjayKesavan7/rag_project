import { ChromaClient } from "chromadb";
import { CHROMA_INSERT_BATCH_SIZE } from "./constants.js";

const client = new ChromaClient({ path: "http://localhost:8000" });
const COLLECTION_NAME = "my_notes_collection";

async function getCollection() {
  return await client.getOrCreateCollection({ name: COLLECTION_NAME });
}

export async function saveToDb(chunks) {
  const collection = await getCollection();
  const batchSeed = `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

  for (let i = 0; i < chunks.length; i += CHROMA_INSERT_BATCH_SIZE) {
    const chunkBatch = chunks.slice(i, i + CHROMA_INSERT_BATCH_SIZE);

    await collection.add({
      ids: chunkBatch.map((_, index) => `chunk_${batchSeed}_${i + index}`),
      embeddings: chunkBatch.map((chunk) => chunk.vector),
      documents: chunkBatch.map((chunk) => chunk.text),
      metadatas: chunkBatch.map((chunk) => chunk.metadata),
    });
  }
}

export async function searchDb(queryVector, limit = 3, sourceName) {
  const collection = await getCollection();
  const queryOptions = {
    queryEmbeddings: queryVector,
    nResults: limit,
  };

  if (sourceName) {
    queryOptions.where = { source: { $eq: sourceName } };
  }

  const results = await collection.query(queryOptions);

  return results;
}
