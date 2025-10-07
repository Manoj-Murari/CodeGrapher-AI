# --- tools/code_graph.py ---

import json
from engine.context import ProjectContext, ProjectScopedTool

class QueryCodeGraphTool(ProjectScopedTool):
    """A tool to query the project's structural code graph."""
    def __init__(self, context: ProjectContext):
        super().__init__(context)
        self.graph = self._load_graph()

    def _load_graph(self):
        try:
            with open(self.context.code_graph_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"nodes": [], "edges": []}

    def execute(self, entity_name: str, relationship: str, min_confidence: float = 0.8) -> str:
        """
        Queries the code's structure graph to find callers or callees of a function/method.
        - entity_name: The name of the function or method to query.
        - relationship: The relationship to find. Must be 'callers' or 'callees'.
        - min_confidence: The minimum confidence score (0.0 to 1.0) for a relationship to be included. Defaults to 0.8.
        """
        if not self.graph.get("nodes"):
            return f"Error: The code graph for project '{self.context.project_id}' is not available or is empty."

        if relationship not in ['callers', 'callees']:
            return "Error: Invalid relationship. Must be 'callers' or 'callees'."

        target_node = next((n for n in self.graph['nodes'] if n['name'] == entity_name), None)

        if not target_node:
            return f"Error: Entity '{entity_name}' not found in the code graph."

        target_id = target_node['id']
        results = []
        
        # --- NEW: Filter edges by the min_confidence score ---
        relevant_edges = [
            edge for edge in self.graph['edges'] 
            if edge.get('confidence', 1.0) >= min_confidence
        ]

        if relationship == 'callers':
            caller_ids = {edge['source'] for edge in relevant_edges if edge['target'] == target_id}
            results = [node for node in self.graph['nodes'] if node['id'] in caller_ids]
        elif relationship == 'callees':
            callee_ids = {edge['target'] for edge in relevant_edges if edge['source'] == target_id}
            results = [node for node in self.graph['nodes'] if node['id'] in callee_ids]

        if not results:
            return f"No {relationship} found for '{entity_name}' with confidence >= {min_confidence}."

        return json.dumps(results, indent=2)