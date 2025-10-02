# --- engine/chain.py ---

import os
import sys

# --- Path Fix ---
# Add the project root to the Python path to allow importing 'config'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End Path Fix ---

from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import our project's configuration and the RAG/Agent engines
import config
from engine.rag import get_query_engine
from engine.agent import get_agent_executor

load_dotenv()

# --- 1. Define the Router's Output Structure ---
class RouteQuery(BaseModel):
    """The model's decision on where to route the user's query."""
    route: Literal["RAG", "AGENT"] = Field(
        description=(
            "The destination for the query. Use 'RAG' for questions about the codebase's content, structure, or purpose. "
            "Use 'AGENT' for commands, requests to read/list files, or complex multi-step tasks."
        )
    )

# --- 2. Create the Classification Chain ---
_routing_chain = None
def get_routing_chain():
    """
    Creates and caches a chain that classifies a user's query to 'RAG' or 'AGENT'.
    """
    global _routing_chain
    if _routing_chain is not None:
        return _routing_chain

    llm = ChatGoogleGenerativeAI(
        model=config.CLASSIFICATION_MODEL_NAME,
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        temperature=0
    )
    
    prompt_template = """
You are an expert at routing a user's query to the correct tool.
Based on the query, you must decide whether to use a RAG (Retrieval-Augmented Generation) system or a general-purpose Agent.

- Use 'RAG' for questions that can be answered by looking at the code, such as:
  "What does the `create_app` function do?"
  "How is the user model defined?"
  "Explain the project structure."

- Use 'AGENT' for commands or tasks that require interacting with the file system or performing a series of actions, such as:
  "List the files in the `src/` directory."
  "Read the contents of `README.md`."
  "Find all functions that call the `create_user` method and summarize them."

User query:
{query}

Respond with a JSON object containing a single key 'route' with a value of either 'RAG' or 'AGENT'.
"""
    
    prompt = PromptTemplate.from_template(prompt_template)
    output_parser = JsonOutputParser(pydantic_object=RouteQuery)
    
    _routing_chain = prompt | llm | output_parser
    return _routing_chain

# --- 3. The Main Entrypoint ---
def run_chain(query: str):
    """
    The main function to run the CodeGrapher AI.
    It classifies the query and routes it to the appropriate engine.
    """
    print(f"\n--- 🧠 Classifying query: '{query}' ---")
    routing_chain = get_routing_chain()
    routing_decision = routing_chain.invoke({"query": query})
    
    route = routing_decision.get("route")
    print(f"--- 🧭 Route chosen: {route} ---")
    
    if route == "AGENT":
        print("--- 🤖 Invoking Agent... ---")
        agent_executor = get_agent_executor()
        result = agent_executor.invoke({"input": query})
        return {"answer": result.get("output"), "source": "Agent"}
        
    elif route == "RAG":
        print("--- 📚 Invoking RAG Engine... ---")
        query_engine = get_query_engine()
        response = query_engine.query(query)
        return {"answer": response, "source": "RAG"}
        
    else:
        return {"answer": "Error: Could not determine how to handle the query.", "source": "Router"}

# --- For testing purposes ---
if __name__ == '__main__':
    # Test 1: A RAG question
    print("--- Running Test 1: RAG Query ---")
    rag_result = run_chain("What is the purpose of the 'create_app' function?")
    print("\n--- RAG Test Result ---")
    print(rag_result['answer'])

    # Test 2: An Agent question
    print("\n\n--- Running Test 2: Agent Query ---")
    agent_result = run_chain("List the files in the root directory of the repository.")
    print("\n--- Agent Test Result ---")
    print(agent_result['answer'])