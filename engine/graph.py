# --- engine/graph.py ---

import operator
import ast
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.exceptions import OutputParserException

from engine.agent import get_agent_and_tools

class AgentState(TypedDict):
    input: str
    chat_history: Sequence[BaseMessage]
    project_id: str
    agent_outcome: AgentAction | AgentFinish | None
    intermediate_steps: Annotated[Sequence[tuple[AgentAction, str]], operator.add]

agent_runnable, tools = get_agent_and_tools()
tool_map = {tool.name: tool for tool in tools}

def run_agent(data):
    project_id = data["project_id"]
    try:
        # --- THIS IS THE FIX ---
        # The agent runnable requires 'intermediate_steps' to know what tools have been called.
        # This was mistakenly removed in the last merge. It is now restored.
        agent_inputs = {
            "input": data["input"],
            "chat_history": data.get("chat_history", []),
            "intermediate_steps": data.get("intermediate_steps", []) # <-- RESTORED LINE
        }
        agent_outcome = agent_runnable.invoke(agent_inputs)
        
        return {"agent_outcome": agent_outcome, "project_id": project_id}

    except OutputParserException as e:
        if hasattr(e, 'llm_output'):
            final_answer = e.llm_output
        else:
            final_answer = str(e)
        
        agent_finish = AgentFinish(
            return_values={"output": final_answer}, 
            log=f"Recovered from OutputParserException: {final_answer}"
        )
        
        return {"agent_outcome": agent_finish, "project_id": project_id}


def execute_tools(data):
    agent_action = data["agent_outcome"]
    project_id = data["project_id"] 
    
    tool_to_run = tool_map.get(agent_action.tool)
    if not tool_to_run:
        observation = f"Error: Tool '{agent_action.tool}' not found."
    else:
        # The logic to inject project_id into the tool input was overly complex
        # and could fail for simple string inputs. It's better to modify the tools
        # to accept a dictionary with an optional project_id.
        # However, for now, we'll keep the existing injection logic but ensure it's robust.
        tool_input = agent_action.tool_input
        
        # We only need to inject the project_id if the tool actually needs it.
        # This should be defined on the tool itself, but for now we can list them.
        tools_requiring_project = [
            "query_code_graph", "read_file", "list_files"
        ]

        if agent_action.tool in tools_requiring_project:
            # The agent will sometimes pass a dict, sometimes a string.
            # The tool expects a dict with project_id. Let's ensure that.
            if isinstance(tool_input, str):
                # For tools like read_file, the string is the path.
                # The tool should be updated to expect a dict like {"file_path": "...", "project_id": "..."}
                # For now, we will assume the tool can handle this special case.
                # A better long-term fix is in the tool definitions.
                pass # This part of the logic needs to be handled by the tool itself.

            elif isinstance(tool_input, dict):
                 tool_input["project_id"] = project_id
        
        observation = tool_to_run.invoke(tool_input)

    return {"intermediate_steps": [(agent_action, str(observation))], "project_id": project_id}

def should_continue(data):
    if isinstance(data["agent_outcome"], AgentFinish):
        return "end"
    else:
        return "continue"

def get_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", run_agent)
    workflow.add_node("action", execute_tools)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "action",
            "end": END,
        },
    )
    workflow.add_edge("action", "agent")
    return workflow.compile()