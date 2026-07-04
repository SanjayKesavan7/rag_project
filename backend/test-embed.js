import { pipeline } from "@huggingface/transformers";

async function testEmbedding() {
  console.log(
    "Downloading/Loading model... (This takes a moment on the first run)"
  );

  // Load the all-MiniLM-L6-v2 model
  const embedder = await pipeline(
    "feature-extraction",
    "Xenova/all-MiniLM-L6-v2"
  );

  const textToEmbed = "This is a test sentence for my RAG project.";

  console.log(`Embedding text: "${textToEmbed}"`);

  // Generate the vector (mean pooling and normalization are standard for semantic search)
  const output = await embedder(textToEmbed, {
    pooling: "mean",
    normalize: true,
  });

  console.log("Success! Here is a slice of your 384-dimensional vector:");
  // Convert the tensor to a standard JavaScript array and slice the first 5 values
  console.log(output.tolist()[0].slice(0, 5));
}

testEmbedding();
