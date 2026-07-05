import { ChromaClient } from "chromadb";

const client = new ChromaClient({ path: "http://localhost:8000" });
const COLLECTION_NAME = "my_notes_collection";

async function getCollection() {
  return await client.getOrCreateCollection({ name: COLLECTION_NAME });
}

export async function saveToDb(chunks) {
  const collection = await getCollection();

  const ids = chunks.map((_, i) => `chunk_${Date.now()}_${i}`);
  const embeddings = chunks.map((c) => c.vector);
  const documents = chunks.map((c) => c.text);
  const metadatas = chunks.map((c) => c.metadata);

  await collection.add({
    ids: ids,
    embeddings: embeddings,
    documents: documents,
    metadatas: metadatas,
  });
  console.log("wrote to chroma db successfully!");
}

export async function searchDb(queryVector, limit = 3) {
  const collection = await getCollection();

  const results = await collection.query({
    queryEmbeddings: queryVector,
    nResults: limit,
  });

  return results;
}
