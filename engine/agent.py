# --- engine/agent.py ---

import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain import hub
from langchain.agents import create_react_agent

import config
from tools.file_system import (
    read_file, 
    list_files, 
    create_file_in_workspace, 
    update_file_in_workspace, 
    list_workspace_files
)
from tools.code_graph import query_code_graph

def get_agent_and_tools():
    """
    Initializes and returns the LangChain agent runnable and its tools.
    """
    logging.info("--- [AGENT] Initializing Agent and Tools... ---")

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
    agent_runnable = create_react_agent(llm, tools, prompt)
    
    logging.info("--- [AGENT] Agent and Tools initialized successfully! ---")
    return agent_runnable, tools