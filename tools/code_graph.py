# --- tools/code_graph.py ---

import json
from langchain.tools import tool
from typing import Literal

# Import our project's configuration
import config

_code_graph_cache = None

def _get_code_graph():
    """Loads and caches the code graph from the JSON file."""
    global _code_graph_cache
    if _code_graph_cache is None:
        try:
            with open(config.CODE_GRAPH_PATH, 'r', encoding='utf-8') as f:
                _code_graph_cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"nodes": [], "edges": []}
    return _code_graph_cache

@tool
def query_code_graph(entity_name: str, relationship: Literal['callers', 'callees']) -> str:
    """
    Queries the code's structure graph to find callers or callees of a function/method.
    NOTE: This tool depends on a 'code_graph.json' file which is not yet generated.
    """
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
    else:
        return "Error: Invalid relationship. Must be 'callers' or 'callees'."

    return json.dumps(results, indent=2)