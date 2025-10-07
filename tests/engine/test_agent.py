# --- tests/engine/test_agent.py ---

import pytest
import json
from pathlib import Path
import os
from unittest.mock import MagicMock

# Make sure the project root is in the path for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import AIMessage

from engine.context import ProjectContext
from engine.agent import create_agent_executor

# Re-using the fixture from file system tests by importing it
# We need to make sure pytest can find it. Create a tests/conftest.py file
# and move the setup_project fixture there. For now, we'll redefine it.

@pytest.fixture
def setup_project_for_agent(tmp_path: Path):
    """Sets up a temporary project directory for agent integration tests."""
    project_root = tmp_path / "agent_test_project"
    data_root = tmp_path / "data"
    
    (data_root / "vector_stores" / "agent_test_project").mkdir(parents=True)
    (data_root / "code_graphs").mkdir(parents=True)
    (data_root / "code_graphs" / "agent_test_project_graph.json").write_text('{"nodes": [], "edges": []}')
    
    repo_path = project_root
    repo_path.mkdir()
    (repo_path / "README.md").write_text("# Test Project")

    mp = pytest.MonkeyPatch()
    mp.setattr("config.VECTOR_STORE_BASE_PATH", data_root / "vector_stores")
    mp.setattr("config.CODE_GRAPH_BASE_PATH", data_root / "code_graphs")
    mp.setattr("config.TARGET_REPO_PATH", project_root.parent)
    yield ProjectContext(project_id="agent_test_project")
    mp.undo()


def test_agent_executor_can_call_read_file_tool(setup_project_for_agent):
    """
    Integration test to ensure the AgentExecutor can correctly parse an LLM response
    and invoke the read_file tool.
    """
    context = setup_project_for_agent
    
    # 1. Create a Mock LLM
    mock_llm = MagicMock()

    # 2. Define the mock's return value to simulate the LLM deciding to use a tool
    # This mimics the ReAct prompt's JSON format for tool calls
    tool_call_json = json.dumps({
        "action": "read_file",
        "action_input": {"file_path": "README.md"}
    }, indent=4)
    
    # The AgentExecutor expects an AIMessage containing the tool call info
    # We simulate both the thought process and the final tool call JSON
    mock_llm.invoke.return_value = AIMessage(
        content=f"Thought: The user wants to read a file. I should use the read_file tool.\n```json\n{tool_call_json}\n```"
    )

    # 3. Create the agent executor, but override the real LLM with our mock
    agent_executor = create_agent_executor(context)
    agent_executor.agent.llm = mock_llm # Inject the mock

    # 4. Run the executor
    inputs = {"input": "Read the README.md file", "chat_history": []}
    result = agent_executor.invoke(inputs)

    # 5. Assert the results
    # Check that the mock LLM was called correctly
    mock_llm.invoke.assert_called_once()
    
    # Check that the agent correctly identified and executed the tool
    # and returned the content of the file we created in our fixture
    assert "output" in result
    assert result["output"] == "# Test Project"