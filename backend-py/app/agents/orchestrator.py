"""
ChefRAG Orchestrator Agent
The main multi-agent orchestrator that routes user queries to the appropriate
sub-agent using LangGraph's react agent framework.

This is the brain of the ChefRAG system — it decides which tools to use
based on the user's intent and combines results into coherent responses.
"""

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from app.config import GROQ_API_KEY, GROQ_MODEL
from app.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from app.agents.retrieval_agent import retrieve_and_answer
from app.agents.adaptation_agent import adapt_recipe_chain
from app.agents.nutrition_agent import get_nutrition_chain, shopping_list_chain


# ── Conversation History Store ────────────────────────────────────────────────
_conversation_histories: dict[str, list] = {}


# ── Tool Definitions ─────────────────────────────────────────────────────────
# Each tool wraps a sub-agent's core functionality so the orchestrator
# can invoke them via LangGraph's react agent mechanism.

@tool
def search_recipes(query: str) -> str:
    """Search the recipe knowledge base for recipes, cooking methods, ingredients,
    and cooking techniques. Use this tool whenever the user asks about finding,
    making, or learning about any recipe or cooking topic. This tool will search
    indexed recipe documents and provide answers blended with culinary knowledge."""
    return retrieve_and_answer(query)


@tool
def adapt_recipe(recipe_and_requirements: str) -> str:
    """Adapt or modify a recipe based on dietary restrictions, available ingredients,
    cuisine preferences, or time constraints. Use this tool when the user wants to
    change a recipe — for example, making it vegan, gluten-free, sugar-free, or
    substituting specific ingredients."""
    return adapt_recipe_chain(recipe_and_requirements)


@tool
def get_nutrition_info(recipe_or_ingredients: str) -> str:
    """Get estimated nutritional information (calories, protein, carbs, fat, etc.)
    for a recipe or list of ingredients. Use this tool when the user asks about
    calories, nutrients, health aspects, or dietary content of a dish."""
    return get_nutrition_chain(recipe_or_ingredients)


@tool
def generate_shopping_list(recipe_and_servings: str) -> str:
    """Generate a categorized shopping list organized by store section for a recipe.
    Use this tool when the user wants to know what groceries to buy for a recipe.
    Include the recipe name and desired number of servings in the input."""
    return shopping_list_chain(recipe_and_servings)


_tools = [search_recipes, adapt_recipe, get_nutrition_info, generate_shopping_list]


# ── Agent Creation ────────────────────────────────────────────────────────────

_agent = None


def _get_agent():
    """Get or create the singleton LangGraph react agent."""
    global _agent
    if _agent is None:
        llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=GROQ_MODEL,
            temperature=0.3,
        )
        _agent = create_react_agent(llm, _tools)
    return _agent


# ── Public API ────────────────────────────────────────────────────────────────

def run_agent(query: str, session_id: str = "default", preferences: dict = None) -> str:
    """
    Run the orchestrator agent with a user query.

    The agent will:
    1. Analyze the user's intent
    2. Select and invoke the appropriate tool(s)
    3. Format and return a comprehensive answer

    Args:
        query: The user's question or request.
        session_id: Session identifier for conversation history.
        preferences: Optional dict with user preferences:
            - dietary_restrictions
            - cuisine_preference
            - available_ingredients
            - max_cooking_time

    Returns:
        The agent's formatted response string.
    """
    preferences = preferences or {}
    agent = _get_agent()

    # Get or initialize conversation history for this session
    history = _conversation_histories.get(session_id, [])

    # Format preferences into a readable string
    pref_parts = []
    if preferences.get("dietary_restrictions"):
        pref_parts.append(f"- Dietary Restrictions: {preferences['dietary_restrictions']}")
    if preferences.get("cuisine_preference"):
        pref_parts.append(f"- Cuisine Preference: {preferences['cuisine_preference']}")
    if preferences.get("available_ingredients"):
        pref_parts.append(f"- Available Ingredients: {preferences['available_ingredients']}")
    if preferences.get("max_cooking_time"):
        pref_parts.append(f"- Max Cooking Time: {preferences['max_cooking_time']}")

    pref_str = "\n".join(pref_parts) if pref_parts else "No specific preferences set."

    # Build the system prompt with preferences
    system_prompt = ORCHESTRATOR_SYSTEM_PROMPT.format(preferences=pref_str)

    # Build message list: system + history + current query
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(history)
    messages.append(HumanMessage(content=query))

    try:
        result = agent.invoke({"messages": messages})

        # Extract the final AI response from the result
        result_messages = result.get("messages", [])
        answer = ""
        for msg in reversed(result_messages):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                answer = msg.content
                break

        if not answer:
            answer = "I encountered an issue processing your request. Please try again."

    except Exception as e:
        # Fallback: if the agent framework fails, fall back to direct retrieval
        print(f"[ChefRAG] Agent error, falling back to direct retrieval: {e}")
        try:
            answer = retrieve_and_answer(query)
        except Exception:
            answer = (
                "I encountered a temporary issue, but I'm still here to help! "
                "Please try rephrasing your question or uploading more recipe "
                "documents for better results."
            )

    # Update conversation history (keep last 10 exchanges = 20 messages)
    history.append(HumanMessage(content=query))
    history.append(AIMessage(content=answer))
    if len(history) > 20:
        history = history[-20:]
    _conversation_histories[session_id] = history

    return answer


def clear_history(session_id: str = "default"):
    """Clear conversation history for a session."""
    _conversation_histories.pop(session_id, None)
