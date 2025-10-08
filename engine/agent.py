# --- engine/agent.py ---

import os
import logging
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI

import config
from engine.context import ProjectContext
from tools.file_system import (
    ReadFileTool, 
    ListFilesTool,
    CreateFileInWorkspaceTool,
    UpdateFileInWorkspaceTool,
    ListWorkspaceFilesTool
)
from tools.code_graph import QueryCodeGraphTool
from tools.test_generator import GenerateTestsTool
from tools.test_runner import RunTestsTool
from tools.refactor import RefactorCodeTool
from tools.bug_fixer import FixBugTool

def create_agent_executor(context: ProjectContext) -> AgentExecutor:
    """
    Creates and returns a LangChain AgentExecutor scoped to a specific project.
    """
    logging.info(f"--- [AGENT] Creating agent for project: {context.project_id} ---")

    llm = ChatGoogleGenerativeAI(
        model=config.AGENT_MODEL_NAME,
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        convert_system_message_to_human=True
    )

    # Instantiate all tool classes
    all_tools = [
        ReadFileTool(context),
        ListFilesTool(context),
        QueryCodeGraphTool(context),
        CreateFileInWorkspaceTool(context),
        UpdateFileInWorkspaceTool(context),
        ListWorkspaceFilesTool(context),
        GenerateTestsTool(context),
        RunTestsTool(context),
        RefactorCodeTool(context),
        FixBugTool(context)
    ]

    # Convert to LangChain Tool objects
    langchain_tools = [
        Tool(
            name=tool.__class__.__name__.replace("Tool", ""),
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