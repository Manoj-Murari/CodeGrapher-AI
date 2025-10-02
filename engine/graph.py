# --- engine/graph.py ---

import operator
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.exceptions import OutputParserException

from engine.agent import get_agent_and_tools

class AgentState(TypedDict):
    input: str
    chat_history: Sequence[BaseMessage]
    agent_outcome: AgentAction | AgentFinish | None
    intermediate_steps: Annotated[Sequence[tuple[AgentAction, str]], operator.add]

agent_runnable, tools = get_agent_and_tools()
tool_map = {tool.name: tool for tool in tools}

def run_agent(data):
    try:
        agent_outcome = agent_runnable.invoke(data)
        return {"agent_outcome": agent_outcome}
    except OutputParserException as e:
        return {
            "agent_outcome": AgentFinish(
                return_values={"output": str(e)}, log=str(e)
            )
        }

def execute_tools(data):
    agent_action = data["agent_outcome"]
    
    tool_to_run = tool_map.get(agent_action.tool)
    if not tool_to_run:
        observation = f"Error: Tool '{agent_action.tool}' not found."
    else:
        observation = tool_to_run.invoke(agent_action.tool_input)

    return {"intermediate_steps": [(agent_action, str(observation))]}

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