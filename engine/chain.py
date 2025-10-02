# --- engine/chain.py ---

import os
import logging
from typing import Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage

from dotenv import load_dotenv

import config
from engine.rag import get_query_engine
from engine.agent import get_agent_executor

load_dotenv()

_memory = ConversationBufferMemory(return_messages=True, input_key="input")

class RouteQuery(BaseModel):
    route: Literal["RAG", "AGENT"] = Field(...)

# --- ADD THIS LINE TO INITIALIZE THE VARIABLE ---
_routing_chain = None

def get_routing_chain():
    global _routing_chain
    if _routing_chain is not None:
        return _routing_chain
        
    llm = ChatGoogleGenerativeAI(model=config.CLASSIFICATION_MODEL_NAME, temperature=0)
    
    prompt_template = """
You are an expert at routing a user's query. Based on the query AND the conversation history, you must decide whether to use a RAG system or a general-purpose Agent.

- Use 'RAG' for general questions about the codebase's content, structure, or purpose.
- Use 'AGENT' for commands, requests to read/list files, or for questions that refer to the content of the conversation history.

CONVERSATION HISTORY:
{chat_history}

USER QUERY:
{input}

Respond with a JSON object containing a single key 'route' with a value of either 'RAG' or 'AGENT'.
"""
    prompt = ChatPromptTemplate.from_template(prompt_template)
    output_parser = JsonOutputParser(pydantic_object=RouteQuery)
    _routing_chain = prompt | llm | output_parser
    return _routing_chain

def run_chain(query: str):
    
    logging.info(f"--- [CLASSIFY] Query: '{query}' ---")
    routing_chain = get_routing_chain()
    
    chat_history = _memory.load_memory_variables({}).get("history", [])
    routing_decision = routing_chain.invoke({
        "input": query,
        "chat_history": chat_history
    })
    
    route = routing_decision.get("route")
    logging.info(f"--- [ROUTE] Chosen: {route} ---")
    
    if route == "AGENT":
        logging.info("--- [AGENT] Invoking Stream... ---")
        agent_executor = get_agent_executor(memory=_memory)
        
        for chunk in agent_executor.stream({"input": query, "chat_history": chat_history}):
            if "actions" in chunk:
                thought = f"🤔 {chunk['messages'][0].content.strip()}"
                yield {"type": "thought", "content": thought}
            elif "output" in chunk:
                yield {"type": "chunk", "content": chunk["output"]}

    elif route == "RAG":
        logging.info("--- [RAG] Invoking Stream... ---")
        query_engine = get_query_engine()
        full_response = ""
        for chunk in query_engine.query(query):
            yield {"type": "chunk", "content": chunk}
            full_response += chunk
        _memory.save_context({"input": query}, {"output": full_response})

    else:
        yield {"type": "error", "content": "Error: Could not determine how to handle the query."}
    
    yield {"type": "end", "content": ""}