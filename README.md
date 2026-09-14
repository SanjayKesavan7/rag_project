# ChefRAG — Intelligent Recipe RAG Agent 🧑‍🍳

An AI-powered recipe assistant built with **LangChain**, **ChromaDB**, and **Groq** that can search, adapt, and generate personalized cooking instructions from your recipe documents.

##  Architecture

| Component | Technology |
|-----------|------------|
| **Framework** | LangChain (Python) + LangFlow |
| **Architecture** | RAG-based **Multi-Agent** System |
| **Vector Database** | ChromaDB (persistent, local) |
| **LLM** | Groq — GPT OSS 120B |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` |
| **Backend** | Python / FastAPI |
| **Frontend** | React 19 / Vite |

### Multi-Agent System

```
User Query → Orchestrator Agent → [Tool Selection]
                                      ├──  Recipe Retrieval Agent (Hybrid RAG)
                                      ├──  Recipe Adaptation Agent
                                      ├──  Nutrition Analysis Agent
                                      └──  Shopping List Agent
                                              ↕
                                     ChromaDB Vector Store
                                              ↕
                                   HuggingFace Embeddings
```

**Agents:**
- **Orchestrator**: Routes queries to the right sub-agent using LangChain's tool-calling agent
- **Recipe Retrieval**: Hybrid RAG with 3-tier confidence strategy (never says "I don't know")
- **Recipe Adaptation**: Modifies recipes for dietary needs, ingredient substitutions, cuisine changes
- **Nutrition Analysis**: Estimates nutritional facts per serving
- **Shopping List**: Generates categorized shopping lists by store section

### Hybrid RAG Strategy

Unlike traditional RAG systems that fail when documents lack relevant information, ChefRAG uses a **3-tier confidence strategy**:

| Tier | Relevance Score | Behavior |
|------|----------------|----------|
| **HIGH** | ≥ 0.50 | Answer primarily from documents, cite sources |
| **MEDIUM** | 0.30 – 0.50 | Blend document context with LLM culinary knowledge |
| **LOW** | < 0.30 | Use LLM general knowledge, suggest uploading documents |

##  Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- A [Groq API key](https://console.groq.com/) (free tier available)

### 1. Backend Setup

```bash
cd backend-py

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env and set your GROQ_API_KEY

# Start the server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The UI will be available at `http://localhost:5173`.

### 3. Load Sample Recipes (Optional)

Upload the included sample recipe file through the UI, or via curl:

```bash
curl -X POST http://localhost:8000/upload \
  -F "document=@data/sample_recipes.txt"
```

##  Project Structure

```
ioc-project/
├── backend-py/                 # Python backend (LangChain + FastAPI)
│   ├── app/
│   │   ├── main.py             # FastAPI endpoints
│   │   ├── config.py           # Configuration & constants
│   │   ├── ingestion.py        # Document processing pipeline
│   │   ├── vectorstore.py      # ChromaDB wrapper
│   │   ├── prompts.py          # LLM prompt templates
│   │   └── agents/
│   │       ├── orchestrator.py # Multi-agent orchestrator
│   │       ├── retrieval_agent.py  # Hybrid RAG retrieval
│   │       ├── adaptation_agent.py # Recipe adaptation
│   │       └── nutrition_agent.py  # Nutrition & shopping lists
│   ├── requirements.txt
│   └── .env
├── frontend/                   # React UI
│   └── src/
│       ├── App.jsx             # Main application
│       └── components/
│           └── ChatMessage.jsx # Markdown message renderer
├── data/
│   └── sample_recipes.txt      # Sample recipe collection
├── langflow/
│   ├── chefrag_flow.json       # LangFlow visual flow
│   └── README.md               # LangFlow setup guide
└── README.md                   # This file
```

##  Features

- ** Document Ingestion**: Upload PDF or TXT recipe files — they're automatically chunked, embedded, and indexed
- ** Conversational Q&A**: Ask natural language questions about recipes and cooking
- ** Recipe Adaptation**: Modify recipes for dietary restrictions (vegan, keto, gluten-free, etc.)
- ** Nutritional Analysis**: Get estimated nutritional facts for any recipe
- ** Shopping Lists**: Generate organized shopping lists by store section
- ** User Preferences**: Set dietary restrictions, cuisine preferences, available ingredients
- ** Hybrid RAG**: Never gets stuck — blends document knowledge with LLM expertise

##  API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload and index a recipe document |
| POST | `/chat` | Chat with the multi-agent assistant |
| GET | `/documents` | List indexed documents |
| DELETE | `/documents/{name}` | Remove a document |
| GET | `/stats` | Vector store statistics |
| POST | `/clear-history` | Clear conversation history |
| GET | `/health` | Health check |

##  LangFlow Integration

ChefRAG includes a LangFlow-compatible flow file. See [`langflow/README.md`](langflow/README.md) for setup instructions.

Screenshots:

![alt text](<Screenshot 2026-09-14 124918.png>) ![alt text](<Screenshot 2026-09-14 115120.png>) ![alt text](<Screenshot 2026-09-14 115230.png>) ![alt text](<Screenshot 2026-09-14 115315.png>) ![alt text](<Screenshot 2026-09-14 115911.png>) ![alt text](<Screenshot 2026-09-14 120533.png>) ![alt text](<Screenshot 2026-09-14 120550.png>) ![alt text](<Screenshot 2026-09-14 120606.png>) ![alt text](<Screenshot 2026-09-14 120624.png>)
