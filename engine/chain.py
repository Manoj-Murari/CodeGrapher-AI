# --- engine/chain.py ---

import logging
from typing import Literal
from threading import Lock

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

# --- Session-Scoped Memory Manager (from previous fix) ---
class ConversationMemoryManager:
    """Thread-safe, session-scoped memory manager with size limits."""
    
    def __init__(self, max_messages_per_session: int = 30):
        self._memories: dict[str, ConversationBufferMemory] = {}
        self._lock = Lock()
        self._max_messages = max_messages_per_session
    
    def get_memory(self, session_id: str) -> ConversationBufferMemory:
        """Get or create memory for a specific session."""
        with self._lock:
            if session_id not in self._memories:
                self._memories[session_id] = ConversationBufferMemory(
                    return_messages=True,
                    input_key="input"
                )
            return self._memories[session_id]
    
    def save_context(self, session_id: str, inputs: dict, outputs: dict):
        """Save to session memory with automatic truncation."""
        memory = self.get_memory(session_id)
        memory.save_context(inputs, outputs)
        
        messages = memory.load_memory_variables({}).get("history", [])
        if len(messages) > self._max_messages:
            memory.chat_memory.messages = messages[-self._max_messages:]
            
    def clear_session(self, session_id: str):
        """Clear memory for a specific session."""
        with self._lock:
            if session_id in self._memories:
                del self._memories[session_id]

_memory_manager = ConversationMemoryManager(max_messages_per_session=30)

class RouteQuery(BaseModel):
    route: Literal["RAG", "AGENT"] = Field(...)

_routing_chain = None
def get_routing_chain():
    # ... (this function is unchanged) ...
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


def run_chain(query: str, project_id: str, session_id: str):
    """The main entry point for processing a user query for a specific project."""
    
    try:
        context = ProjectContext(project_id=project_id)
        logging.info(f"Context validated for project '{context.project_id}'")
    except ProjectNotIndexedError as e:
        logging.error(f"Context validation failed: {e}")
        yield {"type": "error", "content": e.user_friendly_message}
        return

    logging.info(f"--- [CLASSIFY] Query: '{query}' for Project: '{project_id}' Session: '{session_id}' ---")
    
    memory = _memory_manager.get_memory(session_id)
    chat_history = memory.load_memory_variables({}).get("history", [])

    routing_chain = get_routing_chain()
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
        
        # --- ENHANCED STREAMING WITH STRUCTURED EVENTS ---
        full_response = ""
        # The agent stream yields different types of chunks. We process them all.
        for chunk in agent_executor.stream(inputs):
            # 'actions' contain the agent's thoughts and tool choices
            if "actions" in chunk:
                for action in chunk["actions"]:
                    if hasattr(action, 'log') and "Thought:" in action.log:
                        thought_content = action.log.split('Thought:')[-1].strip()
                        yield {
                            "type": "agent_thought", 
                            "content": thought_content,
                            "icon": "🤔",
                            "label": "Thinking"
                        }

            # 'steps' contain the results of tool execution
            elif "steps" in chunk:
                for step in chunk["steps"]:
                    action, observation = step
                    # Truncate observation to keep the thought log clean
                    obs_preview = str(observation).strip()
                    if len(obs_preview) > 200:
                         obs_preview = obs_preview[:200] + "..."
                    # Handle different action object structures
                    tool_name = "Unknown"
                    if hasattr(action, 'tool'):
                        tool_name = action.tool
                    elif hasattr(action, 'action'):
                        tool_name = action.action
                    elif isinstance(action, tuple) and len(action) > 0:
                        tool_name = str(action[0])
                    else:
                        tool_name = str(action)
                    
                    # Send tool start event
                    yield {
                        "type": "tool_start",
                        "content": f"Using {tool_name}",
                        "icon": "🛠️",
                        "label": "Tool",
                        "tool_name": tool_name
                    }
                    
                    # Send tool result event
                    yield {
                        "type": "tool_result",
                        "content": obs_preview,
                        "icon": "✅",
                        "label": "Result",
                        "tool_name": tool_name
                    }
            
            # 'output' contains the final answer, which might arrive in multiple chunks
            elif "output" in chunk:
                output_text = chunk.get("output", "")
                full_response += output_text
                yield {"type": "chunk", "content": output_text}
                # CRITICAL FIX: DO NOT BREAK HERE. Let the stream finish naturally.

        # After the stream is complete, save the full context.
        if full_response:
            _memory_manager.save_context(session_id, inputs, {"output": full_response})
        else:
            yield {"type": "error", "content": "Agent did not produce a final answer."}
        # --- END OF REPLACEMENT ---

    elif route == "RAG":
        # ... (RAG logic remains the same) ...
        logging.info("--- [RAG] Invoking Stream... ---")
        query_engine = get_query_engine(context)
        response = query_engine.query(query)
        full_response = ""
        for chunk in response.response_gen:
            yield {"type": "chunk", "content": chunk}
            full_response += chunk
        _memory_manager.save_context(session_id, {"input": query}, {"output": full_response})

    else:
        yield {"type": "error", "content": "Error: Could not determine how to handle the query."}