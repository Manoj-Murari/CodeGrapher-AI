# --- scripts/build_graph.py ---

import ast
import json
from pathlib import Path
import logging

import config

class DefinitionVisitor(ast.NodeVisitor):
    """
    Pass 1: Visits AST nodes to find all class, function, and method definitions
    and populates a symbol table.
    """
    def __init__(self, relative_path, nodes, symbol_table):
        self.relative_path = relative_path
        self.nodes = nodes
        self.symbol_table = symbol_table
        self.class_stack = []

    def visit_ClassDef(self, node):
        class_id = f"{self.relative_path}::{node.name}"
        self.nodes.append({"id": class_id, "type": "class", "name": node.name, "file": self.relative_path})
        self.symbol_table[class_id] = self.nodes[-1]
        
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node):
        if self.class_stack:
            parent_class = "::".join(self.class_stack)
            func_id = f"{self.relative_path}::{parent_class}::{node.name}"
            node_type = "method"
        else:
            func_id = f"{self.relative_path}::{node.name}"
            node_type = "function"
        
        self.nodes.append({"id": func_id, "type": node_type, "name": node.name, "file": self.relative_path})
        self.symbol_table[func_id] = self.nodes[-1]
        self.generic_visit(node)

class ContextAwareCallVisitor(ast.NodeVisitor):
    """
    Pass 2: Visits AST nodes to find all function/method calls, using
    import context to resolve them intelligently.
    """
    def __init__(self, relative_path, edges, symbol_table):
        self.relative_path = relative_path
        self.edges = edges
        self.symbol_table = symbol_table
        self.scope_stack = []
        self.imports = {}
        self.from_imports = {}

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports[alias.asname or alias.name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ''
        # Handle relative imports (e.g., 'from . import utils')
        if node.level > 0:
            path_parts = self.relative_path.split('/')
            prefix = '.'.join(path_parts[:-(node.level)])
            if module:
                module = f"{prefix}.{module}"
            else:
                module = prefix

        for alias in node.names:
            full_path = f"{module}.{alias.name}".replace('/', '.')
            self.from_imports[alias.asname or alias.name] = full_path
        self.generic_visit(node)

    def _get_current_scope_id(self):
        return '::'.join([self.relative_path] + self.scope_stack) if self.scope_stack else self.relative_path

    def visit_ClassDef(self, node):
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_FunctionDef(self, node):
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Call(self, node: ast.Call):
        caller_id = self._get_current_scope_id()
        callee_id = None
        confidence = 0.0

        # Case 1: Direct call, e.g., my_function()
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.from_imports:
                callee_id = self.from_imports[func_name]
                confidence = 1.0 # High confidence: direct import
            else:
                local_target_id = f"{self.relative_path}::{func_name}"
                if local_target_id in self.symbol_table:
                    callee_id = local_target_id
                    confidence = 0.9 # High confidence: local file scope

        # Case 2: Attribute call, e.g., obj.method()
        elif isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            if isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id
                if obj_name == 'self' and self.scope_stack:
                    class_scope = self.scope_stack[0]
                    callee_id = f"{self.relative_path}::{class_scope}::{method_name}"
                    confidence = 1.0
                elif obj_name in self.imports:
                    module_name = self.imports[obj_name]
                    callee_id = f"{module_name}.{method_name}"
                    confidence = 0.8
                elif obj_name in self.from_imports:
                    module_name = self.from_imports[obj_name]
                    callee_id = f"{module_name}::{method_name}"
                    confidence = 0.9
        
        # Heuristic Fallback for unresolved attribute calls
        if not callee_id and isinstance(node.func, ast.Attribute):
             method_name = node.func.attr
             for key in self.symbol_table:
                 if key.endswith(f"::{method_name}"):
                     callee_id = key
                     confidence = 0.4 # Low confidence: heuristic guess
                     break

        if callee_id:
            self.edges.append({
                "source": caller_id,
                "target": callee_id,
                "type": "CALLS",
                "confidence": confidence
            })
        
        self.generic_visit(node)

def build_code_graph(project_name: str, project_path: Path):
    """
    Analyzes a Python codebase in a given path and builds a JSON file
    representing its call graph, including nodes (functions, methods)
    and edges (calls between them).
    """
    logging.info(f"--- 🚀 Starting Intelligent Code Graph Construction for project: {project_name} ---")
    all_nodes, all_edges, symbol_table = [], [], {}
    
    python_files = list(project_path.rglob("*.py"))
    logging.info(f"Found {len(python_files)} Python files to process.")

    # Pass 1: Discover all definitions
    logging.info("--- Pass 1: Discovering definitions... ---")
    for file_path in python_files:
        relative_path = file_path.relative_to(project_path).as_posix()
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            DefinitionVisitor(relative_path, all_nodes, symbol_table).visit(tree)
        except Exception as e:
            logging.error(f"  - ❌ Error parsing {relative_path} for definitions: {e}")

    logging.info(f"--- ✅ Found {len(all_nodes)} total definitions. ---")

    # Pass 2: Discover all calls
    logging.info("--- Pass 2: Resolving calls with context... ---")
    for file_path in python_files:
        relative_path = file_path.relative_to(project_path).as_posix()
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            ContextAwareCallVisitor(relative_path, all_edges, symbol_table).visit(tree)
        except Exception as e:
            logging.error(f"  - ❌ Error parsing {relative_path} for calls: {e}")

    # Deduplicate edges based on all key-value pairs
    unique_edges = [dict(t) for t in {tuple(sorted(d.items())) for d in all_edges}]
    logging.info(f"--- ✅ Resolved {len(unique_edges)} total calls. ---")

    # Save Graph
    full_graph = {"nodes": all_nodes, "edges": unique_edges}
    save_path = config.get_code_graph_path(project_name)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(full_graph, f, indent=2)
    
    logging.info(f"--- 🎉 Intelligent code graph for {project_name} saved to {save_path} ---")