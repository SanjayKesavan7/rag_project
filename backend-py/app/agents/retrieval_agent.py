"""
ChefRAG Retrieval Agent
Performs hybrid RAG retrieval: searches the vector store and uses a 3-tier
confidence strategy to blend document context with LLM general knowledge.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import GROQ_API_KEY, GROQ_MODEL, HIGH_CONFIDENCE, MEDIUM_CONFIDENCE
from app.vectorstore import search_recipes
from app.prompts import RETRIEVAL_PROMPT


def _get_llm():
    return ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.3)


def retrieve_and_answer(query: str, preferences: dict = None) -> str:
    """
    Search the recipe knowledge base and answer using the hybrid RAG strategy.

    3-Tier Confidence Strategy:
    - HIGH (score >= 0.50): Answer primarily from documents
    - MEDIUM (0.30 - 0.50): Blend document context with LLM knowledge
    - LOW (< 0.30 or no results): Use LLM general knowledge with disclaimer

    Args:
        query: The user's question about recipes/cooking.
        preferences: Optional dict of user preferences.

    Returns:
        A formatted answer string.
    """
    # ── Search the vector store ───────────────────────────────────────────
    results = search_recipes(query, k=5)

    if not results:
        confidence_level = "LOW"
        context = "No recipe documents have been indexed yet. No document context available."
    else:
        # Calculate average relevance score from top results
        scores = [score for _, score in results]
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)

        # Use the max score for confidence determination (best match matters most)
        if max_score >= HIGH_CONFIDENCE:
            confidence_level = "HIGH"
        elif max_score >= MEDIUM_CONFIDENCE:
            confidence_level = "MEDIUM"
        else:
            confidence_level = "LOW"

        # Format the retrieved context with source attribution
        context_parts = []
        for doc, score in results:
            source = doc.metadata.get("source", "Unknown")
            context_parts.append(
                f"[Source: {source} | Relevance: {score:.2f}]\n{doc.page_content}"
            )
        context = "\n\n---\n\n".join(context_parts)

    # ── Build and invoke the retrieval chain ──────────────────────────────
    try:
        prompt = ChatPromptTemplate.from_template(RETRIEVAL_PROMPT)
        llm = _get_llm()
        chain = prompt | llm | StrOutputParser()

        result = chain.invoke({
            "context": context,
            "confidence_level": confidence_level,
            "question": query,
        })

        return result
    except Exception as e:
        # If LLM fails (e.g., invalid API key), return raw retrieved context
        print(f"[ChefRAG Retrieval] LLM error, returning raw context: {e}")
        if results:
            fallback = f"## Retrieved Recipe Information\n\n"
            fallback += f"*(Note: LLM generation unavailable — showing raw retrieved context)*\n\n"
            for doc, score in results:
                source = doc.metadata.get("source", "Unknown")
                fallback += f"**Source:** {source} | **Relevance:** {score:.2f}\n\n"
                fallback += doc.page_content + "\n\n---\n\n"
            return fallback
        else:
            raise
