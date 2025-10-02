# --- engine/agent.py ---

import os
import sys
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from dotenv import load_dotenv

# --- Path Fix ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End Path Fix ---

import config
from tools.file_system import read_file, list_files
from tools.code_graph import query_code_graph

load_dotenv()

_agent_executor = None

def get_agent_executor():
    """
    Initializes and returns a LangChain agent executor.
    Caches the executor in a global variable.
    """
    global _agent_executor
    if _agent_executor is not None:
        return _agent_executor

    logging.info("--- [AGENT] Initializing for the first time... ---")

    llm = ChatGoogleGenerativeAI(
        model=config.AGENT_MODEL_NAME,
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        convert_system_message_to_human=True
    )

    tools = [read_file, list_files, query_code_graph]
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt)

    _agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    
    logging.info("--- [AGENT] Initialized successfully! ---")
    return _agent_executor