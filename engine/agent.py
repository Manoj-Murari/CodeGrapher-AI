# --- engine/agent.py ---

import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
# REMOVE THIS - We will no longer create memory here
# from langchain.memory import ConversationBufferMemory 
from dotenv import load_dotenv

import config
from tools.file_system import (
    read_file, 
    list_files, 
    create_file_in_workspace, 
    update_file_in_workspace, 
    list_workspace_files
)
from tools.code_graph import query_code_graph

load_dotenv()

_agent_executor = None

# --- UPDATE THE FUNCTION TO ACCEPT A MEMORY OBJECT ---
def get_agent_executor(memory):
    """
    Initializes and returns a LangChain agent executor.
    Caches the executor in a global variable.
    """
    global _agent_executor
    if _agent_executor is not None:
        # A simple way to update memory on the cached executor
        _agent_executor.memory = memory 
        return _agent_executor

    logging.info("--- [AGENT] Initializing for the first time... ---")

    llm = ChatGoogleGenerativeAI(
        model=config.AGENT_MODEL_NAME,
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        convert_system_message_to_human=True
    )

    tools = [
        read_file, 
        list_files, 
        query_code_graph,
        create_file_in_workspace,
        update_file_in_workspace,
        list_workspace_files
    ]
    
    prompt = hub.pull("hwchase17/react-chat")
    agent = create_react_agent(llm, tools, prompt)

    _agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        # --- USE THE PASSED-IN MEMORY OBJECT ---
        memory=memory,
        verbose=config.AGENT_VERBOSE,
        handle_parsing_errors=True
    )
    
    logging.info("--- [AGENT] Initialized successfully! ---")
    return _agent_executor