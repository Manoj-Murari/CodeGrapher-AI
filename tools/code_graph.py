# --- tools/code_graph.py ---

import json
from langchain.tools import tool
import config

# The cache and loader functions are now much simpler
_code_graph_caches = {}

def _get_code_graph(project_name: str):
    """Loads and caches the code graph for a specific project."""
    global _code_graph_caches
    if project_name in _code_graph_caches:
        return _code_graph_caches[project_name]
    
    try:
        graph_path = config.get_code_graph_path(project_name)
        with open(graph_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
            _code_graph_caches[project_name] = graph_data
            return graph_data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"nodes": [], "edges": []}

# The parse_tool_input helper function is no longer needed in this file.

@tool
def query_code_graph(entity_name: str, relationship: str, project_id: str) -> str:
    """
    Queries the code's structure graph to find callers or callees of a function/method for a specific project.
    """
    # The internal parsing block is removed, as arguments are now validated automatically.
    
    if relationship not in ['callers', 'callees']:
        return "Error: Invalid relationship. Must be 'callers' or 'callees'."

    graph = _get_code_graph(project_id)
    if not graph.get("nodes"):
        return f"Error: The code graph for project '{project_id}' is not available or is empty."

    target_node = next((n for n in graph['nodes'] if n['name'] == entity_name), None)

    if not target_node:
        return f"Error: Entity '{entity_name}' not found in the code graph for project '{project_id}'."

    target_id = target_node['id']
    results = []

    if relationship == 'callers':
        caller_ids = {edge['source'] for edge in graph['edges'] if edge['target'] == target_id}
        results = [node for node in graph['nodes'] if node['id'] in caller_ids]
    elif relationship == 'callees':
        callee_ids = {edge['target'] for edge in graph['edges'] if edge['source'] == target_id}
        results = [node for node in graph['nodes'] if node['id'] in callee_ids]

    if not results:
        return f"No {relationship} found for '{entity_name}' in project '{project_id}'."

    return json.dumps(results, indent=2)