# --- engine/chain.py ---

import logging
from typing import Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv

import config
from engine.context import ProjectContext, ProjectNotIndexedError
from engine.rag import get_query_engine
from engine.agent import create_agent_executor

load_dotenv()

_memory = ConversationBufferMemory(return_messages=True, input_key="input")

class RouteQuery(BaseModel):
    route: Literal["RAG", "AGENT"] = Field(...)

_routing_chain = None
def get_routing_chain():
    global _routing_chain
    if _routing_chain is not None:
        return _routing_chain
    
    llm = ChatGoogleGenerativeAI(model=config.CLASSIFICATION_MODEL_NAME, temperature=0)
    prompt_template = """
You are an expert at routing a user's query. Based on the query AND the conversation history, you must decide whether to use a RAG system or a general-purpose Agent.

- Use 'RAG' for general questions about the codebase's content, structure, or purpose.
- Use 'AGENT' for commands, requests to read/list files, for questions that refer to the content of the conversation history, OR for specific questions about code structure like finding "callers" or "callees" of a function.

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


def run_chain(query: str, project_id: str):
    """The main entry point for processing a user query for a specific project."""
    
    try:
        context = ProjectContext(project_id=project_id)
        logging.info(f"Context validated for project '{context.project_id}'")
    except ProjectNotIndexedError as e:
        logging.error(f"Context validation failed: {e}")
        yield {"type": "error", "content": str(e)}
        return

    logging.info(f"--- [CLASSIFY] Query: '{query}' for Project: '{project_id}' ---")
    routing_chain = get_routing_chain()
    chat_history = _memory.load_memory_variables({}).get("history", [])
    routing_decision = routing_chain.invoke({
        "input": query,
        "chat_history": chat_history
    })
    route = routing_decision.get("route")
    logging.info(f"--- [ROUTE] Chosen: {route} ---")

    if route == "AGENT":
        logging.info("--- [AGENT] Invoking Agent Executor... ---")
        agent_executor = create_agent_executor(context)
        inputs = {"input": query, "chat_history": chat_history}
        
        # --- ROBUST STREAMING FIX ---
        full_response = ""
        # The agent stream yields different types of chunks (actions, observations, and finally output)
        for chunk in agent_executor.stream(inputs):
            # Intermediate steps (actions) contain the agent's thoughts in their logs
            if "actions" in chunk:
                log_str = chunk.get("logs", "")
                if "Thought:" in log_str:
                    thought = f"🤔 {log_str.split('Thought:')[-1].strip()}"
                    yield {"type": "thought", "content": thought}
            # The final answer is in a chunk with an 'output' key
            elif "output" in chunk:
                full_response = chunk.get("output", "")
                # Once we get the final answer, we yield it and can stop processing the stream
                yield {"type": "chunk", "content": full_response}
                break

        if full_response:
            _memory.save_context(inputs, {"output": full_response})
        else:
            yield {"type": "error", "content": "Agent did not produce a final answer."}
        # --- END OF FIX ---

    elif route == "RAG":
        logging.info("--- [RAG] Invoking Stream... ---")
        query_engine = get_query_engine(context)
        
        response = query_engine.query(query)
        
        full_response = ""
        for chunk in response.response_gen:
            yield {"type": "chunk", "content": chunk}
            full_response += chunk
        _memory.save_context({"input": query}, {"output": full_response})

    else:
        yield {"type": "error", "content": "Error: Could not determine how to handle the query."}