# --- engine/agent.py ---

import os
import logging
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI

import config
from engine.context import ProjectContext
# --- NEW: Import all our tool classes ---
from tools.file_system import (
    ReadFileTool, 
    ListFilesTool,
    CreateFileInWorkspaceTool,
    UpdateFileInWorkspaceTool,
    ListWorkspaceFilesTool
)
from tools.code_graph import QueryCodeGraphTool

def create_agent_executor(context: ProjectContext) -> AgentExecutor:
    """
    Creates and returns a LangChain AgentExecutor scoped to a specific project.
    The agent's tools are instantiated with the given project context.
    """
    logging.info(f"--- [AGENT] Creating agent for project: {context.project_id} ---")

    llm = ChatGoogleGenerativeAI(
        model=config.AGENT_MODEL_NAME,
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        convert_system_message_to_human=True
    )

    # Instantiate all tool classes with the project context
    repo_tools = [
        ReadFileTool(context),
        ListFilesTool(context),
        QueryCodeGraphTool(context)
    ]
    workspace_tools = [
        CreateFileInWorkspaceTool(context),
        UpdateFileInWorkspaceTool(context),
        ListWorkspaceFilesTool(context)
    ]
    all_tools = repo_tools + workspace_tools

    # Convert class instances into LangChain Tool objects
    langchain_tools = [
        Tool(
            name=tool.__class__.__name__.replace("Tool", ""), # e.g., 'ReadFileTool' -> 'ReadFile'
            func=tool.execute,
            description=tool.execute.__doc__
        ) for tool in all_tools
    ]
    
    prompt = hub.pull("hwchase17/react-chat")
    agent_runnable = create_react_agent(llm, langchain_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent_runnable,
        tools=langchain_tools,
        verbose=config.AGENT_VERBOSE,
        handle_parsing_errors=True
    )

    logging.info(f"--- [AGENT] Agent for project '{context.project_id}' created successfully! ---")
    return agent_executor