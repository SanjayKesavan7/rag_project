# LangFlow Integration for ChefRAG

## Overview

ChefRAG's multi-agent architecture can be visualized and extended using [LangFlow](https://www.langflow.org/) — a visual framework for building LangChain applications.

The `chefrag_flow.json` file contains a LangFlow-compatible flow that demonstrates the ChefRAG RAG pipeline.

## Setup Instructions

### 1. Install LangFlow

```bash
pip install langflow
```

### 2. Start LangFlow

```bash
langflow run
```

This opens the LangFlow UI at `http://localhost:7860`.

### 3. Import the ChefRAG Flow

1. In the LangFlow UI, click **"New Project"** → **"Blank Flow"**
2. Click the **Upload** icon (or **Import**) in the top-right
3. Select `chefrag_flow.json` from this directory
4. The flow will load with all components pre-configured

### 4. Configure API Keys

After importing, you'll need to set your API keys:
- Click on the **ChatGroq** node → enter your `GROQ_API_KEY`
- The HuggingFace embeddings node uses the free `all-MiniLM-L6-v2` model (no API key needed)

### 5. Run the Flow

Click the **Run** button (▶️) to start the flow. You can then interact with it through LangFlow's built-in chat interface.

## Flow Architecture

The LangFlow flow mirrors ChefRAG's architecture:

```
User Input → ChatGroq LLM → Tool Router → [Recipe Search | Recipe Adaptation | Nutrition Info | Shopping List]
                                              ↕
                                     ChromaDB Vector Store
                                              ↕
                                   HuggingFace Embeddings
```

## Customizing the Flow

You can extend the flow in LangFlow's visual editor by:
- Adding new tools/agents
- Changing the LLM model
- Adjusting chunking parameters
- Adding more vector store collections
- Integrating with external recipe APIs

## Notes

- The LangFlow flow is a simplified version of the full ChefRAG system
- The full system (Python backend + React frontend) provides a richer experience
- LangFlow is great for prototyping and visualizing the pipeline
