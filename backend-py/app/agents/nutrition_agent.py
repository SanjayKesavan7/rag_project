"""
ChefRAG Nutrition & Shopping Agent
Provides nutritional estimates and generates categorized shopping lists.
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import GROQ_API_KEY, GROQ_MODEL
from app.vectorstore import search_recipes
from app.prompts import NUTRITION_PROMPT, SHOPPING_LIST_PROMPT


def _get_llm():
    return ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.2)


def _get_recipe_context(query: str) -> str:
    """Search the knowledge base and format the context."""
    results = search_recipes(query, k=3)

    if results:
        return "\n\n---\n\n".join([
            f"[Source: {doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}"
            for doc, _ in results
        ])
    else:
        return (
            f"No matching recipe found in the knowledge base. "
            f"User's request: {query}\n"
            f"Please provide nutritional estimates based on your expertise."
        )


def get_nutrition_chain(input_text: str) -> str:
    """
    Get nutritional information for a recipe or list of ingredients.

    Searches the knowledge base first, then uses the LLM to estimate
    nutritional facts.

    Args:
        input_text: Recipe name, description, or ingredient list.

    Returns:
        Formatted nutritional information string.
    """
    recipe_context = _get_recipe_context(input_text)

    prompt = ChatPromptTemplate.from_template(NUTRITION_PROMPT)
    llm = _get_llm()
    chain = prompt | llm | StrOutputParser()

    return chain.invoke({"recipe_context": recipe_context})


def shopping_list_chain(input_text: str, servings: int = 4) -> str:
    """
    Generate a categorized shopping list for a recipe.

    Searches the knowledge base first, then uses the LLM to create
    an organized shopping list scaled to the requested servings.

    Args:
        input_text: Recipe name, description, or ingredient list.
        servings: Number of servings to scale the list for.

    Returns:
        Formatted shopping list string.
    """
    recipe_context = _get_recipe_context(input_text)

    prompt = ChatPromptTemplate.from_template(SHOPPING_LIST_PROMPT)
    llm = _get_llm()
    chain = prompt | llm | StrOutputParser()

    return chain.invoke({
        "recipe_context": recipe_context,
        "servings": str(servings),
    })
