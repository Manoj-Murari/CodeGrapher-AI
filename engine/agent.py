# --- engine/agent.py ---

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from dotenv import load_dotenv

# Import our project's configuration and tools
import config
from tools.file_system import read_file, list_files
from tools.code_graph import query_code_graph

# --- Load Environment Variables ---
load_dotenv()

# --- Global variable to hold the agent executor ---
_agent_executor = None

def get_agent_executor():
    """
    Initializes and returns a LangChain agent executor.
    Caches the executor in a global variable.
    """
    global _agent_executor
    if _agent_executor is not None:
        return _agent_executor

    print("--- 🤖 Initializing agent for the first time... ---")

    # 1. Initialize the LLM
    llm = ChatGoogleGenerativeAI(
        model=config.AGENT_MODEL_NAME,
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        convert_system_message_to_human=True # Helps with compatibility
    )

    # 2. Define the list of tools the agent can use
    tools = [read_file, list_files, query_code_graph]

    # 3. Get the ReAct prompt template from LangChain Hub
    # This prompt is specifically designed to make the LLM reason about which tool to use.
    prompt = hub.pull("hwchase17/react")

    # 4. Create the ReAct agent
    agent = create_react_agent(llm, tools, prompt)

    # 5. Create the agent executor, which runs the agent's reasoning loop
    _agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True, # Set to True to see the agent's thought process
        handle_parsing_errors=True # Gracefully handle any LLM output parsing errors
    )
    print("--- ✅ Agent initialized successfully! ---")
    return _agent_executor

# --- For testing purposes ---
if __name__ == '__main__':
    agent_executor = get_agent_executor()
    result = agent_executor.invoke({
        "input": "List the files in the root of the repository."
    })
    print("\n--- Agent Test Result ---")
    print(result)