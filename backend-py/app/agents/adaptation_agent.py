"""
ChefRAG Adaptation Agent
Modifies recipes based on dietary restrictions, available ingredients,
cuisine preferences, and cooking time constraints.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import GROQ_API_KEY, GROQ_MODEL
from app.vectorstore import search_recipes
from app.prompts import ADAPTATION_PROMPT


def _get_llm():
    return ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.5)


def adapt_recipe_chain(input_text: str, preferences: dict = None) -> str:
    """
    Adapt a recipe based on user requirements.

    First searches the knowledge base for the recipe, then applies
    the requested adaptations using the LLM.

    Args:
        input_text: Description of the recipe to adapt and requirements.
        preferences: Optional dict with dietary_restrictions, available_ingredients,
                     cuisine_preference, max_cooking_time, additional_notes.

    Returns:
        Formatted adapted recipe string.
    """
    preferences = preferences or {}

    # ── Try to find the recipe in the knowledge base ──────────────────────
    results = search_recipes(input_text, k=3)

    if results:
        recipe_context = "\n\n---\n\n".join([
            f"[Source: {doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}"
            for doc, _ in results
        ])
    else:
        recipe_context = (
            f"No matching recipe found in the knowledge base. "
            f"User's request: {input_text}\n"
            f"Please create an adapted recipe based on your culinary expertise."
        )

    # ── Build and invoke the adaptation chain ─────────────────────────────
    prompt = ChatPromptTemplate.from_template(ADAPTATION_PROMPT)
    llm = _get_llm()
    chain = prompt | llm | StrOutputParser()

    result = chain.invoke({
        "recipe_context": recipe_context,
        "dietary_restrictions": preferences.get("dietary_restrictions", "None specified"),
        "available_ingredients": preferences.get("available_ingredients", "Not specified"),
        "cuisine_preference": preferences.get("cuisine_preference", "Any"),
        "max_cooking_time": preferences.get("max_cooking_time", "No limit"),
        "additional_notes": preferences.get("additional_notes", input_text),
    })

    return result
