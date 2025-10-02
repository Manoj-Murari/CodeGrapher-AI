# --- tools/code_graph.py ---

import json
import ast
from langchain.tools import tool
from typing import Union, Dict

import config

_code_graph_cache = None

def _get_code_graph():
    global _code_graph_cache
    if _code_graph_cache is None:
        try:
            with open(config.CODE_GRAPH_PATH, 'r', encoding='utf-8') as f:
                _code_graph_cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"nodes": [], "edges": []}
    return _code_graph_cache

def parse_tool_input(input_str: Union[str, Dict]) -> Dict:
    if isinstance(input_str, dict):
        return input_str
    try:
        evaluated = ast.literal_eval(input_str)
        if isinstance(evaluated, dict):
            return evaluated
        return {}
    except (ValueError, SyntaxError):
        return {}


@tool
def query_code_graph(tool_input: Union[str, Dict]) -> str:
    """
    Queries the code's structure graph to find callers or callees of a function/method.
    The input must be a dictionary containing 'entity_name' and 'relationship' (either 'callers' or 'callees').
    Example: {"entity_name": "my_function", "relationship": "callers"}
    """
    try:
        parsed_args = parse_tool_input(tool_input)
        entity_name = parsed_args["entity_name"]
        relationship = parsed_args["relationship"]
        if relationship not in ['callers', 'callees']:
            return "Error: Invalid relationship. Must be 'callers' or 'callees'."
    except (KeyError, TypeError):
        return "Error: Input must be a dictionary with 'entity_name' and 'relationship' keys."

    graph = _get_code_graph()
    if not graph["nodes"]:
        return "Error: The code_graph.json file is not available or is empty."

    target_node = next((n for n in graph['nodes'] if n['name'] == entity_name), None)

    if not target_node:
        return f"Error: Entity '{entity_name}' not found in the code graph."

    target_id = target_node['id']
    results = []

    if relationship == 'callers':
        caller_ids = {edge['source'] for edge in graph['edges'] if edge['target'] == target_id}
        results = [node for node in graph['nodes'] if node['id'] in caller_ids]
    elif relationship == 'callees':
        callee_ids = {edge['target'] for edge in graph['edges'] if edge['source'] == target_id}
        results = [node for node in graph['nodes'] if node['id'] in callee_ids]

    return json.dumps(results, indent=2)