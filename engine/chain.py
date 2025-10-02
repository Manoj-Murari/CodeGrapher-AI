# --- engine/chain.py ---

import os
import sys
import logging
from typing import Literal

# --- Path Fix ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End Path Fix ---

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import config
from engine.rag import get_query_engine
from engine.agent import get_agent_executor

load_dotenv()

class RouteQuery(BaseModel):
    route: Literal["RAG", "AGENT"] = Field(...)

_routing_chain = None
def get_routing_chain():
    global _routing_chain
    if _routing_chain is not None:
        return _routing_chain
    llm = ChatGoogleGenerativeAI(model=config.CLASSIFICATION_MODEL_NAME, temperature=0)
    prompt_template = """
You are an expert at routing a user's query. Based on the query, you must decide whether to use a RAG system or a general-purpose Agent.
- Use 'RAG' for questions about the codebase's content, structure, or purpose.
- Use 'AGENT' for commands, requests to read/list files, or complex multi-step tasks.
User query: {query}
Respond with a JSON object containing a single key 'route' with a value of either 'RAG' or 'AGENT'.
"""
    prompt = PromptTemplate.from_template(prompt_template)
    output_parser = JsonOutputParser(pydantic_object=RouteQuery)
    _routing_chain = prompt | llm | output_parser
    return _routing_chain

def run_chain(query: str):
    logging.info(f"--- [CLASSIFY] Query: '{query}' ---")
    routing_chain = get_routing_chain()
    routing_decision = routing_chain.invoke({"query": query})
    
    route = routing_decision.get("route")
    logging.info(f"--- [ROUTE] Chosen: {route} ---")
    
    if route == "AGENT":
        logging.info("--- [AGENT] Invoking Stream... ---")
        agent_executor = get_agent_executor()
        for chunk in agent_executor.stream({"input": query}):
            if "actions" in chunk:
                thought = f"🤔 {chunk['messages'][0].content.strip()}"
                yield {"type": "thought", "content": thought}
            elif "output" in chunk:
                yield {"type": "chunk", "content": chunk["output"]}
        
    elif route == "RAG":
        logging.info("--- [RAG] Invoking Stream... ---")
        query_engine = get_query_engine()
        for chunk in query_engine.query(query):
            yield {"type": "chunk", "content": chunk}
            
    else:
        yield {"type": "error", "content": "Error: Could not determine how to handle the query."}
    
    yield {"type": "end", "content": ""}